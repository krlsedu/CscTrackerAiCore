#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import json
import logging
import math
import time
import uuid

from google import genai
from google.genai import types

from .ApiKeyRotator import APIKeyRotator
from .ClickHouseDb import ClickHouseDb


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

    def __init__(
        self,
        host="localhost",
        port=8123,
        username="admin",
        password="admin",
        google_models_limits=None,
        google_free_keys=None,
        google_paid_keys=None,
    ):
        self.logger = logging.getLogger()
        self.api_key_rotator = APIKeyRotator(
            self.logger, google_models_limits, google_free_keys, google_paid_keys
        )
        self.click_house = ClickHouseDb(host, port, username, password)

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
    ):
        """
        Analisa utilizando Gemini com suporte a fallback Free -> Paid e Retry Automático.
        """
        logger = self.logger
        rotator = self.api_key_rotator

        ano_atual = time.strftime("%Y")
        prompt_final = f"{prompt} {ano_atual}\n{input_text}"

        self.estimate_tokens_rough(prompt_final)

        # Loop de tentativas baseado na capacidade instalada
        max_tentativas = rotator.get_total_capacity() + 2
        tentativa_atual = 0

        while tentativa_atual < max_tentativas:
            tentativa_atual += 1

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

            try:
                client = genai.Client(api_key=key)
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

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type=(
                            "application/json" if return_json else "text/plain"
                        ),
                    ),
                )

                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
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
                    },
                    prompt_final,
                    response.text,
                    f"{model_name}-{tier}",
                    task,
                )

                rotator.liberar_slot_model(key, model_name)

                try:
                    if return_json:
                        return json.loads(response.text), input_tokens, event_id
                    else:
                        return response.text, input_tokens, event_id
                except json.JSONDecodeError:
                    logger.error(
                        f"JSON inválido retornado pelo Gemini (Key: {key[:5]}...)"
                    )
                    continue

            except Exception as e:

                rotator.liberar_slot_model(key, model_name)

                foi_erro_de_cota = rotator.processar_exception(key, model_name, e)

                if foi_erro_de_cota:
                    logger.warning(
                        f"Cota excedida na tentativa {tentativa_atual}. Trocando chave..."
                    )
                    continue
                else:
                    logger.error(f"Erro na API Gemini: {e}")
                    continue

        logger.error("Todas as tentativas de conexão com o Gemini falharam.")
        raise GeminiServiceException(
            "Nossos sistemas de IA estão temporariamente sobrecarregados. Tente novamente em alguns minutos."
        )

    def estimate_tokens_rough(self, text):
        if not text:
            return
        self.logger.info(f"Estimativa de tokens: {math.ceil(len(text) / 3)}")
