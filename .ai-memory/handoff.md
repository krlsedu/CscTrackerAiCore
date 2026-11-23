---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-23
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução estrita de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- **[2026-11-23] Implementada a ID 97 (`Por Publicar` — 36/36 testes unitários offline OK + `python -m build` OK em Python `3.15.2`):**
  - Removido import privado quebrado `from google.genai._interactions.types import thinking_level` em `csctracker_ai_core/service/IaProcessor.py` (`ModuleNotFoundError` no `google-genai 3.6.1`).
  - Atualizado `requirements.txt` para `csctracker-py-core>=26.47.3`, `clickhouse-connect>=1.13.0,<2` e `google-genai>=3.6.0,<4` (removido `protobuf==6.33.5`, sem uso direto).
  - Atualizados `setup.py` (`python_requires=">=3.11"`, classifiers `3.11`–`3.15`), `setup.cfg` (`description_file = README.md`), criado `MANIFEST.in`, modernizado `.github/workflows/build.yml` (Python `3.15` + `unittest` + `python -m build`) e atualizado `README.md`.
- **[2026-11-22] Release `v26.47.003` publicada (`dae0a0b` / `26.47.3`, `Em Homologação`)** com a **ID 99** (trava anti-escalonamento de tier, tetos anti-loop `GOOGLE_MAX_NON_QUOTA_ERRORS`/`GOOGLE_MAX_NO_SLOT_RETRIES` e telemetria resiliente contra `None`/*poison pill*).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Na `v26.47.001` (em `CscTrackerIA v26.47.001`), o fallback `lite=gemini-3.5-flash-lite` entrou com `DEFAULT_FALLBACK_MODEL_LIMIT=20` (caindo de 500 para 20 slots), somado à ausência de telemetria de falhas/timeouts, risco de *poison pill* no batch do ClickHouse e brecha de escalonamento em `model_variant=None`/`""`. Tudo corrigido na ID 99.

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/`).
- **Testes e Build offline:** `python -B -m unittest discover -s tests -v` (`36/36` passando em `0.781s`) e `python -m build` OK em Python `3.15.2`.

## 4. Próximos Passos / Pendências Abertas
- Disparar nova release/tag (`v26.47.004` / `26.47.4`) no GitHub/PyPI contendo a **ID 97** (Python `3.15` + `csctracker-py-core>=26.47.3` + `google-genai>=3.6` + `clickhouse-connect>=1.13`).
- Validar em homologação os custos históricos da rota `/ai-costs` (**ID 54**) e atacar evoluções futuras (**IDs 83, 84, 85**).
