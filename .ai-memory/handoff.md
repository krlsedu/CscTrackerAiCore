---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-22
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução estrita de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- Implementada a **ID 99** (`Por Publicar` — 36/36 testes unitários offline OK em `tests/test_tier_fallback.py` e `tests/test_resilience_and_telemetry.py`):
  - **Trava anti-escalonamento de tier (`allow_tier_escalation=False` por padrão):** proibido sair de `lite → flash`, `flash → pro` ou `pro → ultra` sem autorização expressa; `model_variant=None`/`""` em chave paga travado no menor tier titular; `_load_tier_fallbacks()` rejeita fallbacks para tier superior; `"neon"` mapeado para `"pro"` (peso `83`); trava dupla em `ApiKeyRotator` e `IaProcessor`; prioridade Free → Paid no fallback ativo; removido `"unauthorized"` genérico de `_regex_invalid_key`.
  - **Teto anti-loop:** `GOOGLE_MAX_NON_QUOTA_ERRORS` (default `4`) e `GOOGLE_MAX_NO_SLOT_RETRIES` (default `5`).
  - **Telemetria blindada no ClickHouse:** proteção contra `None`/exceções em `usage_metadata`, `item.modality` e `response.text`; registro de falhas/timeouts em `ai_events` (`ERROR [Tipo]: ...`); sanitização contra `None` em `_build_telemetry_row()` e fallback linha a linha contra *poison pill* em `_insert_batch_with_retry()`.
- Release `v26.47.002` publicada no GitHub (`605c5dd`) com a **ID 87** (sufixo `:limite` em `GOOGLE_TIER_FALLBACKS`).
- Release `v26.47.001` publicada no GitHub/PyPI (`bf8e523`) com as **IDs 79, 80, 81 e 82**.

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Na `v26.47.001` (em `CscTrackerIA v26.47.001`), o fallback `lite=gemini-3.5-flash-lite` entrou com `DEFAULT_FALLBACK_MODEL_LIMIT=20` (caindo de 500 para 20 slots), somado à ausência de telemetria de falhas/timeouts, risco de *poison pill* no batch do ClickHouse e brecha de escalonamento em `model_variant=None`/`""`. Tudo corrigido na ID 99.

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/CscTrackerAiCore-master.zip`).
- **Arquivos Alterados:** `csctracker_ai_core/service/ApiKeyRotator.py`, `csctracker_ai_core/service/IaProcessor.py`, `csctracker_ai_core/service/ClickHouseDb.py`, `tests/test_tier_fallback.py`, `tests/test_resilience_and_telemetry.py`, `README.md`, `.agents/skills/csctracker/SKILL.md`, `.github/workflows/notify-cicd.yml`, `.ai-memory/*`.

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release (`v26.47.003` via `CscTrackerCicd`) da biblioteca `csctracker-ai-core` contendo a **ID 99** + **ID 87**.
- Atualizar `CscTrackerIA` para consumir a nova versão do `csctracker-ai-core` (junto à blindagem de `/analyze` — ID 100) e configurar `:limite` no compose (`lite=gemini-3.5-flash-lite:500`).
- Validar em homologação os custos históricos da rota `/ai-costs` (**ID 54**).
