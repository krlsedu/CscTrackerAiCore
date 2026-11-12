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

    CANONICAL_TIERS = ("lite", "flash", "pro", "ultra")

    TIER_ALIASES = {
        "lite": "lite",
        "flash-lite": "lite",
        "flash_lite": "lite",
        "flash": "flash",
        "pro": "pro",
        "ultra": "ultra",
    }

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
        self._model_tiers = {}  # {model_name: canonical_tier}

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

    @classmethod
    def _infer_model_tier(cls, model_name: str) -> str:
        """
        Infere o tier canônico ('lite', 'flash', 'pro', 'ultra') pelo nome do modelo,
        incluindo a nomenclatura de elementos químicos da família Gemini 4:
        - carbon   -> ultra (Frontier #1 / Google AI Ultra)
        - argon    -> pro   (Frontier Reasoning / Google AI Pro)
        - hydrogen -> flash (Fast Agentic / Next-Gen Flash)
        - helium / flash-lite / lite -> lite
        """
        m = (model_name or "").lower()
        if "ultra" in m or "carbon" in m:
            return "ultra"
        if "pro" in m or "argon" in m:
            return "pro"
        if "flash-lite" in m or "lite" in m or "helium" in m:
            return "lite"
        if "flash" in m or "hydrogen" in m:
            return "flash"
        return "flash"

    def _parse_model_key_and_tier(self, raw_key: str):
        """
        Extrai o nome limpo do modelo e o tier opcional caso configurado como 'modelo:tier'.
        Ex: 'gemini-4-carbon:ultra' -> ('gemini-4-carbon', 'ultra')
            'gemini-4-argon'        -> ('gemini-4-argon', 'pro')
        """
        cleaned = raw_key.strip()
        explicit_tier = None
        if ":" in cleaned:
            parts = cleaned.rsplit(":", 1)
            candidate_tier = parts[1].strip().lower()
            if candidate_tier in self.TIER_ALIASES:
                cleaned = parts[0].strip()
                explicit_tier = self.TIER_ALIASES[candidate_tier]
        tier = explicit_tier or self._infer_model_tier(cleaned)
        return cleaned, tier

    def _load_model_config(self):
        """
        Lê a ENV 'GOOGLE_MODEL_LIMITS'.
        Suporta dois formatos (com tag opcional ':tier' por modelo):
        1. JSON: '{"model": 1}' ou '{"gemini-4-carbon:ultra": 2}'
        2. Simples (Portainer Friendly): 'model=1,model2=10' ou 'gemini-4-argon:pro=2,gemini-4-hydrogen:flash=5'
        """
        default_limits = {
            "gemini-3-flash-preview": 1,
            "gemini-2.5-flash": 1,
        }
        env_config = self.google_models_limits or os.getenv("GOOGLE_MODEL_LIMITS")

        raw_limits = {}

        if env_config:
            env_config = env_config.strip()
            # Tenta decodificar formato JSON (antigo)
            if env_config.startswith("{"):
                try:
                    raw_limits = json.loads(env_config)
                    self.logger.info(
                        f"Configuração (JSON) carregada: {raw_limits}"
                    )
                except json.JSONDecodeError:
                    self.logger.error("JSON inválido. Usando padrões.")
                    raw_limits = default_limits
            # Tenta decodificar formato Simples (Novo - Portainer Safe)
            else:
                try:
                    # Ex: "gemini-4-carbon:ultra=2,gemini-4-argon:pro=4,gemini-4-hydrogen:flash=10"
                    items = env_config.split(",")
                    for item in items:
                        if "=" in item:
                            key, value = item.split("=", 1)
                            raw_limits[key.strip()] = int(value.strip())
                    self.logger.info(
                        f"Configuração (Simple) carregada: {raw_limits}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Erro ao ler config simples: {e}. Usando padrões."
                    )
                    raw_limits = default_limits

        # Se falhou ou veio vazio, usa default
        if not raw_limits:
            raw_limits = default_limits

        self._model_limits = {}
        self._model_tiers = {}
        for raw_key, limit_val in raw_limits.items():
            model_name, tier = self._parse_model_key_and_tier(raw_key)
            self._model_limits[model_name] = int(limit_val)
            self._model_tiers[model_name] = tier

        self._models = list(self._model_limits.keys())

    def _get_model_weight(self, model_name: str) -> int:
        """
        Retorna o peso de custo/capacidade do modelo para ordenação:
        lite (5) < flash (10) < hydrogen (15) < pro (80) < argon (85) < ultra (100) < carbon (105).
        Respeita override explícito de tier em GOOGLE_MODEL_LIMITS.
        """
        m = model_name.lower()
        tier = self._model_tiers.get(model_name) or self._infer_model_tier(model_name)

        if tier == "ultra":
            return 105 if "carbon" in m else 100
        if tier == "pro":
            if "carbon" in m:
                return 90
            return 85 if "argon" in m else 80
        if tier == "lite":
            return 5
        if tier == "flash":
            return 15 if "hydrogen" in m else 10
        return 50

    def _get_prioritized_models(self, is_paid_key: bool):
        """Define a ordem dos modelos para economizar dinheiro."""
        models_copy = self._models.copy()
        if is_paid_key:
            # PAGA: Prioriza o MAIS BARATO (Lite -> Flash/Hydrogen -> Pro/Argon -> Ultra/Carbon)
            return sorted(models_copy, key=self._get_model_weight, reverse=False)
        else:
            # FREE: Prioriza o MELHOR (Ultra/Carbon -> Pro/Argon -> Flash/Hydrogen -> Lite) - "Gastar o caro de graça"
            return sorted(models_copy, key=self._get_model_weight, reverse=True)

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

    def _resolve_requested_tier(self, model_variant: str = None, variant_family: str = None):
        """
        Se variant_family ou model_variant for um alias de tier ('lite', 'flash-lite',
        'flash', 'pro', 'ultra'), retorna o tier canônico correspondente.
        Caso contrário, retorna None (para busca por nome/substring específico, ex: 'argon', 'carbon').
        """
        raw = (variant_family or model_variant or "").strip().lower()
        if not raw:
            return None
        return self.TIER_ALIASES.get(raw)

    def _matches_model_filter(
        self,
        model: str,
        model_variant: str = None,
        variant_family: str = None,
        exact_match: bool = False,
    ) -> bool:
        """
        Verifica se 'model' atende ao filtro solicitado por tier canônico ou por substring/exact_match.
        """
        model_l = model.lower()
        model_tier = self._model_tiers.get(model) or self._infer_model_tier(model)

        if not exact_match:
            requested_tier = self._resolve_requested_tier(model_variant, variant_family)
            if requested_tier:
                if model_tier == requested_tier:
                    return True
                # Se pediu 'pro' e não há nenhum modelo 'pro' configurado na lista,
                # permite fallback transparente para 'ultra' (ex: carbon).
                if requested_tier == "pro" and "pro" not in self._model_tiers.values():
                    return model_tier == "ultra"
                return False

        target = (variant_family or model_variant or "").strip().lower()
        if not target:
            return True

        if exact_match:
            return model_l == target
        return target in model_l

    def select_and_reserve_best_slot(
        self,
        model_variant: str = None,
        variant_family: str = None,
        forced_paid: bool = False,
        forced_free: bool = False,
        exact_match: bool = False,
    ):
        """
        Busca slot livre: 1º em Free Keys (RR), 2º em Paid Keys (RR).
        Retorna: (key, model) ou (None, None) se tudo estiver ocupado.

        Parâmetros:
        - model_variant: quando informado, filtra o modelo a ser alocado.
          Aceita tanto tiers canônicos ("lite", "flash-lite", "flash", "pro", "ultra")
          quanto nomes/substrings de modelos ("carbon", "argon", "hydrogen", "gemini-4-argon").
        - variant_family: atalho sem versão. Aceita "ultra", "pro", "flash", "lite"/"flash-lite".
          Regras:
            * ultra -> modelos de tier ultra ("ultra", "carbon" ou tag ':ultra')
            * pro   -> modelos de tier pro ("pro", "argon" ou tag ':pro')
            * lite  -> modelos de tier lite ("flash-lite", "lite", "helium" ou tag ':lite')
            * flash -> modelos de tier flash ("flash" exceto lite, "hydrogen" ou tag ':flash')
          Quando informado, tem precedência sobre model_variant.
        - exact_match: se True, exige correspondência exata do nome do modelo
          (case-insensitive). Útil para restringir, por ex., somente
          "...flash-lite" sem pegar variantes que também contém "flash".
        """
        with self._lock:
            current_time = time.time()

            # TIER 1: Tenta Free Keys
            if not forced_paid:
                key, model = self._find_slot_in_list(
                    self._free_keys, self._free_index, current_time, model_variant, variant_family, exact_match
                )
                if key:
                    self._free_index = (self._free_index + 1) % len(self._free_keys)
                    return key, model, "free"

            # TIER 2: Tenta Paid Keys (Fallback)
            if not forced_free:
                key, model = self._find_slot_in_list(
                    self._paid_keys, self._paid_index, current_time, model_variant, variant_family, exact_match
                )
                if key:
                    self._paid_index = (self._paid_index + 1) % len(self._paid_keys)
                    return key, model, "paid"

            return None, None, None

    def _find_slot_in_list(
        self, keys_list, start_index, current_time, model_variant: str = None, variant_family: str = None, exact_match: bool = False
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
                # 0. Filtra por variante/tier se informado
                if not self._matches_model_filter(
                    model, model_variant=model_variant, variant_family=variant_family, exact_match=exact_match
                ):
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
