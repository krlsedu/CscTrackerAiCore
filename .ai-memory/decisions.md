---
project: CscTrackerAiCore
kind: decision
tier: semantic
updated_at: 2026-11-13
---

# 🏛️ Decisões Arquiteturais Recentes (ADRs) — `CscTrackerAiCore`

> Registre aqui decisões técnicas tomadas neste repositório, a data, o contexto e o motivo de termos escolhido o caminho X em vez do caminho Y.

- **[2026-11-13] Vigência Temporal de Preços via `ASOF LEFT JOIN` em `Telemetry.py` (ID 54):**
  - Substituído o `LEFT JOIN` com `ORDER BY timestamp DESC LIMIT 1 BY model` por `ASOF LEFT JOIN` (`ON e.clean_model = p.join_model AND e.timestamp >= p.timestamp`), garantindo que cada evento em `ai_events` utilize o preço vigente na data/hora do evento sem distorcer o passado quando reajustes futuros forem cadastrados em `model_prices`.
- **[2026-11-13] Adoção de Memória Híbrida (`.ai-memory/` no Git + `projects/ai-memory/` no Drive) e `.junie/guidelines.md`:**
  - Permite continuidade imediata entre sessões do Antigravity e do JetBrains Junie após `git pull`.
