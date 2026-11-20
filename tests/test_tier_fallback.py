import json
import logging
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Permite rodar os testes offline mesmo em ambientes sem google-genai ou clickhouse-connect instalados
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

from csctracker_ai_core.service.ApiKeyRotator import APIKeyRotator
from csctracker_ai_core.service.IaProcessor import GeminiServiceException, IaProcessor


def _make_fake_response(text='{"ok": true}', prompt_tokens=10, output_tokens=5, thoughts_tokens=0):
    resp = MagicMock()
    resp.text = text
    resp.usage_metadata = MagicMock()
    resp.usage_metadata.prompt_token_count = prompt_tokens
    resp.usage_metadata.candidates_token_count = output_tokens
    resp.usage_metadata.thoughts_token_count = thoughts_tokens
    resp.usage_metadata.prompt_tokens_details = []
    return resp


class TestAPIKeyRotatorTierFallback(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_rotator")
        self.logger.setLevel(logging.CRITICAL)

    def test_parse_simple_and_default_limit_20_without_jumping_primary_queue(self):
        rotator = APIKeyRotator(
            self.logger,
            google_models_limits="gemini-4-hydrogen:flash=5,gemini-3.5-flash-lite:lite=10",
            google_paid_keys="paid_key_1",
            google_tier_fallbacks="flash=gemini-2.5-flash,pro=gemini-2.5-pro",
        )

        self.assertEqual(rotator.get_tier_fallback("flash"), "gemini-2.5-flash")
        self.assertEqual(rotator.get_tier_fallback("pro"), "gemini-2.5-pro")
        self.assertEqual(rotator._model_limits["gemini-2.5-flash"], 20)
        self.assertEqual(rotator._model_limits["gemini-2.5-pro"], 20)

        # Mesmo em paid_keys (onde gemini-2.5-flash tem peso 10 < gemini-4-hydrogen peso 15),
        # o modelo fallback NÃO pode furar a fila do primário enquanto não estiver ativo.
        key, model, tier = rotator.select_and_reserve_best_slot(model_variant="flash")
        self.assertEqual((key, model, tier), ("paid_key_1", "gemini-4-hydrogen", "paid"))
        rotator.liberar_slot_model(key, model)

        # Isolamento estrito flash vs lite preservado
        key_l, model_l, _ = rotator.select_and_reserve_best_slot(model_variant="lite")
        self.assertEqual(model_l, "gemini-3.5-flash-lite")
        rotator.liberar_slot_model(key_l, model_l)

    def test_parse_json_from_env(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_TIER_FALLBACKS": json.dumps(
                    {"flash": "gemini-2.5-flash", "ultra": "gemini-4-argon"}
                )
            },
        ):
            rotator = APIKeyRotator(
                self.logger,
                google_models_limits="gemini-4-hydrogen:flash=5,gemini-4-carbon:ultra=2",
                google_paid_keys="paid_key_1",
            )
            self.assertEqual(rotator.get_tier_fallback("flash"), "gemini-2.5-flash")
            self.assertEqual(rotator.get_tier_fallback("ultra"), "gemini-4-argon")
            self.assertEqual(rotator._model_limits["gemini-2.5-flash"], 20)

    def test_pro_to_ultra_transparent_fallback_preserved_with_pro_tier_fallback(self):
        rotator = APIKeyRotator(
            self.logger,
            google_models_limits="gemini-4-carbon:ultra=2",
            google_paid_keys="paid_key_1",
            google_tier_fallbacks="pro=gemini-2.5-pro",
        )
        # Sem erros: pedido 'pro' continua fazendo fallback transparente para 'ultra' primário
        key, model, _ = rotator.select_and_reserve_best_slot(model_variant="pro")
        self.assertEqual(model, "gemini-4-carbon")
        rotator.liberar_slot_model(key, model)

    def test_two_consecutive_errors_activate_cooldown_and_expire(self):
        rotator = APIKeyRotator(
            self.logger,
            google_models_limits="gemini-4-hydrogen:flash=5",
            google_paid_keys="paid_key_1",
            google_tier_fallbacks="flash=gemini-2.5-flash",
            fallback_cooldown_seconds=300,
        )

        # 1º erro não ativa fallback
        self.assertIsNone(rotator.registrar_erro_modelo("gemini-4-hydrogen", "flash"))
        self.assertFalse(rotator.is_tier_fallback_active("flash"))

        # Sucesso zera contador -> próximo erro volta a ser o 1º
        rotator.registrar_sucesso_modelo("gemini-4-hydrogen", "flash")
        self.assertIsNone(rotator.registrar_erro_modelo("gemini-4-hydrogen", "flash"))
        self.assertFalse(rotator.is_tier_fallback_active("flash"))

        # 2º erro consecutivo ativa fallback por 300s
        activated = rotator.registrar_erro_modelo("gemini-4-hydrogen", "flash")
        self.assertEqual(activated, "gemini-2.5-flash")
        self.assertTrue(rotator.is_tier_fallback_active("flash"))

        key, model, _ = rotator.select_and_reserve_best_slot(model_variant="flash")
        self.assertEqual(model, "gemini-2.5-flash")
        rotator.liberar_slot_model(key, model)

        # Após expirar os 300s, volta ao principal
        rotator._tier_fallback_until[("standard", "flash")] -= 301
        self.assertFalse(rotator.is_tier_fallback_active("flash"))
        key2, model2, _ = rotator.select_and_reserve_best_slot(model_variant="flash")
        self.assertEqual(model2, "gemini-4-hydrogen")
        rotator.liberar_slot_model(key2, model2)

    def test_without_fallbacks_configured_keeps_legacy_behavior(self):
        rotator = APIKeyRotator(
            self.logger,
            google_models_limits="gemini-4-hydrogen:flash=5",
            google_paid_keys="paid_key_1",
        )
        self.assertIsNone(rotator.registrar_erro_modelo("gemini-4-hydrogen", "flash"))
        self.assertIsNone(rotator.registrar_erro_modelo("gemini-4-hydrogen", "flash"))
        key, model, _ = rotator.select_and_reserve_best_slot(model_variant="flash")
        self.assertEqual(model, "gemini-4-hydrogen")
        rotator.liberar_slot_model(key, model)


