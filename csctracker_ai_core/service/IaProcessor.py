#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import base64
import datetime
import json
import logging
import math
import os
import random
import threading
import time
import uuid
import weakref

from google import genai
from google.genai import types
from google.genai._interactions.types import thinking_level

from .ApiKeyRotator import APIKeyRotator
from .ClickHouseDb import ClickHouseDb


def _parse_float_env(env_name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(env_name)
    if raw is None or not raw.strip():
        return default
    try:
        parsed = float(raw.strip())
        return parsed if parsed >= minimum else default
    except ValueError:
        return default


def _atexit_close_processor(proc_ref):
    proc = proc_ref()
    if proc is not None:
        try:
            proc.close()
        except Exception:
            pass


class GeminiServiceException(Exception):
    """
    Represents a custom exception for the Gemini service.

    This exception is designed to handle errors specific to the Gemini service
    and can be used for custom error handling processes where more context or
    a better understanding of the failure is required.
    """

    pass


class IaProcessor:
    """
    IaProcessor class.

    This class facilitates interactions with a Gemini-based AI system, providing support for API key
    rotation, automatic retries, and fallback strategies between free and paid keys. Its primary purpose
    is to process and generate AI-driven content while managing telemetry and ensuring optimal utilization
    of API capacities.

    :ivar logger: Logger instance for logging messages and errors.
    :type logger: logging.Logger
    :ivar api_key_rotator: API key rotator instance for managing key selection and utilization.
    :type api_key_rotator: APIKeyRotator
    :ivar click_house: Database instance for storing telemetry and logging events.
    :type click_house: ClickHouseDb
    """

    DEFAULT_TIMEOUT_STANDARD_SECONDS = 300.0
    DEFAULT_TIMEOUT_FLEX_SECONDS = 600.0
    DEFAULT_RETRY_BACKOFF_BASE_SECONDS = 0.5
    DEFAULT_RETRY_BACKOFF_MAX_SECONDS = 4.0

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        google_models_limits=None,
        google_free_keys=None,
        google_paid_keys=None,
        google_tier_fallbacks=None,
    ):
        self.logger = logging.getLogger()
        self.api_key_rotator = APIKeyRotator(
            self.logger,
            google_models_limits,
            google_free_keys,
            google_paid_keys,
            google_tier_fallbacks=google_tier_fallbacks,
        )
        self.click_house = ClickHouseDb(host, port, username, password)

        self._timeout_standard_seconds = _parse_float_env(
            "GOOGLE_TIMEOUT_STANDARD_SECONDS",
            self.DEFAULT_TIMEOUT_STANDARD_SECONDS,
            minimum=0.001,
        )
        self._timeout_flex_seconds = _parse_float_env(
            "GOOGLE_TIMEOUT_FLEX_SECONDS",
            self.DEFAULT_TIMEOUT_FLEX_SECONDS,
            minimum=0.001,
        )
        self._retry_backoff_base_seconds = _parse_float_env(
            "GOOGLE_RETRY_BACKOFF_BASE_SECONDS",
            self.DEFAULT_RETRY_BACKOFF_BASE_SECONDS,
            minimum=0.0,
        )
        self._retry_backoff_max_seconds = _parse_float_env(
            "GOOGLE_RETRY_BACKOFF_MAX_SECONDS",
            self.DEFAULT_RETRY_BACKOFF_MAX_SECONDS,
            minimum=0.0,
        )

        self._clients = {}
        self._clients_lock = threading.Lock()
        self.api_key_rotator.register_on_key_removed(self._evict_clients_for_key)

        self._atexit_handler = lambda ref=weakref.ref(self): _atexit_close_processor(ref)
        atexit.register(self._atexit_handler)

    def _resolve_timeout_ms(self, service_tier: str, timeout: float = None) -> int:
        if timeout is not None:
            seconds = float(timeout)
        elif service_tier == "flex":
            seconds = self._timeout_flex_seconds
        else:
            seconds = self._timeout_standard_seconds
        return max(1, int(seconds * 1000))

    def _get_client(self, api_key: str, timeout_ms: int):
        cache_key = (api_key, timeout_ms)
        with self._clients_lock:
            client = self._clients.get(cache_key)
            if client is None:
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=timeout_ms),
                )
                self._clients[cache_key] = client
            return client

    def _evict_clients_for_key(self, api_key: str):
        removed_clients = []
        with self._clients_lock:
            keys_to_pop = [k for k in self._clients if k[0] == api_key]
            for cache_key in keys_to_pop:
                removed_clients.append(self._clients.pop(cache_key))
        for client in removed_clients:
            if hasattr(client, "close"):
                try:
                    client.close()
                except Exception:
                    pass

    def close(self):
        """Fecha todos os clientes genai em pool e encerra a telemetria ClickHouse."""
        with self._clients_lock:
            clients = list(self._clients.values())
            self._clients.clear()

        for client in clients:
            if hasattr(client, "close"):
                try:
                    client.close()
                except Exception:
                    pass

        if hasattr(self.click_house, "close"):
            try:
                self.click_house.close()
            except Exception:
                pass

    def _compute_transient_backoff(self, erro_consecutivo: int) -> float:
        base = self._retry_backoff_base_seconds
        max_delay = self._retry_backoff_max_seconds
        if base <= 0 or max_delay <= 0:
            return 0.0
        exp_delay = min(base * (2 ** (erro_consecutivo - 1)), max_delay)
        return exp_delay + random.uniform(0.0, 0.3)

    def analisar_com_gemini(
        self,
        input_text: str = "",
        prompt: str = "",
        file_base64: str = None,
        task: str = None,
        return_json: bool = True,
        event_id: str = None,
        mime_type: str = "image/jpeg",
        model_variant: str = None,
        forced_free: bool = False,
        forced_paid: bool = False,
        thinking_level: str = "high",
        service_tier: str = "standard",
        timeout: float = None,
    ):
        """
        Analisa utilizando Gemini com suporte a fallback Free -> Paid e Retry Automático.
        """
        logger = self.logger
        rotator = self.api_key_rotator

        if not service_tier or service_tier.lower() not in ("flex", "standard"):
            service_tier = "standard"
        else:
            service_tier = service_tier.lower()

        timeout_ms = self._resolve_timeout_ms(service_tier, timeout=timeout)

        ano_atual = time.strftime("%Y")
        prompt_final = f"{prompt} {ano_atual}\n{input_text}"

        self.estimate_tokens_rough(prompt_final)

        def _resolve_effective_tier(m_name: str) -> str:
            req_tier = rotator.resolve_requested_tier(model_variant)
            if req_tier and rotator.get_tier_fallback(req_tier):
                return req_tier
            return rotator.get_model_tier(m_name)

        # Loop de tentativas baseado na capacidade instalada
        max_tentativas = rotator.get_total_capacity() + 2
        tentativa_atual = 0
        erros_transitorios_consecutivos = 0

        while tentativa_atual < max_tentativas:
            tentativa_atual += 1

            if service_tier == "flex":
                key, model_name, tier = rotator._select_and_reserve_slot(
                    model_variant=model_variant,
                    forced_free=forced_free,
                    forced_paid=forced_paid,
                    service_tier="flex",
                )
            else:
                key, model_name, tier = rotator.select_and_reserve_best_slot(
                    model_variant=model_variant,
                    forced_free=forced_free,
                    forced_paid=forced_paid,
                )

            if not key:
                logger.warning("Nenhum slot disponível no momento. Aguardando...")
                time.sleep(1)
                if tentativa_atual >= max_tentativas:
                    break
                continue

            slot_released = False

            def _release_slot_once():
                nonlocal slot_released
                if not slot_released:
                    slot_released = True
                    rotator.liberar_slot_model(key, model_name)

            try:
                client = self._get_client(key, timeout_ms)
                contents = []

                if not file_base64:
                    if return_json:
                        contents.append(
                            f"Responda APENAS com um objeto JSON válido. Não use markdown. \n{prompt_final}"
                        )
                    else:
                        contents.append(prompt_final)
                else:
                    contents.append(prompt_final)
                    image_bytes = base64.b64decode(file_base64)
                    contents.append(
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                    )

                _before = datetime.datetime.now()
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type=(
                            "application/json" if return_json else "text/plain"
                        ),
                        thinking_config=types.ThinkingConfig(
                            thinking_level=thinking_level
                        ),
                        service_tier=service_tier,
                    ),
                )
                _time_spent = datetime.datetime.now() - _before
                _time_spent = _time_spent.total_seconds()

                # Libera o slot imediatamente após o retorno do Gemini (antes de telemetria e parsing)
                _release_slot_once()

                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                reasoning_tokens = response.usage_metadata.thoughts_token_count

                if not reasoning_tokens:
                    reasoning_tokens = 0
                output_tokens += reasoning_tokens

                if not output_tokens:
                    logger.warning(f"No output tokens generated: {response.text}")
                    output_tokens = 0
                detalhes = response.usage_metadata.prompt_tokens_details
                image_tokens = 0
                if detalhes:
                    for item in detalhes:
                        if item.modality == "IMAGE" or item.modality.name == "IMAGE":
                            image_tokens = item.token_count

                if not event_id:
                    event_id = str(uuid.uuid4())
                self.click_house.log_event_telemetry(
                    event_id,
                    {
                        "input": input_tokens,
                        "image": image_tokens,
                        "output": output_tokens,
                        "reasoning": reasoning_tokens,
                    },
                    prompt_final,
                    response.text,
                    f"{model_name}-{tier}",
                    task,
                    _time_spent,
                    service_tier.lower(),
                )

                try:
                    if return_json:
                        parsed_result = json.loads(response.text)
                    else:
                        parsed_result = response.text
                except json.JSONDecodeError:
                    erros_transitorios_consecutivos = 0
                    logger.error(
                        f"JSON inválido retornado pelo Gemini (Key: {key[:5]}...)"
                    )
                    rotator.registrar_erro_modelo(
                        model_name,
                        _resolve_effective_tier(model_name),
                        service_tier=service_tier,
                    )
                    continue

                rotator.registrar_sucesso_modelo(
                    model_name,
                    _resolve_effective_tier(model_name),
                    service_tier=service_tier,
                )
                return parsed_result, input_tokens, event_id

            except Exception as e:
                _release_slot_once()

                foi_erro_de_cota = rotator.processar_exception(key, model_name, e)

                if foi_erro_de_cota:
                    erros_transitorios_consecutivos = 0
                    logger.warning(
                        f"Cota excedida na tentativa {tentativa_atual}. Trocando chave..."
                    )
                    continue
                else:
                    erros_transitorios_consecutivos += 1
                    logger.error(f"Erro na API Gemini: {e}")
                    rotator.registrar_erro_modelo(
                        model_name,
                        _resolve_effective_tier(model_name),
                        service_tier=service_tier,
                    )
                    if tentativa_atual < max_tentativas:
                        delay = self._compute_transient_backoff(
                            erros_transitorios_consecutivos
                        )
                        if delay > 0:
                            time.sleep(delay)
                    continue
            finally:
                _release_slot_once()

        logger.error("Todas as tentativas de conexão com o Gemini falharam.")
        raise GeminiServiceException(
            "Nossos sistemas de IA estão temporariamente sobrecarregados. Tente novamente em alguns minutos."
        )

    def estimate_tokens_rough(self, text):
        if not text:
            return
        self.logger.info(f"Estimativa de tokens: {math.ceil(len(text) / 3)}")
