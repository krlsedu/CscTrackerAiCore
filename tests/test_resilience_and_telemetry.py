import logging
import os
import sys
import threading
import time
import types
import unittest
from unittest.mock import MagicMock, patch

# Permite rodar os testes offline mesmo sem google-genai ou clickhouse-connect instalados
if "google" not in sys.modules:
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_types_mod = types.ModuleType("google.genai.types")
    genai_interactions_mod = types.ModuleType("google.genai._interactions")
    genai_interactions_types_mod = types.ModuleType("google.genai._interactions.types")
    genai_interactions_types_mod.thinking_level = None

    class _DummyConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _DummyPart:
        @staticmethod
        def from_bytes(data, mime_type):
            return {"data": data, "mime_type": mime_type}

    genai_types_mod.GenerateContentConfig = _DummyConfig
    genai_types_mod.ThinkingConfig = _DummyConfig
    genai_types_mod.HttpOptions = _DummyConfig
    genai_types_mod.Part = _DummyPart
    genai_mod.types = genai_types_mod
    genai_mod.Client = MagicMock()
    google_mod.genai = genai_mod

    sys.modules["google"] = google_mod
    sys.modules["google.genai"] = genai_mod
    sys.modules["google.genai.types"] = genai_types_mod
    sys.modules["google.genai._interactions"] = genai_interactions_mod
    sys.modules["google.genai._interactions.types"] = genai_interactions_types_mod

if "clickhouse_connect" not in sys.modules:
    ch_mod = types.ModuleType("clickhouse_connect")
    ch_mod.get_client = MagicMock()
    sys.modules["clickhouse_connect"] = ch_mod

from csctracker_ai_core.service.ClickHouseDb import ClickHouseDb
from csctracker_ai_core.service.IaProcessor import GeminiServiceException, IaProcessor
from csctracker_ai_core.service.Telemetry import Telemetry


def _make_fake_response(
    text='{"ok": true}', prompt_tokens=10, output_tokens=5, thoughts_tokens=0
):
    resp = MagicMock()
    resp.text = text
    resp.usage_metadata = MagicMock()
    resp.usage_metadata.prompt_token_count = prompt_tokens
    resp.usage_metadata.candidates_token_count = output_tokens
    resp.usage_metadata.thoughts_token_count = thoughts_tokens
    resp.usage_metadata.prompt_tokens_details = []
    return resp


def _extract_timeout_ms(http_options):
    if hasattr(http_options, "timeout"):
        return http_options.timeout
    if hasattr(http_options, "kwargs"):
        return http_options.kwargs.get("timeout")
    return None


