---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-20
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- Implementada a **ID 79** (`Por Publicar` — 13/13 testes unitários offline OK em `tests/test_tier_fallback.py`):
  - Suporte à ENV `GOOGLE_TIER_FALLBACKS` (formatos simples e JSON + parâmetro `google_tier_fallbacks` no construtor de `APIKeyRotator` e `IaProcessor`), com limite padrão de `20` slots quando ausente de `GOOGLE_MODEL_LIMITS` (sem furar a fila primária).
  - Contagem thread-safe de erros consecutivos não-cota (exceções de API/5xx/timeout e `JSONDecodeError`) e ativação do modelo fallback do tier após 2 erros seguidos com cooldown de 5 minutos (`300s`) **isolado por `(service_tier, tier)`** (`flex` e `standard` completamente independentes) e alternância de volta ao principal caso o fallback falhe 2x seguidas.
  - Documentação atualizada em `README.md` e `projects/AI_specs/CscTrackerAiCore.md`.
- Release anterior `v26.46.002` publicada no GitHub (`f135279`) com a correção da **ID 54** (`Em Homologação`).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- *(Nenhuma tentativa falha registrada na sessão atual).*

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/CscTrackerAiCore-master.zip`).
- **Arquivos Alterados:** `csctracker_ai_core/service/ApiKeyRotator.py`, `csctracker_ai_core/service/IaProcessor.py`, `tests/test_tier_fallback.py`, `README.md`, `.ai-memory/*`.

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release da biblioteca `csctracker-ai-core` (via `CscTrackerCicd`) contendo a **ID 79** e validar em homologação nos serviços consumidores configurando `GOOGLE_TIER_FALLBACKS`.
- Validar em homologação os custos históricos da rota `/ai-costs` (**ID 54**) e, após confirmação do desenvolvedor, mover `54.md` para `projects/ideias/prontas/54.md`.
