---
project: CscTrackerAiCore
kind: session_log
tier: episodic
updated_at: 2026-11-20
---

# 📜 Changelog de Sessões Recentes — `CscTrackerAiCore`

> Mantém o resumo enxuto das últimas 5 a 10 sessões deste projeto. Sessões mais antigas são rotacionadas para `projects/ai-memory/arquivo_sessoes/AAAA-MM.md`.

- **[2026-11-20]** Implementação das IDs 80, 81 e 82 (pool de `genai.Client` por `(key, timeout_ms)`, timeouts explícitos `300s`/`600s` + override, backoff exponencial com jitter apenas em erros transitórios, liberação antecipada de slot sem *double-release*, `ClickHouseDb` com cliente persistente/auto-reconexão/boot em 1 conexão e telemetria assíncrona em fila com batching + teto de RAM/eventos + `flush()`/`close()`, `finally: client.close()` no `Telemetry.py`, 28/28 testes offline OK e atualização do `README.md`).
- **[2026-11-20]** Refinamento e implementação da ID 79 (`GOOGLE_TIER_FALLBACKS` com fallback por tier após 2 erros consecutivos não-cota, limite padrão `20`, cooldown de 5 min isolado por `service_tier` `flex`/`standard`, alternância em falha do fallback, 13/13 testes unitários offline e atualização do `README.md`).
- **[2026-11-13]** Implementação da ID 54 (`ASOF LEFT JOIN` para vigência temporal de preços em `model_prices` no `Telemetry.py`) e auto-provisionamento de `.agents/skills/csctracker/SKILL.md`, `.ai-memory/` e `.junie/guidelines.md`.
- **[2026-11-13]** Inicialização da estrutura `ai-memory` v1.0 para `CscTrackerAiCore`.