class TestIaProcessorTierFallback(unittest.TestCase):
    def _build_processor(
        self,
        limits="gemini-4-hydrogen:flash=5",
        paid_keys="paid_key_1",
        free_keys=None,
        fallbacks="flash=gemini-2.5-flash",
    ):
        with patch.dict(
            os.environ, {"GOOGLE_RETRY_BACKOFF_BASE_SECONDS": "0"}, clear=False
        ), patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits=limits,
                google_free_keys=free_keys,
                google_paid_keys=paid_keys,
                google_tier_fallbacks=fallbacks,
            )
            proc.click_house = ch_instance
            return proc

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_standard_mode_triggers_shared_cooldown_after_two_errors(self, mock_client_cls):
        proc = self._build_processor()
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            if model == "gemini-4-hydrogen":
                raise RuntimeError("503 Service Unavailable")
            return _make_fake_response('{"status": "ok"}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, tokens, event_id = proc.analisar_com_gemini(
            input_text="teste",
            prompt="analise",
            model_variant="flash",
            service_tier="standard",
        )

        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(tokens, 10)
        self.assertTrue(event_id)
        self.assertEqual(
            called_models,
            ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-2.5-flash"],
        )
        # Cooldown compartilhado ativo para próximas chamadas standard
        self.assertTrue(proc.api_key_rotator.is_tier_fallback_active("flash"))
        # Telemetria registrou o modelo fallback real
        telemetry_model = proc.click_house.log_event_telemetry.call_args[0][4]
        self.assertEqual(telemetry_model, "gemini-2.5-flash-paid")

        # 2ª requisição standard já vai direto para o fallback sem bater no principal
        called_models.clear()
        result2, _, _ = proc.analisar_com_gemini(
            input_text="teste2",
            prompt="analise",
            model_variant="flash",
            service_tier="standard",
        )
        self.assertEqual(result2, {"status": "ok"})
        self.assertEqual(called_models, ["gemini-2.5-flash"])

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_flex_mode_cooldown_applies_only_to_flex_and_isolates_standard(self, mock_client_cls):
        proc = self._build_processor()
        called_models = []
        should_fail_primary = {"value": True}

        def fake_generate(model, contents, config):
            called_models.append(model)
            if should_fail_primary["value"] and model == "gemini-4-hydrogen":
                raise RuntimeError("500 Internal Error in flex")
            return _make_fake_response('{"ok": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="teste flex",
            prompt="analise",
            model_variant="flash",
            service_tier="flex",
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(
            called_models,
            ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-2.5-flash"],
        )
        # Cooldown de 5 min fica ativo SOMENTE para flex, sem contaminar standard
        self.assertTrue(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="flex")
        )
        self.assertFalse(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="standard")
        )

        # Próxima chamada flex aproveita o cooldown de 5 min e vai direto para o fallback
        called_models.clear()
        should_fail_primary["value"] = False
        result_flex_2, _, _ = proc.analisar_com_gemini(
            input_text="proxima flex",
            prompt="analise",
            model_variant="flash",
            service_tier="flex",
        )
        self.assertEqual(result_flex_2, {"ok": True})
        self.assertEqual(called_models, ["gemini-2.5-flash"])

        # Chamada standard segue normal usando o modelo principal
        called_models.clear()
        result_std, _, _ = proc.analisar_com_gemini(
            input_text="proxima standard",
            prompt="analise",
            model_variant="flash",
            service_tier="standard",
        )
        self.assertEqual(result_std, {"ok": True})
        self.assertEqual(called_models, ["gemini-4-hydrogen"])

        # Após expirar 300s no flex, flex também volta ao modelo principal
        proc.api_key_rotator._tier_fallback_until[("flex", "flash")] -= 301
        called_models.clear()
        result_flex_3, _, _ = proc.analisar_com_gemini(
            input_text="flex apos expirar",
            prompt="analise",
            model_variant="flash",
            service_tier="flex",
        )
        self.assertEqual(result_flex_3, {"ok": True})
        self.assertEqual(called_models, ["gemini-4-hydrogen"])

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_json_decode_error_counts_toward_two_errors(self, mock_client_cls):
        proc = self._build_processor()
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            if model == "gemini-4-hydrogen":
                return _make_fake_response("NOT_VALID_JSON")
            return _make_fake_response('{"recovered": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="teste json",
            prompt="analise",
            return_json=True,
            model_variant="flash",
            service_tier="standard",
        )

        self.assertEqual(result, {"recovered": True})
        self.assertEqual(
            called_models,
            ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-2.5-flash"],
        )

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_429_quota_error_does_not_increment_fallback_counter(self, mock_client_cls):
        proc = self._build_processor(
            free_keys="free_1,free_2",
            paid_keys="paid_1",
        )
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            if len(called_models) <= 2:
                raise RuntimeError("429 RESOURCE_EXHAUSTED PerMinute")
            return _make_fake_response('{"via": "paid_primary"}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="teste 429",
            prompt="analise",
            model_variant="flash",
            service_tier="standard",
        )

        self.assertEqual(result, {"via": "paid_primary"})
        self.assertEqual(
            called_models,
            ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-4-hydrogen"],
        )
        self.assertFalse(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="flex")
        )
        self.assertFalse(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="standard")
        )

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_alternates_back_to_primary_when_fallback_also_fails(self, mock_client_cls):
        proc = self._build_processor(paid_keys="paid_1,paid_2")
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            # 1-2: principal falha -> 3-4: fallback falha -> 5: principal volta e funciona
            if len(called_models) <= 4:
                raise RuntimeError("503 temporary error")
            return _make_fake_response('{"alternated": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="teste alternancia",
            prompt="analise",
            model_variant="flash",
            service_tier="standard",
        )

        self.assertEqual(result, {"alternated": True})
        self.assertEqual(
            called_models,
            [
                "gemini-4-hydrogen",
                "gemini-4-hydrogen",
                "gemini-2.5-flash",
                "gemini-2.5-flash",
                "gemini-4-hydrogen",
            ],
        )

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_alternates_back_to_primary_in_flex_mode(self, mock_client_cls):
        proc = self._build_processor(paid_keys="paid_1,paid_2")
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            if len(called_models) <= 4:
                raise RuntimeError("503 flex error")
            return _make_fake_response('{"flex_alternated": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="teste flex alternancia",
            prompt="analise",
            model_variant="flash",
            service_tier="flex",
        )

        self.assertEqual(result, {"flex_alternated": True})
        self.assertEqual(
            called_models,
            [
                "gemini-4-hydrogen",
                "gemini-4-hydrogen",
                "gemini-2.5-flash",
                "gemini-2.5-flash",
                "gemini-4-hydrogen",
            ],
        )
        self.assertFalse(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="flex")
        )
        self.assertFalse(
            proc.api_key_rotator.is_tier_fallback_active("flash", service_tier="standard")
        )

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_model_variant_none_uses_allocated_model_tier_fallback(self, mock_client_cls):
        proc = self._build_processor(
            limits="gemini-4-hydrogen:flash=5",
            paid_keys="paid_1",
            fallbacks="flash=gemini-2.5-flash",
        )
        called_models = []

        def fake_generate(model, contents, config):
            called_models.append(model)
            if model == "gemini-4-hydrogen":
                raise RuntimeError("500 error")
            return _make_fake_response('{"none_variant": true}')

        mock_client_cls.return_value.models.generate_content.side_effect = fake_generate

        result, _, _ = proc.analisar_com_gemini(
            input_text="sem variant",
            prompt="analise",
            model_variant=None,
            service_tier="standard",
        )

        self.assertEqual(result, {"none_variant": True})
        self.assertEqual(
            called_models,
            ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-2.5-flash"],
        )

    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_raises_gemini_service_exception_when_all_attempts_fail(self, mock_client_cls):
        proc = self._build_processor(paid_keys="paid_1")
        mock_client_cls.return_value.models.generate_content.side_effect = RuntimeError(
            "503 always down"
        )

        with self.assertRaises(GeminiServiceException):
            proc.analisar_com_gemini(
                input_text="sempre falha",
                prompt="analise",
                model_variant="flash",
                service_tier="standard",
            )


if __name__ == "__main__":
    unittest.main()
