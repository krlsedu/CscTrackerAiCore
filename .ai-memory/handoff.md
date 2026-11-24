---
project: CscTrackerAiCore
kind: handoff
tier: working
updated_at: 2026-11-24
---

# 🤝 Handoff Ativo — `CscTrackerAiCore`

> **Escopo do Projeto:** Biblioteca central Python (`csctracker-ai-core`): rotação Free/Paid (`APIKeyRotator`), resolução estrita de tiers (`lite`, `flash`, `pro`, `ultra`) e telemetria no ClickHouse.

## 1. Onde Paramos / Contexto Atual (`WIP`)
- **[2026-11-24] Implementação da Task #109 (`Por Publicar` — 42/42 testes offline OK em Python `3.15`):**
  - Adicionado parâmetro opcional `allowed_users=None` em `IaProcessor.__init__` e criada `UnauthorizedUserException(GeminiServiceException)` (`status_code = 403`) em `csctracker_ai_core/service/IaProcessor.py`.
  - Quando `allowed_users` está preenchido e o e-mail resolvido via `RequestInfo.get_user_email()` não está na lista, bloqueia acesso a `GOOGLE_PAID_KEYS` forçando `forced_free=True` e lança `UnauthorizedUserException` (`403`) se `forced_paid=True` ou se não houver chave/slot `FREE` disponível.
  - Adicionados 6 testes offline em `tests/test_allowed_users.py` (`42/42` passando) e sincronizada `.agents/skills/csctracker/SKILL.md`.
- **[2026-11-23] ID 97 publicada no PyPI (`v26.48.001` / `csctracker-ai-core==26.48.1`, status `Em Homologação`):**
  - Workflow `Build` (`run 45279328892`) verde em `ubuntu-latest` / Python `3.15.2` (54s): `36/36` testes OK, `python -m build` OK e upload PyPI OK (`requires_python >=3.11`).
- **[2026-11-22] Release `v26.47.003` (`dae0a0b` / `26.47.3`):** **ID 99** (trava anti-escalonamento de tier, tetos anti-loop e telemetria resiliente).

## 2. Tentativas Descartadas / O que Falhou (`Failed Approaches`)
- Na `v26.47.001` (em `CscTrackerIA v26.47.001`), o fallback `lite=gemini-3.5-flash-lite` entrou com `DEFAULT_FALLBACK_MODEL_LIMIT=20` (caindo de 500 para 20 slots), somado à ausência de telemetria de falhas/timeouts, risco de *poison pill* no batch do ClickHouse e brecha de escalonamento em `model_variant=None`/`""`. Tudo corrigido na ID 99.

## 3. Estado dos Arquivos / Branch / Build
- **Fonte Primária:** GitHub (`master`, com espelho `.zip` em `projects/repositorys/CscTrackerAiCore/`).
- **Testes:** `42/42` passando em Python `3.15` (`0.741s`).

## 4. Próximos Passos / Pendências Abertas
- Publicar nova release de `csctracker-py-core` (com `RequestInfo.get_user_email()`) e em seguida nova release de `csctracker-ai-core` no PyPI para liberar a **Task #109** no `CscTrackerIA`.
- Atacar evoluções futuras (**IDs 83, 84, 85**).
