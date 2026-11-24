import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Permite rodar os testes offline mesmo sem google-genai ou clickhouse-connect instalados
if "google" not in sys.modules:
    google_mod = types.ModuleType("google")
    genai_mod = types.ModuleType("google.genai")
    genai_types_mod = types.ModuleType("google.genai.types")

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

if "clickhouse_connect" not in sys.modules:
    ch_mod = types.ModuleType("clickhouse_connect")
    ch_mod.get_client = MagicMock()
    sys.modules["clickhouse_connect"] = ch_mod

from csctracker_ai_core.service.IaProcessor import (
    GeminiServiceException,
    IaProcessor,
    UnauthorizedUserException,
)


def _make_fake_response(text='{"ok": true}'):
    resp = MagicMock()
    resp.text = text
    resp.usage_metadata = MagicMock()
    resp.usage_metadata.prompt_token_count = 12
    resp.usage_metadata.candidates_token_count = 6
    resp.usage_metadata.thoughts_token_count = 0
    resp.usage_metadata.prompt_tokens_details = []
    return resp


class TestIaProcessorAllowedUsers(unittest.TestCase):
    def _build_processor(
        self,
        free_keys=None,
        paid_keys="paid_key_1",
        allowed_users=None,
        limits="gemini-4-hydrogen:flash=5",
    ):
        with patch("csctracker_ai_core.service.IaProcessor.ClickHouseDb") as ch_cls:
            ch_instance = MagicMock()
            ch_cls.return_value = ch_instance
            proc = IaProcessor(
                google_models_limits=limits,
                google_free_keys=free_keys,
                google_paid_keys=paid_keys,
                allowed_users=allowed_users,
            )
            proc.click_house = ch_instance
            return proc

    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_allowed_users_none_or_empty_preserves_legacy_unrestricted_behavior(
        self, mock_client_cls, mock_request_info
    ):
        client = MagicMock()
        client.models.generate_content.return_value = _make_fake_response()
        mock_client_cls.return_value = client

        for cfg in (None, [], "", "  , "):
            proc = self._build_processor(
                free_keys=None, paid_keys="paid_key_1", allowed_users=cfg
            )
            result, tokens, event_id = proc.analisar_com_gemini(
                input_text="oi", prompt="teste", model_variant="flash"
            )
            self.assertEqual(result, {"ok": True})
            self.assertEqual(tokens, 12)
            self.assertTrue(event_id)
            proc.close()

        mock_request_info.get_user_email.assert_not_called()

    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_authorized_user_case_insensitive_can_use_paid_keys(
        self, mock_client_cls, mock_request_info
    ):
        mock_request_info.get_user_email.return_value = "CARLOS@CSCTRACKER.COM"
        client = MagicMock()
        client.models.generate_content.return_value = _make_fake_response()
        mock_client_cls.return_value = client

        proc = self._build_processor(
            free_keys=None,
            paid_keys="paid_key_1",
            allowed_users="  carlos@csctracker.com , outro@csc.com ",
        )
        result, _, _ = proc.analisar_com_gemini(
            input_text="oi", prompt="teste", model_variant="flash"
        )
        self.assertEqual(result, {"ok": True})
        mock_client_cls.assert_called_once()
        self.assertEqual(mock_client_cls.call_args.kwargs["api_key"], "paid_key_1")
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_unauthorized_user_restricted_to_free_pool_succeeds_when_free_available(
        self, mock_client_cls, mock_request_info
    ):
        mock_request_info.get_user_email.return_value = "intruso@externo.com"
        client = MagicMock()
        client.models.generate_content.return_value = _make_fake_response()
        mock_client_cls.return_value = client

        proc = self._build_processor(
            free_keys="free_key_1",
            paid_keys="paid_key_1",
            allowed_users=["carlos@csctracker.com"],
        )
        result, _, _ = proc.analisar_com_gemini(
            input_text="oi", prompt="teste", model_variant="flash"
        )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(mock_client_cls.call_args.kwargs["api_key"], "free_key_1")
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_unauthorized_user_without_free_keys_raises_403_without_calling_gemini(
        self, mock_client_cls, mock_request_info
    ):
        mock_request_info.get_user_email.return_value = "intruso@externo.com"

        proc = self._build_processor(
            free_keys=None,
            paid_keys="paid_key_1",
            allowed_users=["carlos@csctracker.com"],
        )
        with self.assertRaises(UnauthorizedUserException) as ctx:
            proc.analisar_com_gemini(
                input_text="oi", prompt="teste", model_variant="flash"
            )
        self.assertIsInstance(ctx.exception, GeminiServiceException)
        self.assertEqual(ctx.exception.status_code, 403)
        mock_client_cls.assert_not_called()
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_unauthorized_user_with_forced_paid_raises_403_immediately(
        self, mock_client_cls, mock_request_info
    ):
        mock_request_info.get_user_email.return_value = None

        proc = self._build_processor(
            free_keys="free_key_1",
            paid_keys="paid_key_1",
            allowed_users=["carlos@csctracker.com"],
        )
        with self.assertRaises(UnauthorizedUserException):
            proc.analisar_com_gemini(
                input_text="oi",
                prompt="teste",
                model_variant="flash",
                forced_paid=True,
            )
        mock_client_cls.assert_not_called()
        proc.close()

    @patch("csctracker_ai_core.service.IaProcessor.time.sleep")
    @patch("csctracker_ai_core.service.IaProcessor.RequestInfo")
    @patch("csctracker_ai_core.service.IaProcessor.genai.Client")
    def test_unauthorized_user_when_free_pool_exhausted_never_uses_paid_and_raises_403(
        self, mock_client_cls, mock_request_info, _mock_sleep
    ):
        mock_request_info.get_user_email.return_value = "intruso@externo.com"
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError(
            "429 RESOURCE_EXHAUSTED GenerateRequestsPerMinutePerProjectPerModel"
        )
        mock_client_cls.return_value = client

        proc = self._build_processor(
            free_keys="free_key_1",
            paid_keys="paid_key_1",
            allowed_users=["carlos@csctracker.com"],
        )
        with self.assertRaises(UnauthorizedUserException):
            proc.analisar_com_gemini(
                input_text="oi", prompt="teste", model_variant="flash"
            )

        used_keys = [c.kwargs["api_key"] for c in mock_client_cls.call_args_list]
        self.assertEqual(used_keys, ["free_key_1"])
        proc.close()


if __name__ == "__main__":
    unittest.main()
