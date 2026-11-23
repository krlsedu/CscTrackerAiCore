---
project: CscTrackerAiCore
kind: gotcha
tier: semantic
pinned: true
updated_at: 2026-11-22
---

# ⚠️ Gotchas e Armadilhas Conhecidas — `CscTrackerAiCore`

> Registre aqui bugs sutis, limitações de biblioteca/SO e abordagens que falharam para que nenhum agente repita o mesmo erro no futuro. Use `[PINNED]` para regras permanentes e `[EXPIRES: AAAA-MM-DD]` para alertas temporários.

- `[PINNED]` Consultar sempre `projects/AI_specs/CscTrackerAiCore.md` e `spark.md` antes de alterar fluxos críticos, preservando estritamente as assinaturas públicas de `IaProcessor.analisar_com_gemini()` e `APIKeyRotator.select_and_reserve_best_slot()`.
- `[PINNED]` Nunca utilizar `LIMIT 1 BY model` estático ao cruzar `ai_events` com `model_prices` no ClickHouse; manter sempre `ASOF LEFT JOIN` com `e.timestamp >= p.timestamp` para preservar a vigência temporal dos preços (ID 54).
- `[PINNED]` Em `ClickHouseDb`, todas as colunas de `ai_events` (`UInt32`/`String`/`Float`) são não-`Nullable`: nunca enviar `None` no batch (causa *poison pill* descartando o lote inteiro) e manter o fallback linha a linha em `_insert_batch_with_retry()` (ID 99).
- `[PINNED]` Em `IaProcessor`, `response.usage_metadata.candidates_token_count` e `response.text` podem vir `None` em modelos *thinking* (ex.: Gemini 4 Neon/Argon): sempre normalizar `or 0` / `or ""` antes de somar ou chamar `json.loads()`, e gravar telemetria de erro/timeout no ClickHouse (ID 99).
- `[PINNED]` Nunca importar módulos privados do SDK Google GenAI (ex.: `google.genai._interactions.types`, removido no `google-genai>=3.6`) e manter `MANIFEST.in` (`version.py`, `version.txt`, `requirements.txt`, `README.md`, `LICENSE`) para que `python -m build` empacote o wheel a partir do sdist sem `ModuleNotFoundError: No module named 'version'` (ID 97).
