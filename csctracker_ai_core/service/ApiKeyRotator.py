#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import time
from datetime import datetime, timezone, timedelta
from threading import Lock


class APIKeyRotator:
    """
    Handles rotation and management of API keys for free and paid tiers, ensuring
    efficient use of resources, and balancing load across available keys and models.

    The `APIKeyRotator` class manages the configuration, organization, and allocation
    of API keys, separating them into free and paid tiers. It tracks usage, enforces
    rate limits, and detects when keys are invalid or suspended. This class also
    prioritizes models based on cost and optimizes their usage across the tiers for
    cost-efficiency.

    :ivar logger: The logger instance used for logging operations.
    :type logger: logging.Logger
    :ivar google_models_limits: Configured model limits, optional.
    :ivar google_free_keys: Comma-separated free API keys, optional.
    :ivar google_paid_keys: Comma-separated paid API keys, optional.
    """

    def __init__(
        self,
        logger: logging.Logger,
        google_models_limits=None,
        google_free_keys=None,
        google_paid_keys=None,
    ):
        self.logger = logger
        self.google_models_limits = google_models_limits
        self.google_free_keys = google_free_keys
        self.google_paid_keys = google_paid_keys

        # Estruturas de dados separadas por TIER
        self._free_keys = []
        self._paid_keys = []
        self._all_keys_count = 0

        self._models = []
        self._model_limits = {}

        # Controle de estado
        self._active_slots = {}  # {key: {model: count}}
        self._suspended_until = {}  # {key: {model: timestamp}}
        self._models_by_key = {}  # {key: [modelos_ordenados_por_custo]}

        # Índices para Round-Robin (Balanceamento de Carga)
        self._free_index = 0
        self._paid_index = 0
        self._lock = Lock()

        # Regex Compilados para detecção de erro
        self._regex_429 = re.compile(r"(429|RESOURCE_EXHAUSTED)", re.IGNORECASE)
        self._regex_limit_zero = re.compile(r"limit:\s*0", re.IGNORECASE)
        self._regex_per_day = re.compile(r"(PerDay|Quota.*Day)", re.IGNORECASE)
        self._regex_per_minute = re.compile(r"(PerMinute|Quota.*Minute)", re.IGNORECASE)
        self._regex_invalid_key = re.compile(
            r"(API_KEY_INVALID|key not valid|unauthorized)", re.IGNORECASE
        )

        # 1. Carregar Configuração de Modelos (ENV ou Default)
        self._load_model_config()

        # 2. Carregar Chaves (Separando Free e Paga)
        self.load_keys()

    def _load_model_config(self):
        """
        Lê a ENV 'GOOGLE_MODEL_LIMITS'.
        Suporta dois formatos:
        1. JSON: '{"model": 1}'
        2. Simples (Portainer Friendly): 'model=1,model2=10'
        """
        default_limits = {
            "gemini-3-flash-preview": 1,
            "gemini-2.5-flash": 1,
        }
        env_config = self.google_models_limits or os.getenv("GOOGLE_MODEL_LIMITS")

        self._model_limits = {}

        if env_config:
            env_config = env_config.strip()
            # Tenta decodificar formato JSON (antigo)
            if env_config.startswith("{"):
                try:
                    self._model_limits = json.loads(env_config)
                    self.logger.info(
                        f"Configuração (JSON) carregada: {self._model_limits}"
                    )
                except json.JSONDecodeError:
                    self.logger.error("JSON inválido. Usando padrões.")
                    self._model_limits = default_limits
            # Tenta decodificar formato Simples (Novo - Portainer Safe)
            else:
                try:
                    # Ex: "gemini-3-pro=4,gemini-2.5-pro=10"
                    items = env_config.split(",")
                    for item in items:
                        if "=" in item:
                            key, value = item.split("=")
                            self._model_limits[key.strip()] = int(value.strip())
                    self.logger.info(
                        f"Configuração (Simple) carregada: {self._model_limits}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Erro ao ler config simples: {e}. Usando padrões."
                    )
                    self._model_limits = default_limits

        # Se falhou ou veio vazio, usa default
        if not self._model_limits:
            self._model_limits = default_limits

        self._models = list(self._model_limits.keys())

    def _get_prioritized_models(self, is_paid_key: bool):
        """Define a ordem dos modelos para economizar dinheiro."""

        def get_model_weight(model_name):
            m = model_name.lower()
            if "ultra" in m:
                return 100
            if "pro" in m:
                return 80
            if "flash" in m:
                return 10
            return 50

        models_copy = self._models.copy()
        if is_paid_key:
            # PAGA: Prioriza o MAIS BARATO (Flash -> Pro)
            return sorted(models_copy, key=get_model_weight, reverse=False)
        else:
            # FREE: Prioriza o MELHOR (Pro -> Flash) - "Gastar o caro de graça"
            return sorted(models_copy, key=get_model_weight, reverse=True)

    def load_keys(self):
        """Carrega chaves separando em listas Free e Paid."""
        self._free_keys = []
        self._paid_keys = []

        # 1. Carregar FREE
        _keys_free_str = self.google_free_keys or os.getenv("GOOGLE_FREE_KEYS")
        if _keys_free_str:
            keys = [k.strip() for k in _keys_free_str.split(",") if k.strip()]
            keys = list(dict.fromkeys(keys))  # Remove duplicatas

            # Nas Free, queremos usar o Pro primeiro
            models_for_free = self._get_prioritized_models(is_paid_key=False)
            for key in keys:
                self._setup_key_state(key, models_for_free)
            self._free_keys = keys

        # 2. Carregar PAGAS
        try:
            _keys_paid_str = self.google_paid_keys or os.getenv("GOOGLE_PAID_KEYS")
            if _keys_paid_str:
                keys = [k.strip() for k in _keys_paid_str.split(",") if k.strip()]
                keys = list(dict.fromkeys(keys))

                # Nas Pagas, queremos usar o Flash primeiro
                models_for_paid = self._get_prioritized_models(is_paid_key=True)
                for key in keys:
                    self._setup_key_state(key, models_for_paid)
                self._paid_keys = keys
        except Exception:
            pass

        self._all_keys_count = len(self._free_keys) + len(self._paid_keys)
        self.logger.info(
            f"Rotator iniciado: {len(self._free_keys)} Free, {len(self._paid_keys)} Paid."
        )

    def _setup_key_state(self, key, sorted_models):
        if key not in self._models_by_key:
            self._models_by_key[key] = sorted_models.copy()
            self._active_slots[key] = {model: 0 for model in self._models}
            self._suspended_until[key] = {}

    def get_total_capacity(self):
        """Retorna capacidade total para cálculo de tentativas máximas."""
        with self._lock:
            return max(1, self._all_keys_count * len(self._models))

    # --- LÓGICA DE SELEÇÃO DE SLOT (CASCATA + ROUND ROBIN) ---

    def select_and_reserve_best_slot(
        self,
        model_variant: str = None,
        forced_paid: bool = False,
        forced_free: bool = False,
    ):
        """
        Busca slot livre: 1º em Free Keys (RR), 2º em Paid Keys (RR).
        Retorna: (key, model) ou (None, None) se tudo estiver ocupado.
        """
        with self._lock:
            current_time = time.time()

            # TIER 1: Tenta Free Keys
            if not forced_paid:
                key, model = self._find_slot_in_list(
                    self._free_keys, self._free_index, current_time, model_variant
                )
                if key:
                    self._free_index = (self._free_index + 1) % len(self._free_keys)
                    return key, model, "free"

            # TIER 2: Tenta Paid Keys (Fallback)
            if not forced_free:
                key, model = self._find_slot_in_list(
                    self._paid_keys, self._paid_index, current_time, model_variant
                )
                if key:
                    self._paid_index = (self._paid_index + 1) % len(self._paid_keys)
                    return key, model, "paid"

            return None, None, None

    def _find_slot_in_list(
        self, keys_list, start_index, current_time, model_variant: str = None
    ):
        """Helper para iterar numa lista circularmente (Round-Robin)."""
        count = len(keys_list)
        if count == 0:
            return None, None

        for i in range(count):
            idx = (start_index + i) % count
            key = keys_list[idx]

            # Itera sobre os modelos dessa chave (já ordenados por prioridade/custo)
            for model in self._models_by_key[key]:
                # 0. Filtra por variante se informado
                if model_variant and model_variant.lower() not in model.lower():
                    continue

                # 1. Verifica Suspensão
                if model in self._suspended_until[key]:
                    if current_time < self._suspended_until[key][model]:
                        continue
                    else:
                        del self._suspended_until[key][model]

                # 2. Verifica Slots Livres
                limit = self._model_limits.get(model, 1)
                if self._active_slots[key][model] < limit:
                    self._active_slots[key][model] += 1
                    self.logger.info(
                        f"Slot alocado: {model} (Free? {key in self._free_keys}) - Key: {key[:10]}..."
                    )
                    return key, model

        return None, None

    def liberar_slot_model(self, key, model):
        with self._lock:
            if key in self._active_slots and model in self._active_slots[key]:
                if self._active_slots[key][model] > 0:
                    self._active_slots[key][model] -= 1
                    self.logger.info(f"Slot liberado: {model} - Key: {key[:10]}...")

    # --- Tratamento de Erro Centralizado ---

    def processar_exception(self, key, model, exception):
        error_str = str(exception)
        if self._regex_429.search(error_str):
            self._tratar_erro_429(key, model, error_str)
            return True
        if self._regex_invalid_key.search(error_str):
            self.logger.error(f"Chave inválida: {key[:10]}... Removendo.")
            self.remove_key(key)
            return True
        return False

    def _tratar_erro_429(self, key, model, error_str):
        suspension_time = 60
        if self._regex_limit_zero.search(error_str):
            suspension_time = 86400
            reason = "Limit 0"
        elif self._regex_per_day.search(error_str):
            suspension_time = self._calcular_segundos_ate_renovacao()
            reason = "Cota Diária"
        elif self._regex_per_minute.search(error_str):
            suspension_time = 120
            reason = "Cota RPM"
        else:
            reason = "429 Genérico"

        self.logger.warning(
            f"Erro 429 ({reason}). Suspendendo {model} na key {key[:10]}... por {suspension_time}s"
        )
        self.suspender_modelo(key, model, suspension_time)

    def suspender_modelo(self, key, model, segundos):
        with self._lock:
            if key not in self._models_by_key:
                return
            liberacao_em = time.time() + segundos
            if model in self._suspended_until[key]:
                if self._suspended_until[key][model] > liberacao_em:
                    return
            self._suspended_until[key][model] = liberacao_em

    def _calcular_segundos_ate_renovacao(self):
        now_utc = datetime.now(timezone.utc)
        target = now_utc.replace(hour=8, minute=0, second=0, microsecond=0)
        if now_utc >= target:
            target += timedelta(days=1)
        return int((target - now_utc).total_seconds()) + 300

    def remove_key(self, key_to_remove):
        with self._lock:
            if key_to_remove in self._free_keys:
                self._free_keys.remove(key_to_remove)
                self._all_keys_count -= 1
                return True
            if key_to_remove in self._paid_keys:
                self._paid_keys.remove(key_to_remove)
                self._all_keys_count -= 1
                return True
            return False
