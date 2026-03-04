Aqui estão as Notas de Lançamento (Release Notes) para a versão **v26.10.002**, elaboradas com foco técnico e clareza para a equipe de engenharia.

---

# 📝 Release Notes - v26.10.002

## Resumo
Esta versão foca na expansão das capacidades de observabilidade e métricas do motor de IA, introduzindo novos campos de rastreamento temporal no banco de dados analítico ClickHouse.

---

## 🚀 Features

*   **Expansão do Schema de Eventos de IA:** Adição da coluna `time_spent` à tabela `ai_events` no ClickHouse. 
    *   *Impacto:* Permite a mensuração precisa do tempo de processamento de cada evento de IA, facilitando a criação de dashboards de performance e identificação de gargalos.
    *   *Resiliência:* A migração foi implementada com tratamento de erros robusto para garantir a integridade do schema durante o processo de atualização.

## 🐛 Fixes
*   Nenhuma correção de bug reportada nesta versão.

## 🔧 Chore
*   Manutenção preventiva no módulo `ClickHouseDb.py` para suporte a evoluções de schema dinâmicas.

---

### 🛠 Detalhes Técnicos
*   **Commit:** `bc65cb1`
*   **Módulo Afetado:** `csctracker_ai_core/service/ClickHouseDb.py`
*   **Autor:** Carlos Eduardo Duarte Schwalm (krlsedu)

---
*Tech Lead: @krlsedu*