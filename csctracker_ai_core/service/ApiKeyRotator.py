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

    DEFAULT_FALLBACK_MODEL_LIMIT = 20
    DEFAULT_FALLBACK_ERROR_THRESHOLD = 2
    DEFAULT_FALLBACK_COOLDOWN_SECONDS = 300

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
        google_tier_fallbacks=None,
        fallback_error_threshold: int = DEFAULT_FALLBACK_ERROR_THRESHOLD,
        fallback_cooldown_seconds: int = DEFAULT_FALLBACK_COOLDOWN_SECONDS,
    ):
        self.logger = logger
        self.google_models_limits = google_models_limits
        self.google_free_keys = google_free_keys
        self.google_paid_keys = google_paid_keys
        self.google_tier_fallbacks = google_tier_fallbacks
        self.fallback_error_threshold = max(1, int(fallback_error_threshold))
        self.fallback_cooldown_seconds = max(1, int(fallback_cooldown_seconds))

        # Estruturas de dados separadas por TIER
        self._free_keys = []
        self._paid_keys = []
        self._all_keys_count = 0

        self._models = []
        self._model_limits = {}
        self._model_tiers = {}  # {model_name: canonical_tier}
        self._tier_fallbacks = {}  # {canonical_tier: fallback_model_name}
        self._fallback_only_models = set()

        # Controle de estado
        self._active_slots = {}  # {key: {model: count}}
        self._suspended_until = {}  # {key: {model: timestamp}}
        self._models_by_key = {}  # {key: [modelos_ordenados_por_custo]}
        self._consecutive_errors = {}  # {(service_tier, model_name, canonical_tier): count}
        self._tier_fallback_until = {}  # {(service_tier, canonical_tier): timestamp}

        # Índices para Round-Robin (Balanceamento de Carga)
        self._free_index = 0
        self._paid_index = 0
        self._lock = Lock()
        self._on_key_removed_callbacks = []

        # Regex Compilados para detecção de erro
        self._regex_429 = re.compile(r"(429|RESOURCE_EXHAUSTED)", re.IGNORECASE)
        self._regex_limit_zero = re.compile(r"limit:\s*0", re.IGNORECASE)
        self._regex_per_day = re.compile(r"(PerDay|Quota.*Day)", re.IGNORECASE)
        self._regex_per_minute = re.compile(r"(PerMinute|Quota.*Minute)", re.IGNORECASE)
        self._regex_invalid_key = re.compile(
            r"(API_KEY_INVALID|key not valid|unauthorized)", re.IGNORECASE
        )

        # 1. Carregar Configuração de Modelos e Fallbacks por Tier (ENV ou Default)
        self._load_model_config()
        self._load_tier_fallbacks()

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

    def _load_tier_fallbacks(self):
        """
        Lê a ENV 'GOOGLE_TIER_FALLBACKS' (ou parâmetro google_tier_fallbacks).
        Suporta dois formatos:
        1. JSON: '{"flash": "gemini-2.5-flash", "pro": "gemini-2.5-pro"}'
        2. Simples (Portainer Friendly): 'flash=gemini-2.5-flash,pro=gemini-2.5-pro,lite=gemini-2.5-flash-lite'
        Modelos de fallback que não constam em GOOGLE_MODEL_LIMITS recebem limite padrão 20.
        """
        self._tier_fallbacks = {}
        self._fallback_only_models = set()

        env_config = self.google_tier_fallbacks
        if env_config is None:
            env_config = os.getenv("GOOGLE_TIER_FALLBACKS")

        if not env_config:
            return

        raw_fallbacks = {}
        if isinstance(env_config, dict):
            raw_fallbacks = env_config
        else:
            env_str = str(env_config).strip()
            if not env_str:
                return
            if env_str.startswith("{"):
                try:
                    parsed = json.loads(env_str)
                    if isinstance(parsed, dict):
                        raw_fallbacks = parsed
                except json.JSONDecodeError:
                    self.logger.error(
                        "JSON inválido em GOOGLE_TIER_FALLBACKS. Ignorando fallbacks por tier."
                    )
                    return
            else:
                try:
                    for item in env_str.split(","):
                        if "=" in item:
                            tier_key, model_val = item.split("=", 1)
                            raw_fallbacks[tier_key.strip()] = model_val.strip()
                except Exception as e:
                    self.logger.error(
                        f"Erro ao ler GOOGLE_TIER_FALLBACKS: {e}. Ignorando fallbacks por tier."
                    )
                    return

        for raw_tier, raw_model in raw_fallbacks.items():
            canonical_tier = self.TIER_ALIASES.get(str(raw_tier).strip().lower())
            if not canonical_tier:
                self.logger.warning(
                    f"Tier desconhecido em GOOGLE_TIER_FALLBACKS: '{raw_tier}'. Ignorando."
                )
                continue

            model_str = str(raw_model or "").strip()
            if not model_str:
                continue

            clean_model, _ = self._parse_model_key_and_tier(model_str)
            self._tier_fallbacks[canonical_tier] = clean_model

            if clean_model not in self._model_limits:
                self._model_limits[clean_model] = self.DEFAULT_FALLBACK_MODEL_LIMIT
                self._model_tiers[clean_model] = canonical_tier
                self._fallback_only_models.add(clean_model)

        if self._tier_fallbacks:
            self.logger.info(
                f"Fallbacks por tier carregados: {self._tier_fallbacks}"
            )

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
            self._active_slots[key] = {model: 0 for model in self._model_limits}
            self._suspended_until[key] = {}

    def get_total_capacity(self):
        """Retorna capacidade total para cálculo de tentativas máximas."""
        with self._lock:
            total_models = len(self._model_limits) or len(self._models)
            return max(1, self._all_keys_count * total_models)

    # --- LÓGICA DE FALLBACK POR TIER (2 ERROS CONSECUTIVOS) ---

    def get_model_tier(self, model_name: str) -> str:
        """Retorna o tier canônico ('lite', 'flash', 'pro', 'ultra') do modelo."""
        return self._model_tiers.get(model_name) or self._infer_model_tier(model_name)

    def resolve_requested_tier(self, model_variant: str = None, variant_family: str = None):
        """Resolve um alias de tier canônico a partir de variant_family ou model_variant."""
        return self._resolve_requested_tier(model_variant, variant_family)

    def get_tier_fallback(self, tier: str):
        """Retorna o nome do modelo fallback configurado para o tier canônico, ou None."""
        canonical = self.TIER_ALIASES.get((tier or "").strip().lower())
        if not canonical:
            return None
        return self._tier_fallbacks.get(canonical)

    @staticmethod
    def _normalize_service_tier(service_tier: str = "standard") -> str:
        """Normaliza service_tier para 'flex' ou 'standard'."""
        return "flex" if (service_tier or "").strip().lower() == "flex" else "standard"

    def _is_tier_fallback_active_unlocked(
        self, tier: str, current_time: float, service_tier: str = "standard"
    ) -> bool:
        """Verifica (sem lock) se o fallback de (service_tier, tier) está ativo no cooldown."""
        if not tier:
            return False
        st = self._normalize_service_tier(service_tier)
        key = (st, tier)
        if key not in self._tier_fallback_until:
            return False
        if current_time < self._tier_fallback_until[key]:
            return True
        del self._tier_fallback_until[key]
        return False

    def is_tier_fallback_active(
        self, tier: str, current_time: float = None, service_tier: str = "standard"
    ) -> bool:
        """Verifica de forma thread-safe se o fallback de (service_tier, tier) está ativo."""
        canonical = self.TIER_ALIASES.get((tier or "").strip().lower())
        if not canonical:
            return False
        with self._lock:
            now = time.time() if current_time is None else current_time
            return self._is_tier_fallback_active_unlocked(
                canonical, now, service_tier=service_tier
            )

    def registrar_sucesso_modelo(
        self, model: str, tier: str = None, service_tier: str = "standard"
    ):
        """Zera a contagem de erros consecutivos de (service_tier, model, tier) após resposta válida."""
        st = self._normalize_service_tier(service_tier)
        canonical = (
            self.TIER_ALIASES.get((tier or "").strip().lower())
            or self.get_model_tier(model)
        )
        with self._lock:
            self._consecutive_errors[(st, model, canonical)] = 0

    def registrar_erro_modelo(
        self, model: str, tier: str = None, service_tier: str = "standard"
    ):
        """
        Registra erro não-cota consecutivo para (service_tier, model, tier),
        isolando completamente o estado entre 'standard' e 'flex'.
        - Após 2 erros consecutivos no modelo principal: ativa o fallback do tier por 5 minutos para aquele service_tier.
        - Após 2 erros consecutivos no modelo fallback: desativa o fallback para alternar de volta ao principal.
        Retorna o nome do modelo fallback ativado, 'primary' ao voltar para o principal, ou None.
        """
        st = self._normalize_service_tier(service_tier)
        canonical = (
            self.TIER_ALIASES.get((tier or "").strip().lower())
            or self.get_model_tier(model)
        )
        with self._lock:
            fb_model = self._tier_fallbacks.get(canonical)
            if not fb_model:
                return None

            error_key = (st, model, canonical)
            count = self._consecutive_errors.get(error_key, 0) + 1
            self._consecutive_errors[error_key] = count

            if count < self.fallback_error_threshold:
                return None

            self._consecutive_errors[error_key] = 0
            cooldown_key = (st, canonical)

            if model == fb_model:
                self._tier_fallback_until.pop(cooldown_key, None)
                self.logger.warning(
                    f"[{st}] Fallback '{fb_model}' do tier '{canonical}' falhou {count}x seguidas. "
                    f"Alternando de volta para o modelo principal."
                )
                return "primary"

            self._tier_fallback_until[cooldown_key] = (
                time.time() + self.fallback_cooldown_seconds
            )
            self.logger.warning(
                f"[{st}] Modelo '{model}' (tier '{canonical}') falhou {count}x seguidas. "
                f"Ativando fallback '{fb_model}' por {self.fallback_cooldown_seconds}s (somente {st})."
            )
            return fb_model

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
                # Se pediu 'pro' e não há nenhum modelo 'pro' primário configurado na lista,
                # permite fallback transparente para 'ultra' (ex: carbon).
                primary_tiers = {
                    self._model_tiers.get(m) or self._infer_model_tier(m)
                    for m in self._models
                }
                if requested_tier == "pro" and "pro" not in primary_tiers:
                    return model_tier == "ultra"
                return False

        target = (variant_family or model_variant or "").strip().lower()
        if not target:
            return True

        if exact_match:
            return model_l == target
        return target in model_l

    def _try_allocate_model_on_key(self, key: str, model: str, current_time: float) -> bool:
        """Tenta reservar 1 slot para 'model' na 'key' respeitando suspensão e limite."""
        if model not in self._model_limits:
            return False

        # 1. Verifica Suspensão
        if model in self._suspended_until[key]:
            if current_time < self._suspended_until[key][model]:
                return False
            del self._suspended_until[key][model]

        # 2. Verifica Slots Livres
        limit = self._model_limits.get(model, 1)
        if self._active_slots[key].get(model, 0) < limit:
            self._active_slots[key][model] = self._active_slots[key].get(model, 0) + 1
            self.logger.info(
                f"Slot alocado: {model} (Free? {key in self._free_keys}) - Key: {key[:10]}..."
            )
            return True

        return False

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
        return self._select_and_reserve_slot(
            model_variant=model_variant,
            variant_family=variant_family,
            forced_paid=forced_paid,
            forced_free=forced_free,
            exact_match=exact_match,
            service_tier="standard",
        )

    def _select_and_reserve_slot(
        self,
        model_variant: str = None,
        variant_family: str = None,
        forced_paid: bool = False,
        forced_free: bool = False,
        exact_match: bool = False,
        service_tier: str = "standard",
    ):
        """Implementação interna de seleção de slot com isolamento de fallback por service_tier."""
        st = self._normalize_service_tier(service_tier)
        with self._lock:
            current_time = time.time()

            # TIER 1: Tenta Free Keys
            if not forced_paid:
                key, model = self._find_slot_in_list(
                    self._free_keys,
                    self._free_index,
                    current_time,
                    model_variant,
                    variant_family,
                    exact_match,
                    service_tier=st,
                )
                if key:
                    self._free_index = (self._free_index + 1) % len(self._free_keys)
                    return key, model, "free"

            # TIER 2: Tenta Paid Keys (Fallback)
            if not forced_free:
                key, model = self._find_slot_in_list(
                    self._paid_keys,
                    self._paid_index,
                    current_time,
                    model_variant,
                    variant_family,
                    exact_match,
                    service_tier=st,
                )
                if key:
                    self._paid_index = (self._paid_index + 1) % len(self._paid_keys)
                    return key, model, "paid"

            return None, None, None

    def _find_slot_in_list(
        self,
        keys_list,
        start_index,
        current_time,
        model_variant: str = None,
        variant_family: str = None,
        exact_match: bool = False,
        service_tier: str = "standard",
    ):
        """Helper para iterar numa lista circularmente (Round-Robin)."""
        count = len(keys_list)
        if count == 0:
            return None, None

        requested_tier = (
            None
            if exact_match
            else self._resolve_requested_tier(model_variant, variant_family)
        )

        # Caso 1: exact_match pode selecionar inclusive modelos registrados apenas como fallback
        if exact_match:
            target = (variant_family or model_variant or "").strip().lower()
            if target:
                for i in range(count):
                    idx = (start_index + i) % count
                    key = keys_list[idx]
                    for model in self._model_limits:
                        if model.lower() == target:
                            if self._try_allocate_model_on_key(key, model, current_time):
                                return key, model
                return None, None

        # Caso 2: Tier explícito com fallback ativo no cooldown daquele service_tier
        if requested_tier and self._is_tier_fallback_active_unlocked(
            requested_tier, current_time, service_tier=service_tier
        ):
            fb_model = self._tier_fallbacks.get(requested_tier)
            if fb_model:
                for i in range(count):
                    idx = (start_index + i) % count
                    key = keys_list[idx]
                    if self._try_allocate_model_on_key(key, fb_model, current_time):
                        return key, fb_model

        for i in range(count):
            idx = (start_index + i) % count
            key = keys_list[idx]

            # Itera sobre os modelos primários dessa chave (já ordenados por prioridade/custo)
            for model in self._models_by_key[key]:
                # 0. Filtra por variante/tier se informado
                if not self._matches_model_filter(
                    model, model_variant=model_variant, variant_family=variant_family, exact_match=exact_match
                ):
                    continue

                # Sem filtro de tier explícito (ex: model_variant=None): respeita fallback ativo do tier do modelo
                if not exact_match and not requested_tier:
                    m_tier = self.get_model_tier(model)
                    if self._is_tier_fallback_active_unlocked(
                        m_tier, current_time, service_tier=service_tier
                    ):
                        fb_model = self._tier_fallbacks.get(m_tier)
                        if fb_model and self._try_allocate_model_on_key(
                            key, fb_model, current_time
                        ):
                            return key, fb_model

                if self._try_allocate_model_on_key(key, model, current_time):
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

    def register_on_key_removed(self, callback):
        """Registra callback(key) executado quando uma chave é removida do pool."""
        if callable(callback):
            with self._lock:
                if callback not in self._on_key_removed_callbacks:
                    self._on_key_removed_callbacks.append(callback)

    def remove_key(self, key_to_remove):
        removed = False
        callbacks = []
        with self._lock:
            if key_to_remove in self._free_keys:
                self._free_keys.remove(key_to_remove)
                self._all_keys_count -= 1
                removed = True
            elif key_to_remove in self._paid_keys:
                self._paid_keys.remove(key_to_remove)
                self._all_keys_count -= 1
                removed = True
            if removed:
                callbacks = list(self._on_key_removed_callbacks)

        if removed:
            for cb in callbacks:
                try:
                    cb(key_to_remove)
                except Exception as e:
                    self.logger.warning(f"Erro em callback on_key_removed: {e}")
        return removed
