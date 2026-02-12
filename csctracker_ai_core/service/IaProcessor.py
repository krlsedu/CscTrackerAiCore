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
    Exception representing errors related to the Gemini service.

    This exception is used to handle and represent various errors that may occur
    during interactions with the Gemini service. It is a custom exception that can
    be used for error handling specific to this context.
    """
    pass

class IaProcessor:
    """
    Processes input for an AI-based system with integrated API key rotation and database logging support.

    This class provides methods to perform analysis using the Gemini AI system, including handling image
    and textual inputs. It incorporates a retry mechanism with automatic fallback between free and paid
    API keys and logs telemetry data to a ClickHouse database.

    Attributes:
        logger (logging.Logger): Logger instance for logging messages and errors.
        api_key_rotator (APIKeyRotator): Manages API key rotation for free and paid API keys with
                                         error handling capabilities.
        click_house (ClickHouseDb): Handles database operations for logging telemetry data.
    """
    def __init__(self, host="localhost", port=8123, username='admin', password='admin', google_models_limits = None, google_free_keys = None, google_paid_keys = None):
        self.logger = logging.getLogger()
        self.api_key_rotator = APIKeyRotator(self.logger, google_models_limits, google_free_keys, google_paid_keys)
        self.click_house = ClickHouseDb(host, port, username, password)

    def analisar_com_gemini(self, input_text: str = "", prompt: str = "", image_base64: str = None, task: str = None, return_json: bool = True, event_id: str = None):
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

            # 1. Pede o melhor slot disponível (Free ou Paid)
            key, model_name = rotator.select_and_reserve_best_slot()

            if not key:
                # Nenhuma chave disponível agora
                logger.warning("Nenhum slot disponível no momento. Aguardando...")
                time.sleep(1)
                if tentativa_atual >= max_tentativas: break
                continue

            try:
                # 2. Executa a chamada
                client = genai.Client(api_key=key)
                contents = []

                if not image_base64:
                    if return_json:
                        contents.append(f"Responda APENAS com um objeto JSON válido. Não use markdown. \n{prompt_final}")
                    else:
                        contents.append(prompt_final)
                else:
                    contents.append(prompt_final)
                    image_bytes = base64.b64decode(image_base64)
                    contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json" if return_json else "text/plain"
                    )
                )

                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                detalhes = response.usage_metadata.prompt_tokens_details
                image_tokens = 0
                if detalhes:
                    for item in detalhes:
                        if item.modality == 'IMAGE' or item.modality.name == 'IMAGE':
                            image_tokens = item.token_count

                if not event_id:
                    event_id = str(uuid.uuid4())
                self.click_house.log_event_telemetry(
                    event_id,
                    {'input': input_tokens, 'image': image_tokens, 'output': output_tokens},
                    prompt_final,
                    response.text,
                    model_name,
                    task
                )
                # 3. Sucesso: Libera slot e retorna o JSON
                rotator.liberar_slot_model(key, model_name)

                try:
                    if return_json:
                        return json.loads(response.text), input_tokens, event_id
                    else:
                        return response.text, input_tokens, event_id
                except json.JSONDecodeError:
                    logger.error(f"JSON inválido retornado pelo Gemini (Key: {key[:5]}...)")
                    continue

            except Exception as e:
                # 4. Erro: Libera slot e reporta ao rotator para análise
                rotator.liberar_slot_model(key, model_name)

                foi_erro_de_cota = rotator.processar_exception(key, model_name, e)

                if foi_erro_de_cota:
                    logger.warning(f"Cota excedida na tentativa {tentativa_atual}. Trocando chave...")
                    # O loop 'continue' vai forçar select_and_reserve_best_slot a pegar outra chave
                    continue
                else:
                    # Erros de rede ou prompt inválido
                    logger.error(f"Erro na API Gemini: {e}")
                    continue

        # Fim do loop sem sucesso
        logger.error("Todas as tentativas de conexão com o Gemini falharam.")
        raise GeminiServiceException(
            "Nossos sistemas de IA estão temporariamente sobrecarregados. Tente novamente em alguns minutos.")

    def estimate_tokens_rough(self, text):
        if not text:
            return
        self.logger.info(f"Estimativa de tokens: {math.ceil(len(text) / 4)}")