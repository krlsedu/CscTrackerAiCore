---
project: CscTrackerAiCore
kind: decision
tier: semantic
pinned: true
updated_at: 2026-11-22
---

# 🏛️ Decisões Arquiteturais e Cláusulas Pétreas — `CscTrackerAiCore`

> Regras específicas e invioláveis deste repositório + histórico de decisões arquiteturais (ADRs).

## 🔒 Cláusulas Pétreas e Regras Invioláveis `[PINNED]`

1. **Preservação dos Tiers Canônicos, Proibição Absoluta de Escalonamento de Tier e Rotação Free/Paid (`APIKeyRotator`):**
   - Manter a resolução canônica de tiers (`lite`, `flash`, `pro`, `ultra` / tags `:tier` em `GOOGLE_MODEL_LIMITS`, incluindo `neon -> pro`) e a lógica de rotação/fallback entre chaves Free e Paid em `APIKeyRotator` sem quebrar contratos consumidos por `CscTrackerIA` e `CscTrackerNotificationAI`.
   - **Proibição de Escalonamento Silencioso (ID 99):** Em hipótese alguma escalar `lite → flash`, `flash → pro` ou `pro → ultra` (nem com `model_variant=None`/`""` em chaves pagas, nem via `GOOGLE_TIER_FALLBACKS`) sem autorização expressa (`allow_tier_escalation=True`). Em indisponibilidade do tier solicitado, retornar erro (`GeminiServiceException`).
2. **Vigência Temporal de Preços na Tabela `model_prices` (`Telemetry.py` — ID 54):**
   - Consultas de custo na tabela `model_prices` DEVEM usar `ASOF LEFT JOIN` (`ON e.clean_model = p.join_model AND e.timestamp >= p.timestamp`) para garantir que reajustes futuros de tarifas jamais distorçam o cálculo histórico de eventos passados em `ai_events`.
3. **Telemetria Assíncrona, Não-Bloqueante e Sem Pontos Cegos (IDs 82 e 99):**
   - Falhas ou latências na gravação de telemetria no ClickHouse jamais devem derrubar a resposta principal de inferência da biblioteca (`csctracker-ai-core`), mas **toda** tentativa enviada ao Gemini (sucesso, erro ou timeout) deve ser registrada em `ai_events`, com sanitização contra `None` e fallback unitário contra *poison pill* em lotes.

---

## 📜 Registro de Decisões (ADRs)
- **[2026-11-22] Blindagem Anti-Escalonamento, Teto Anti-Loop e Telemetria Resiliente (ID 99):**
  - Introduzida hierarquia `TIER_RANK` com `allow_tier_escalation=False` (default) e trava dupla em `APIKeyRotator` e `IaProcessor`, mapeamento `"neon" -> "pro"` (peso `83`), rejeição de fallbacks para tier superior, trava de `model_variant=None`/`""` no menor tier titular em chaves pagas e prioridade Free → Paid no fallback ativo.
  - Adicionados tetos rígidos `GOOGLE_MAX_NON_QUOTA_ERRORS` (default `4`) e `GOOGLE_MAX_NO_SLOT_RETRIES` (default `5`), removida palavra genérica `"unauthorized"` de `_regex_invalid_key`, blindada leitura de `usage_metadata`/`response.text`/`modality` contra `None`, adicionado log de falhas/timeouts em `ai_events` e fallback linha a linha em `ClickHouseDb._insert_batch_with_retry()`.
- **[2026-11-20] Pool de `genai.Client`, Timeout Explícito, Backoff Transitório, Conexão Persistente e Telemetria Assíncrona em Lote (IDs 80, 81 e 82):**
  - `IaProcessor` reutiliza `genai.Client` por `(api_key, timeout_ms)` com `HttpOptions(timeout=...)` (`300s` standard / `600s` flex / override `timeout`), fecha clientes ao remover chaves inválidas ou no `close()`/`atexit`, aplica backoff exponencial com jitter somente em erros transitórios (nunca em `429` ou `JSONDecodeError`) e libera o slot antes da telemetria/JSON com guarda contra *double-release*.
  - `ClickHouseDb` consolida `init_db()` em 1 conexão persistente protegida por `threading.Lock` com auto-reconexão e timeouts configuráveis (`5s`/`30s`), enfileira eventos de telemetria de forma não-bloqueante em `queue.Queue` (limites de 10.000 eventos / 500 MB) com worker daemon `ClickHouseTelemetryWorker` gravando em batches (`20` eventos ou `5.0s`), 1 retry com reconexão, `flush()`/`close()` gracioso e kill-switch `CLICKHOUSE_ASYNC_TELEMETRY=false`; `Telemetry.py` garante `client.close()` em `finally:`.
- **[2026-11-20] Fallback de Modelo por Tier com Cooldown Isolado por `service_tier` (ID 79):**
  - Adicionada a ENV `GOOGLE_TIER_FALLBACKS` (JSON ou `tier=modelo`, limite padrão `20` quando fora de `GOOGLE_MODEL_LIMITS` sem furar a fila primária).
  - Contadores de 2 erros consecutivos não-cota (API/5xx/timeout + `JSONDecodeError`) e cooldown de 5 minutos (`300s`) são indexados por `(service_tier, tier)` no `APIKeyRotator`, isolando completamente instabilidades do modo `flex` do modo `standard` e alternando de volta ao modelo principal caso o fallback também falhe 2x seguidas.
- **[2026-11-13] Vigência Temporal de Preços via `ASOF LEFT JOIN` em `Telemetry.py` (ID 54):**
  - Substituído o `LEFT JOIN` com `ORDER BY timestamp DESC LIMIT 1 BY model` por `ASOF LEFT JOIN`, preservando precisão histórica e futura de custos na rota `/ai-costs`.
- **[2026-11-13] Adoção de Memória Híbrida (`.ai-memory/` no Git + `projects/ai-memory/` no Drive) e `.junie/guidelines.md`:**
  - Permite continuidade imediata entre sessões do Antigravity e do JetBrains Junie após `git pull`.