class TestId80ClientPoolTimeoutBackoff(unittest.TestCase):
    def _build_processor(
        self,
        limits="gemini-4-hydrogen:flash=5",
        paid_keys="paid_key_1",
        free_keys=None,
        env_overrides=None,
    ):
        env = env_overrides or {}
        with patch.dict(os.environ, env, clear=False), patch(
            "csctracker_ai_core.service.IaProcessor.ClickHouseDb"
        ) as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits=limits,
                google_free_keys=free_keys,
                google_paid_keys=paid_keys,
            )
            proc.click_house = ch_instance
            return proc

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_client_pool_reuses_by_key_and_timeout_and_closes_on_processor_close(
        self, mock_client_cls
    ):
        created_clients = []

        def make_client(**kwargs):
            client = MagicMock()
            client.init_kwargs = kwargs
            client.models.generate_content.return_value = _make_fake_response()
            created_clients.append(client)
            return client

        mock_client_cls.side_effect = make_client
        proc = self._build_processor(paid_keys="paid_key_1")

        # 2 chamadas com mesma key e mesmo timeout (standard=300s) -> 1 único client reutilizado
        proc.analisar_com_gemini(input_text="a", prompt="p", service_tier="standard")
        proc.analisar_com_gemini(input_text="b", prompt="p", service_tier="standard")
        self.assertEqual(len(created_clients), 1)
        self.assertEqual(
            _extract_timeout_ms(created_clients[0].init_kwargs["http_options"]),
            300_000,
        )

        # Chamada em modo flex (600s) -> novo client para (paid_key_1, 600_000)
        proc.analisar_com_gemini(input_text="c", prompt="p", service_tier="flex")
        self.assertEqual(len(created_clients), 2)
        self.assertEqual(
            _extract_timeout_ms(created_clients[1].init_kwargs["http_options"]),
            600_000,
        )

        # close() fecha todos os clients do pool e também fecha o click_house
        proc.close()
        created_clients[0].close.assert_called_once()
        created_clients[1].close.assert_called_once()
        proc.click_house.close.assert_called_once()
        self.assertEqual(len(proc._clients), 0)

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_evicts_and_closes_client_when_invalid_key_removed(self, mock_client_cls):
        clients_by_key = {}

        def make_client(**kwargs):
            key = kwargs["api_key"]
            client = MagicMock()
            if key == "bad_key":
                client.models.generate_content.side_effect = RuntimeError(
                    "400 API_KEY_INVALID"
                )
            else:
                client.models.generate_content.return_value = _make_fake_response(
                    '{"ok": "good"}'
                )
            clients_by_key[key] = client
            return client

        mock_client_cls.side_effect = make_client
        proc = self._build_processor(free_keys="bad_key", paid_keys="good_key")

        result, _, _ = proc.analisar_com_gemini(input_text="x", prompt="p")
        self.assertEqual(result, {"ok": "good"})

        # bad_key foi removida do pool e teve close() chamado; good_key permanece no pool
        clients_by_key["bad_key"].close.assert_called_once()
        clients_by_key["good_key"].close.assert_not_called()
        self.assertTrue(all(k[0] != "bad_key" for k in proc._clients))
        self.assertTrue(any(k[0] == "good_key" for k in proc._clients))
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_timeout_env_and_per_call_override(self, mock_client_cls):
        captured_timeouts = []

        def make_client(**kwargs):
            captured_timeouts.append(_extract_timeout_ms(kwargs["http_options"]))
            client = MagicMock()
            client.models.generate_content.return_value = _make_fake_response()
            return client

        mock_client_cls.side_effect = make_client
        proc = self._build_processor(
            env_overrides={
                "GOOGLE_TIMEOUT_STANDARD_SECONDS": "120",
                "GOOGLE_TIMEOUT_FLEX_SECONDS": "450",
            }
        )

        proc.analisar_com_gemini(input_text="1", prompt="p", service_tier="standard")
        proc.analisar_com_gemini(input_text="2", prompt="p", service_tier="flex")
        proc.analisar_com_gemini(
            input_text="3", prompt="p", service_tier="standard", timeout=45.5
        )

        self.assertEqual(captured_timeouts, [120_000, 450_000, 45_500])
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.random.uniform", return_value=0.1)
    @patch("csctracker_ai_core.service.IaProcessor.time.sleep")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_backoff_applied_only_on_transient_errors(
        self, mock_client_cls, mock_sleep, _mock_uniform
    ):
        proc = self._build_processor(
            free_keys="free_1",
            paid_keys="paid_1",
            env_overrides={
                "GOOGLE_RETRY_BACKOFF_BASE_SECONDS": "0.5",
                "GOOGLE_RETRY_BACKOFF_MAX_SECONDS": "2.0",
            },
        )

        # 1) Erros transitórios 503 -> backoff exponencial (0.5+0.1, 1.0+0.1, 2.0+0.1) e sucesso na 4ª
        calls = {"n": 0}

        def transient_then_ok(**kwargs):
            calls["n"] += 1
            if calls["n"] <= 3:
                raise RuntimeError("503 Service Unavailable")
            return _make_fake_response()

        mock_client_cls.return_value.models.generate_content.side_effect = (
            transient_then_ok
        )
        proc.analisar_com_gemini(input_text="t", prompt="p")
        slept = [round(c.args[0], 3) for c in mock_sleep.call_args_list]
        self.assertEqual(slept, [0.6, 1.1, 2.1])

        # 2) Erro 429 -> NUNCA faz backoff sleep
        mock_sleep.reset_mock()
        calls_429 = {"n": 0}

        def quota_then_ok(**kwargs):
            calls_429["n"] += 1
            if calls_429["n"] == 1:
                raise RuntimeError("429 RESOURCE_EXHAUSTED PerMinute")
            return _make_fake_response()

        mock_client_cls.return_value.models.generate_content.side_effect = quota_then_ok
        proc.analisar_com_gemini(input_text="q", prompt="p")
        mock_sleep.assert_not_called()

        # 3) JSONDecodeError -> NUNCA faz backoff sleep
        mock_sleep.reset_mock()
        calls_json = {"n": 0}

        def bad_json_then_ok(**kwargs):
            calls_json["n"] += 1
            if calls_json["n"] == 1:
                return _make_fake_response("NOT_JSON")
            return _make_fake_response('{"ok": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = (
            bad_json_then_ok
        )
        proc.analisar_com_gemini(input_text="j", prompt="p", return_json=True)
        mock_sleep.assert_not_called()

        # 4) Falha total: não dorme após a última tentativa
        mock_sleep.reset_mock()
        proc2 = self._build_processor(
            paid_keys="paid_only",
            env_overrides={
                "GOOGLE_RETRY_BACKOFF_BASE_SECONDS": "0.5",
                "GOOGLE_RETRY_BACKOFF_MAX_SECONDS": "4.0",
            },
        )
        # get_total_capacity() = 1 * 1 = 1 -> max_tentativas = 3 -> dorme apenas 2 vezes
        mock_client_cls.return_value.models.generate_content.side_effect = RuntimeError(
            "503 always down"
        )
        with self.assertRaises(GeminiServiceException):
            proc2.analisar_com_gemini(input_text="fail", prompt="p")
        self.assertEqual(mock_sleep.call_count, 2)

        proc.close()
        proc2.close()


