Aqui está o Release Notes técnico para a versão **v26.15.006**, focado em clareza e impacto técnico.

---

# 📦 Release Notes - v26.15.006

## Resumo
Esta versão foca na refatoração e simplificação da lógica de atribuição de camadas de serviço (`service_tier`) dentro do processador de IA, eliminando redundâncias de código legado.

---

## 🔧 Chore
- **Refatoração do `IaProcessor`**: Remoção de lógica redundante para tratamento do tier `free`. A atribuição de `service_tier` foi simplificada para garantir um fluxo de dados mais direto e menos propenso a erros de estado.
    - *Arquivo afetado:* `csctracker_ai_core/service/IaProcessor.py`

---

## 🛠 Detalhes Técnicos (Internal)
- **Commit:** `ea7bb34`
- **Impacto:** Baixo. A alteração limpa o código técnico sem alterar a regra de negócio final, otimizando a manutenção do componente core de IA.
- **Remoções:** 3 linhas de código redundante.

---
**Tech Lead:** Carlos Eduardo Duarte Schwalm (krlsedu)
**Data:** 2026