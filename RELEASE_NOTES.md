Aqui estão as Notas de Lançamento para a versão **v26.13.001**, focadas nas melhorias de processamento de IA e observabilidade.

---

# 📝 Release Notes - v26.13.001

## 🚀 Features

### IA & Processamento
- **Suporte a `thinking_level`:** Implementada a capacidade de configurar o nível de raciocínio (*thinking level*) no `IaProcessor`. Isso permite um controle mais refinado sobre modelos que suportam processamento em etapas ou cadeias de pensamento (Chain of Thought).

### Observabilidade e Telemetria
- **Rastreamento de Reasoning Tokens:** Adicionada a captura e persistência de *reasoning tokens* (tokens de raciocínio). 
    - Os dados agora são registrados nos logs de telemetria.
    - O schema do banco de dados **ClickHouse** foi atualizado para armazenar essas métricas, permitindo auditoria de custos e análise de performance de modelos avançados.

## 🐛 Fixes
- Nenhuma correção de bug reportada nesta versão.

## 🔧 Chore
- Atualização de infraestrutura de dados no `ClickHouseDb.py` para suporte aos novos campos de telemetria.

---
**Tech Lead:** Carlos Eduardo Duarte Schwalm  
**Commit de referência:** `84b99b8`