---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-20
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- Implementada a **ID 87** (`Por Publicar` — 29/29 testes unitários offline OK em `tests/test_tier_fallback.py` e `tests/test_resilience_and_telemetry.py`):
  - Suporte ao sufixo opcional `:limite` em `GOOGLE_TIER_FALLBACKS` (`pro=gemini-4-neon:15,flash=gemini-4-hydrogen:50,lite=gemini-3.5-flash-lite:500` e JSON), preservando o padrão `20` quando omitido/inválido e mantendo os modelos fallback estritamente fora da fila dos titulares (`GOOGLE_MODEL_LIMITS`).
- Release `v26.47.001` publicada no GitHub/PyPI (`bf8e523`) consolidando as **IDs 79, 80, 81 e 82** (`Em Homologação`).
- Release anterior `v26.46.002` publicada no GitHub (`f135279`) com a correção da **ID 54** (`Em Homologação`).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- *(Nenhuma tentativa falha registrada na sessão atual).*

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/CscTrackerAiCore-master.zip`).
- **Arquivos Alterados:** `csctracker_ai_core/service/ApiKeyRotator.py`, `csctracker_ai_core/service/IaProcessor.py`, `csctracker_ai_core/service/ClickHouseDb.py`, `csctracker_ai_core/service/Telemetry.py`, `tests/test_resilience_and_telemetry.py`, `tests/test_tier_fallback.py`, `README.md`, `.ai-memory/*`.

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release da biblioteca `csctracker-ai-core` (via `CscTrackerCicd`) contendo a **ID 87** e validar em homologação junto às **IDs 79, 80, 81 e 82**.
- Validar em homologação os custos históricos da rota `/ai-costs` (**ID 54**) e, após confirmação do desenvolvedor, mover `54.md` para `projects/ideias/prontas/54.md`.
