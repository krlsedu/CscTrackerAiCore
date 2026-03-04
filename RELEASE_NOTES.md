Aqui estão as notas de lançamento para a versão **v26.10.001**, focadas em melhorias de observabilidade e telemetria do motor de IA.

---

# 📝 Release Notes - v26.10.001

## 🚀 Features

### Observabilidade e Performance
* **Rastreamento de Tempo de Processamento:** Implementada a captura da métrica `time_spent` dentro do `IaProcessor`. Esta melhoria permite mensurar com precisão o tempo de execução das tarefas de Inteligência Artificial, facilitando a identificação de gargalos operacionais.
* **Atualização de Schema (ClickHouse):** Atualizado o esquema do banco de dados ClickHouse para suportar a persistência da nova métrica `time_spent`. Isso possibilita a criação de dashboards de performance e análise histórica de latência.

## 🐛 Fixes
* *Nenhuma correção de bug reportada nesta versão.*

## 🔧 Chore
* *Nenhuma alteração de infraestrutura ou manutenção interna nesta versão.*

---
### Detalhes Técnicos
- **Commit Base:** `5321ad0`
- **Arquivos Afetados:**
  - `csctracker_ai_core/service/ClickHouseDb.py` (Migração de Schema)
  - `csctracker_ai_core/service/IaProcessor.py` (Lógica de Telemetria)

**Tech Lead:** Carlos Eduardo Duarte Schwalm (@krlsedu)