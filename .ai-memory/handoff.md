---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-20
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- Implementadas as **IDs 80, 81 e 82** (`Por Publicar` — 28/28 testes unitários offline OK em `tests/test_tier_fallback.py` e `tests/test_resilience_and_telemetry.py`):
  - **ID 80:** Pool thread-safe de `genai.Client` por `(api_key, timeout_ms)` com eviction/close ao remover chave inválida (`register_on_key_removed`) e no `close()`/`atexit`; timeout explícito via `types.HttpOptions` (`GOOGLE_TIMEOUT_STANDARD_SECONDS=300`, `GOOGLE_TIMEOUT_FLEX_SECONDS=600` e override `timeout=...`); backoff exponencial com jitter apenas em erros transitórios (`GOOGLE_RETRY_BACKOFF_BASE_SECONDS=0.5`, `GOOGLE_RETRY_BACKOFF_MAX_SECONDS=4.0`).
  - **ID 81:** Liberação antecipada e única do slot (`_release_slot_once()` antes da telemetria/JSON e em `finally:`); cliente persistente único no `ClickHouseDb` com `threading.Lock`, auto-reconexão, timeouts explícitos (`CLICKHOUSE_CONNECT_TIMEOUT=5`, `CLICKHOUSE_SEND_RECEIVE_TIMEOUT=30`) e `init_db()` consolidado em 1 conexão (fail-fast); `client.close()` garantido em `finally:` no `Telemetry.py`.
  - **ID 82:** Telemetria assíncrona não-bloqueante via `queue.Queue` com teto de eventos (`CLICKHOUSE_QUEUE_MAXSIZE=10000`) e teto de RAM (`CLICKHOUSE_QUEUE_MAX_MB=500`), worker daemon `ClickHouseTelemetryWorker` com batching híbrido (`CLICKHOUSE_BATCH_SIZE=20` ou `CLICKHOUSE_FLUSH_INTERVAL_SECONDS=5.0`), 1 retry com reconexão, `flush()`/`close()` + `atexit` e kill-switch `CLICKHOUSE_ASYNC_TELEMETRY=false`.
- **ID 79** também está `Por Publicar` na mesma branch `master`.
- Release anterior `v26.46.002` publicada no GitHub (`f135279`) com a correção da **ID 54** (`Em Homologação`).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- *(Nenhuma tentativa falha registrada na sessão atual).*

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/CscTrackerAiCore-master.zip`).
- **Arquivos Alterados:** `csctracker_ai_core/service/ApiKeyRotator.py`, `csctracker_ai_core/service/IaProcessor.py`, `csctracker_ai_core/service/ClickHouseDb.py`, `csctracker_ai_core/service/Telemetry.py`, `tests/test_resilience_and_telemetry.py`, `tests/test_tier_fallback.py`, `README.md`, `.ai-memory/*`.

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release da biblioteca `csctracker-ai-core` (via `CscTrackerCicd`) contendo as **IDs 79, 80, 81 e 82** e validar em homologação nos serviços consumidores.
- Validar em homologação os custos históricos da rota `/ai-costs` (**ID 54**) e, após confirmação do desenvolvedor, mover `54.md` para `projects/ideias/prontas/54.md`.