class TestId81SlotReleaseAndClickHouseResilience(unittest.TestCase):
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_slot_released_before_telemetry_and_never_double_released(
        self, mock_client_cls
    ):
        mock_client_cls.return_value.models.generate_content.return_value = (
            _make_fake_response()
        )
        call_order = []

        with patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits="gemini-4-hydrogen:flash=5",
                google_paid_keys="paid_key_1",
            )
            proc.click_house = ch_instance

            orig_release = proc.api_key_rotator.liberar_slot_model
            release_count = {"n": 0}

            def tracked_release(key, model):
                release_count["n"] += 1
                call_order.append("release_slot")
                return orig_release(key, model)

            def tracked_telemetry(*args, **kwargs):
                call_order.append("telemetry")

            proc.api_key_rotator.liberar_slot_model = tracked_release
            proc.click_house.log_event_telemetry.side_effect = tracked_telemetry

            proc.analisar_com_gemini(input_text="hi", prompt="p")

            self.assertEqual(call_order, ["release_slot", "telemetry"])
            self.assertEqual(release_count["n"], 1)
            proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.time.sleep")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_no_double_release_when_telemetry_or_gemini_raises(
        self, mock_client_cls, _mock_sleep
    ):
        with patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits="gemini-4-hydrogen:flash=5",
                google_paid_keys="paid_key_1",
            )
            proc.click_house = ch_instance

            orig_release = proc.api_key_rotator.liberar_slot_model
            release_count = {"n": 0}

            def tracked_release(key, model):
                release_count["n"] += 1
                return orig_release(key, model)

            proc.api_key_rotator.liberar_slot_model = tracked_release

            # Caso 1: telemetria lança exceção na 1ª tentativa e sucesso na 2ª -> 1 release por tentativa
            attempts = {"n": 0}

            def telemetry_flaky(*args, **kwargs):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise RuntimeError("clickhouse boom")

            mock_client_cls.return_value.models.generate_content.return_value = (
                _make_fake_response()
            )
            proc.click_house.log_event_telemetry.side_effect = telemetry_flaky
            proc.analisar_com_gemini(input_text="hi", prompt="p")
            self.assertEqual(release_count["n"], 2)
            self.assertEqual(
                proc.api_key_rotator._active_slots["paid_key_1"]["gemini-4-hydrogen"], 0
            )
            proc.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_init_db_single_persistent_client_timeouts_and_fail_fast(
        self, mock_get_client
    ):
        fake_client = MagicMock()
        mock_get_client.return_value = fake_client

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "false",
                "CLICKHOUSE_CONNECT_TIMEOUT": "3",
                "CLICKHOUSE_SEND_RECEIVE_TIMEOUT": "15",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local", port=8123, username="u", password="p")

            # Apenas 1 cliente criado no boot para CREATE TABLE + 3 ALTER TABLE
            self.assertEqual(mock_get_client.call_count, 1)
            self.assertEqual(fake_client.command.call_count, 4)
            kwargs = mock_get_client.call_args.kwargs
            self.assertEqual(kwargs["connect_timeout"], 3.0)
            self.assertEqual(kwargs["send_receive_timeout"], 15.0)

            # Gravações reutilizam o mesmo cliente persistente
            db.log_event_telemetry(
                "evt-1",
                {"input": 10, "image": 0, "output": 5, "reasoning": 0},
                "payload",
                "result",
                "gemini-4-hydrogen-paid",
                "task",
                0.5,
                "standard",
            )
            self.assertEqual(mock_get_client.call_count, 1)
            fake_client.insert.assert_called_once()
            db.close()
            fake_client.close.assert_called_once()

        # Fail-fast no boot: se falhar na 1ª tentativa, não abre outras 3 conexões
        mock_get_client.reset_mock()
        mock_get_client.side_effect = RuntimeError("Connection refused")
        with patch.dict(
            os.environ, {"CLICKHOUSE_ASYNC_TELEMETRY": "false"}, clear=False
        ):
            db_offline = ClickHouseDb(host="ch.offline", port=8123)
            self.assertEqual(mock_get_client.call_count, 1)
            db_offline.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_persistent_client_auto_reconnects_after_failure(self, mock_get_client):
        client_1 = MagicMock()
        client_2 = MagicMock()
        client_1.insert.side_effect = RuntimeError("Broken pipe")
        mock_get_client.side_effect = [client_1, client_2]

        with patch.dict(
            os.environ, {"CLICKHOUSE_ASYNC_TELEMETRY": "false"}, clear=False
        ):
            db = ClickHouseDb(host="ch.local")
            db.log_event_telemetry(
                "evt-recon",
                {"input": 1, "image": 0, "output": 2, "reasoning": 0},
                "p",
                "r",
                "m-paid",
                "t",
                0.1,
                "standard",
            )
            client_1.close.assert_called_once()
            client_2.insert.assert_called_once()
            db.close()
            client_2.close.assert_called_once()

    def test_telemetry_closes_read_client_in_finally_on_success_and_error(self):
        fake_db = MagicMock()
        client_ok = MagicMock()
        client_ok.query.return_value.named_results.return_value = [{"task": "x"}]
        fake_db.get_ch_client.return_value = client_ok

        telemetry = Telemetry(db=fake_db)
        rows = telemetry.get_telemetry_data("day", "today")
        self.assertEqual(rows, [{"task": "x"}])
        client_ok.close.assert_called_once()

        # Mesmo em exceção na query, client.close() deve ser chamado no finally
        client_err = MagicMock()
        client_err.query.side_effect = RuntimeError("Query timeout")
        fake_db.get_ch_client.return_value = client_err

        rows_err = telemetry.get_telemetry_data("day", "today")
        self.assertEqual(rows_err, [])
        client_err.close.assert_called_once()


