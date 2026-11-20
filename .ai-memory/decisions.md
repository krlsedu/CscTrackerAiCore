---
project: CscTrackerAiCore
kind: decision
tier: semantic
pinned: true
updated_at: 2026-11-20
---

# 🏛️ Decisões Arquiteturais e Cláusulas Pétreas — `CscTrackerAiCore`

> Regras específicas e invioláveis deste repositório + histórico de decisões arquiteturais (ADRs).

## 🔒 Cláusulas Pétreas e Regras Invioláveis `[PINNED]`

1. **Preservação dos Tiers Canônicos e Rotação Free/Paid (`APIKeyRotator`):**
   - Manter a resolução canônica de tiers (`lite`, `flash`, `pro`, `ultra` / tags `:tier` em `GOOGLE_MODEL_LIMITS`) e a lógica de rotação/fallback entre chaves Free e Paid em `APIKeyRotator` sem quebrar contratos consumidos por `CscTrackerIA` e `CscTrackerNotificationAI`.
2. **Vigência Temporal de Preços na Tabela `model_prices` (`Telemetry.py` — ID 54):**
   - Consultas de custo na tabela `model_prices` DEVEM usar `ASOF LEFT JOIN` (`ON e.clean_model = p.join_model AND e.timestamp >= p.timestamp`) para garantir que reajustes futuros de tarifas jamais distorçam o cálculo histórico de eventos passados em `ai_events`.
3. **Telemetria Assíncrona e Não-Bloqueante:**
   - Falhas ou latências na gravação de telemetria no ClickHouse jamais devem derrubar a resposta principal de inferência da biblioteca (`csctracker-ai-core`).

---

## 📜 Registro de Decisões (ADRs)
- **[2026-11-20] Fallback de Modelo por Tier com Cooldown Isolado por `service_tier` (ID 79):**
  - Adicionada a ENV `GOOGLE_TIER_FALLBACKS` (JSON ou `tier=modelo`, limite padrão `20` quando fora de `GOOGLE_MODEL_LIMITS` sem furar a fila primária).
  - Contadores de 2 erros consecutivos não-cota (API/5xx/timeout + `JSONDecodeError`) e cooldown de 5 minutos (`300s`) são indexados por `(service_tier, tier)` no `APIKeyRotator`, isolando completamente instabilidades do modo `flex` do modo `standard` e alternando de volta ao modelo principal caso o fallback também falhe 2x seguidas.
- **[2026-11-13] Vigência Temporal de Preços via `ASOF LEFT JOIN` em `Telemetry.py` (ID 54):**
  - Substituído o `LEFT JOIN` com `ORDER BY timestamp DESC LIMIT 1 BY model` por `ASOF LEFT JOIN`, preservando precisão histórica e futura de custos na rota `/ai-costs`.
- **[2026-11-13] Adoção de Memória Híbrida (`.ai-memory/` no Git + `projects/ai-memory/` no Drive) e `.junie/guidelines.md`:**
  - Permite continuidade imediata entre sessões do Antigravity e do JetBrains Junie após `git pull`.
