---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-13
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- Aplicada em `csctracker_ai_core/service/Telemetry.py` a correção da **ID 54**: substituição do `LEFT JOIN` estático (`LIMIT 1 BY model`) por `ASOF LEFT JOIN` na tabela `model_prices` (`ON e.clean_model = p.join_model AND e.timestamp >= p.timestamp`), respeitando a vigência temporal histórica e futura dos preços por modelo.
- Auto-provisionados e sincronizados no repositório `.agents/skills/csctracker/SKILL.md` (com Diretriz 3.18), `.ai-memory/` e `.junie/guidelines.md`.

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- *(Nenhuma tentativa falha registrada na sessão atual).*

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/`).
- **Arquivos Alterados:** `csctracker_ai_core/service/Telemetry.py`, `.agents/skills/csctracker/SKILL.md`, `.ai-memory/*`, `.junie/guidelines.md`.

## 4. Próximos Passos / Pendências Abertas
- Validar em homologação os custos históricos da rota `/ai-costs` e, após confirmação do desenvolvedor, mover `54.md` para `projects/ideias/prontas/54.md`.
