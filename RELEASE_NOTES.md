Aqui está o Release Notes técnico para a versão **v26.15.003**, estruturado conforme solicitado:

---

# 📦 Release Notes - v26.15.003

## 📝 Resumo
Esta versão foca na estabilidade da camada de persistência, corrigindo uma regressão crítica no esquema de banco de dados ClickHouse que impedia a atualização correta da estrutura de serviços.

---

## 🐛 Fixes

- **Database Schema:** Corrigido erro de sintaxe no script de atualização do `ClickHouseDb`. O ajuste foi aplicado especificamente na definição da coluna `service_tier`, garantindo a integridade do esquema durante a migração ou inicialização do banco.
    - *Arquivo afetado:* `csctracker_ai_core/service/ClickHouseDb.py`

---

## 🚀 Features
*Nenhuma nova funcionalidade foi introduzida nesta versão.*

---

## 🔧 Chore
*Nenhuma alteração de infraestrutura, dependências ou refatoração foi realizada nesta versão.*

---

**Informações de Build:**
- **Commit:** `d8c0e9a`
- **Autor:** Carlos Eduardo Duarte Schwalm (krlsedu)
- **Data:** 2026