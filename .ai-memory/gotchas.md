---
project: CscTrackerAiCore
kind: gotcha
tier: semantic
pinned: true
updated_at: 2026-11-13
---

# ⚠️ Gotchas e Armadilhas Conhecidas — `CscTrackerAiCore`

> Registre aqui bugs sutis, limitações de biblioteca/SO e abordagens que falharam para que nenhum agente repita o mesmo erro no futuro. Use `[PINNED]` para regras permanentes e `[EXPIRES: AAAA-MM-DD]` para alertas temporários.

- `[PINNED]` Consultar sempre `projects/AI_specs/CscTrackerAiCore.md` e `spark.md` antes de alterar fluxos críticos, preservando estritamente as assinaturas públicas de `IaProcessor.analisar_com_gemini()` e `APIKeyRotator.select_and_reserve_best_slot()`.
- `[PINNED]` Nunca utilizar `LIMIT 1 BY model` estático ao cruzar `ai_events` com `model_prices` no ClickHouse; manter sempre `ASOF LEFT JOIN` com `e.timestamp >= p.timestamp` para preservar a vigência temporal dos preços (ID 54).