class TestId82AsyncTelemetryBatching(unittest.TestCase):
    def _sample_event(self, db, event_id, payload="p", result="r"):
        db.log_event_telemetry(
            event_id,
            {"input": 10, "image": 0, "output": 5, "reasoning": 1},
            payload,
            result,
            "gemini-4-hydrogen-paid",
            "test_task",
            0.25,
            "standard",
        )

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_async_batches_by_batch_size(self, mock_get_client):
        fake_client = MagicMock()
        inserted_batches = []
        done_event = threading.Event()

        def capture_insert(table, rows, column_names=None):
            inserted_batches.append(list(rows))
            done_event.set()

        fake_client.insert.side_effect = capture_insert
        mock_get_client.return_value = fake_client

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_BATCH_SIZE": "3",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            try:
                self._sample_event(db, "e1")
                self._sample_event(db, "e2")
                self._sample_event(db, "e3")
                self.assertTrue(done_event.wait(timeout=2.0))
                self.assertEqual(len(inserted_batches), 1)
                self.assertEqual(len(inserted_batches[0]), 3)
                self.assertEqual(
                    [r[1] for r in inserted_batches[0]], ["e1", "e2", "e3"]
                )
            finally:
                db.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_async_flushes_by_interval_when_below_batch_size(self, mock_get_client):
        fake_client = MagicMock()
        inserted_batches = []
        done_event = threading.Event()

        def capture_insert(table, rows, column_names=None):
            inserted_batches.append(list(rows))
            done_event.set()

        fake_client.insert.side_effect = capture_insert
        mock_get_client.return_value = fake_client

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_BATCH_SIZE": "20",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "0.1",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            try:
                self._sample_event(db, "e1")
                self._sample_event(db, "e2")
                self.assertTrue(done_event.wait(timeout=2.0))
                self.assertEqual(len(inserted_batches), 1)
                self.assertEqual([r[1] for r in inserted_batches[0]], ["e1", "e2"])
            finally:
                db.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_queue_respects_event_limit_and_ram_cap(self, mock_get_client):
        fake_client = MagicMock()
        mock_get_client.return_value = fake_client

        # 1) Teste de teto de RAM (CLICKHOUSE_QUEUE_MAX_MB = 0.0005 -> ~524 bytes)
        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_QUEUE_MAXSIZE": "100",
                "CLICKHOUSE_QUEUE_MAX_MB": "0.0005",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            try:
                # Payload de 2000 bytes excede ~524 bytes -> descartado sem travar
                self._sample_event(db, "huge", payload="x" * 2000, result="y" * 2000)
                self.assertTrue(db.flush(timeout=2.0))
                fake_client.insert.assert_not_called()
            finally:
                db.close()

        # 2) Teste de teto de eventos (CLICKHOUSE_QUEUE_MAXSIZE = 2) com worker bloqueado no insert
        block_insert = threading.Event()
        in_insert = threading.Event()
        inserted_ids = []

        def slow_insert(table, rows, column_names=None):
            in_insert.set()
            block_insert.wait(timeout=2.0)
            inserted_ids.extend(r[1] for r in rows)

        fake_client.insert.side_effect = slow_insert
        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_QUEUE_MAXSIZE": "2",
                "CLICKHOUSE_BATCH_SIZE": "1",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            db2 = ClickHouseDb(host="ch.local")
            try:
                self._sample_event(db2, "first")
                self.assertTrue(in_insert.wait(timeout=2.0))
                # Fila agora aceita até 2 eventos; o 3º e 4º devem ser descartados imediatamente
                self._sample_event(db2, "q1")
                self._sample_event(db2, "q2")
                self._sample_event(db2, "dropped_3")
                self._sample_event(db2, "dropped_4")
                block_insert.set()
                self.assertTrue(db2.flush(timeout=2.0))
                self.assertEqual(inserted_ids, ["first", "q1", "q2"])
            finally:
                block_insert.set()
                db2.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_async_batch_retries_once_and_discards_on_double_failure(
        self, mock_get_client
    ):
        client_1 = MagicMock()
        client_2 = MagicMock()
        client_3 = MagicMock()
        client_4 = MagicMock()

        # Batch 1: client_1 falha, reconecta em client_2 e sucede
        client_1.insert.side_effect = RuntimeError("CH restarting")
        # Batch 2: client_2 falha, reconecta em client_3 que também falha -> descarta batch 2
        call_state = {"c2_calls": 0}

        def c2_insert(table, rows, column_names=None):
            call_state["c2_calls"] += 1
            if call_state["c2_calls"] == 2:
                raise RuntimeError("CH down 1")

        client_2.insert.side_effect = c2_insert
        client_3.insert.side_effect = RuntimeError("CH down 2")

        mock_get_client.side_effect = [client_1, client_2, client_3, client_4]

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_BATCH_SIZE": "1",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            try:
                self._sample_event(db, "b1")
                self.assertTrue(db.flush(timeout=2.0))
                self.assertEqual(client_2.insert.call_count, 1)

                self._sample_event(db, "b2_dropped")
                self.assertTrue(db.flush(timeout=2.0))
                self.assertEqual(client_3.insert.call_count, 1)

                # Worker continua vivo e grava batch 3 com client_4
                self._sample_event(db, "b3_ok")
                self.assertTrue(db.flush(timeout=2.0))
                client_4.insert.assert_called_once()
            finally:
                db.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_flush_and_close_drain_pending_events(self, mock_get_client):
        fake_client = MagicMock()
        inserted_ids = []

        def capture_insert(table, rows, column_names=None):
            inserted_ids.extend(r[1] for r in rows)

        fake_client.insert.side_effect = capture_insert
        mock_get_client.return_value = fake_client

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_BATCH_SIZE": "50",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "60",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            self._sample_event(db, "f1")
            self._sample_event(db, "f2")
            self.assertTrue(db.flush(timeout=2.0))
            self.assertEqual(inserted_ids, ["f1", "f2"])

            self._sample_event(db, "c1")
            db.close(timeout=2.0)
            self.assertEqual(inserted_ids, ["f1", "f2", "c1"])
            fake_client.close.assert_called_once()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_sync_kill_switch_disables_worker_thread(self, mock_get_client):
        fake_client = MagicMock()
        mock_get_client.return_value = fake_client

        with patch.dict(
            os.environ, {"CLICKHOUSE_ASYNC_TELEMETRY": "false"}, clear=False
        ):
            db = ClickHouseDb(host="ch.local")
            self.assertIsNone(db._worker_thread)
            self._sample_event(db, "sync-1")
            fake_client.insert.assert_called_once()
            db.close()

    @patch("csctracker_ai_core.service.ClickHouseDb.clickhouse_connect.get_client")
    def test_sanitizes_none_fields_and_recovers_valid_rows_on_poison_pill_batch(
        self, mock_get_client
    ):
        inserted_rows = []
        client = MagicMock()

        def flaky_insert(table, rows, column_names=None):
            # Simula falha quando 'bad-event' está no lote (seja em batch ou unitário)
            if any(r[1] == "bad-event" for r in rows):
                raise RuntimeError("DataError: invalid row")
            inserted_rows.extend(rows)

        client.insert.side_effect = flaky_insert
        mock_get_client.return_value = client

        with patch.dict(
            os.environ,
            {
                "CLICKHOUSE_ASYNC_TELEMETRY": "true",
                "CLICKHOUSE_BATCH_SIZE": "3",
                "CLICKHOUSE_FLUSH_INTERVAL_SECONDS": "30",
            },
            clear=False,
        ):
            db = ClickHouseDb(host="ch.local")
            try:
                # Sanitização de None em colunas não-Nullable
                row, _ = db._build_telemetry_row(
                    "evt-none",
                    {"input": None, "image": None, "output": None, "reasoning": None},
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
                self.assertEqual(row[2:6], [0, 0, 0, 0])
                self.assertEqual(row[7:10], ["", "", ""])
                self.assertEqual(row[10], 0.0)
                self.assertEqual(row[11], "standard")

                # Batch com 2 válidos + 1 poison pill -> fallback unitário salva os 2 válidos
                self._sample_event(db, "ok-1")
                self._sample_event(db, "bad-event")
                self._sample_event(db, "ok-2")
                self.assertTrue(db.flush(timeout=2.0))
                self.assertEqual([r[1] for r in inserted_rows], ["ok-1", "ok-2"])
            finally:
                db.close()


class TestHardGuardrailsAntiLoopAndNullSafety(unittest.TestCase):
    @patch("csctracker_ai_core.service.IaProcessor.time.sleep")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_hard_cap_on_non_quota_retries_and_error_telemetry_logged(
        self, mock_client_cls, _mock_sleep
    ):
        mock_client_cls.return_value.models.generate_content.side_effect = RuntimeError(
            "503 backend timeout"
        )
        with patch.dict(
            os.environ,
            {
                "GOOGLE_RETRY_BACKOFF_BASE_SECONDS": "0",
                "GOOGLE_MAX_NON_QUOTA_ERRORS": "4",
            },
            clear=False,
        ), patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            # 10 chaves × 6 modelos = 62 tentativas potenciais, mas teto rígido limita a 5 chamadas!
            proc = IaProcessor(
                google_models_limits="gemini-4-argon=15,gemini-3.8-flash=50,gemini-3.1-flash-lite=500",
                google_paid_keys=",".join(f"paid_{i}" for i in range(10)),
                google_tier_fallbacks="pro=gemini-4-neon:15,flash=gemini-4-hydrogen:50,lite=gemini-3.5-flash-lite:500",
            )
            proc.click_house = ch_instance

            with self.assertRaises(GeminiServiceException):
                proc.analisar_com_gemini(
                    input_text="msg",
                    prompt="p",
                    model_variant="lite",
                    service_tier="flex",
                )

            # Jamais escalou para flash/pro/neon e parou após 5 chamadas (4 erros + 1 final)
            called_models = [
                c.kwargs["model"]
                for c in mock_client_cls.return_value.models.generate_content.call_args_list
            ]
            self.assertEqual(len(called_models), 5)
            self.assertTrue(
                all(
                    m in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite")
                    for m in called_models
                ),
                f"Modelos inesperados chamados: {called_models}",
            )
            # Todas as 5 tentativas com falha foram registradas no ClickHouse
            self.assertEqual(proc.click_house.log_event_telemetry.call_count, 5)
            for call in proc.click_house.log_event_telemetry.call_args_list:
                self.assertTrue(str(call.args[3]).startswith("ERROR [RuntimeError]:"))
            proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.time.sleep")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_handles_none_tokens_none_text_and_string_modality_safely(
        self, mock_client_cls, _mock_sleep
    ):
        resp_none = MagicMock()
        resp_none.text = None
        resp_none.usage_metadata = MagicMock()
        resp_none.usage_metadata.prompt_token_count = None
        resp_none.usage_metadata.candidates_token_count = None
        resp_none.usage_metadata.thoughts_token_count = 120
        modality_item = MagicMock()
        modality_item.modality = "TEXT"
        modality_item.token_count = None
        resp_none.usage_metadata.prompt_tokens_details = [modality_item]

        mock_client_cls.return_value.models.generate_content.return_value = resp_none

        with patch.dict(
            os.environ, {"GOOGLE_RETRY_BACKOFF_BASE_SECONDS": "0"}, clear=False
        ), patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits="gemini-3.1-flash-lite=500",
                google_paid_keys="paid_1",
            )
            proc.click_house = ch_instance

            # 1) return_json=False: retorna "" sem lançar TypeError/AttributeError e grava telemetria
            result, input_tokens, _ = proc.analisar_com_gemini(
                input_text="hi",
                prompt="p",
                return_json=False,
                model_variant="lite",
            )
            self.assertEqual(result, "")
            self.assertEqual(input_tokens, 0)
            proc.click_house.log_event_telemetry.assert_called_once()
            logged_tokens = proc.click_house.log_event_telemetry.call_args.args[1]
            self.assertEqual(logged_tokens["output"], 120)
            self.assertEqual(logged_tokens["reasoning"], 120)
            self.assertEqual(proc.click_house.log_event_telemetry.call_args.args[3], "")

            # 2) return_json=True com response.text=None: trata como JSONDecodeError (não TypeError),
            # grava telemetria e encerra no teto sem loop infinito
            proc.click_house.log_event_telemetry.reset_mock()
            with self.assertRaises(GeminiServiceException):
                proc.analisar_com_gemini(
                    input_text="hi",
                    prompt="p",
                    return_json=True,
                    model_variant="lite",
                )
            self.assertEqual(proc.click_house.log_event_telemetry.call_count, 3)
            proc.close()


if __name__ == "__main__":
    unittest.main()
