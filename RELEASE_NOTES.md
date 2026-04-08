Aqui está o Release Notes técnico para a versão **v26.15.002**, focado em clareza para a equipe de engenharia e stakeholders.

---

# 📝 Release Notes - v26.15.002

## Resumo
Esta versão foca na integridade dos dados de processamento de IA e no refinamento do motor de cálculo de custos de telemetria, garantindo que descontos de camadas de serviço específicas sejam aplicados corretamente.

---

## 🚀 Features

### Refinamento de Cálculo de Custos (Telemetry)
*   **Ajuste de Telemetria:** Atualizada a lógica de cálculo no módulo `Telemetry` para suportar e aplicar descontos nativos da camada de serviço `flex`. Isso garante uma bilhetagem mais precisa para o consumo de recursos de IA.

---

## 🐛 Fixes

### Validação de Service Tier (IaProcessor)
*   **Integridade de Dados:** Implementada a obrigatoriedade de atribuições válidas de `service_tier` dentro do `IaProcessor`. Esta alteração evita que processamentos com tiers inválidos ou nulos causem inconsistências nos fluxos de processamento de IA.

---

## 🔧 Chore

*   **Refatoração de Código:** Pequenos ajustes de tipagem e validação nos arquivos `IaProcessor.py` e `Telemetry.py` para melhor manutenibilidade.

---

### 📊 Estatísticas do Commit
- **Arquivos alterados:** 2
- **Inserções:** 6
- **Deleções:** 3
- **SHA:** `8fc7ea1`
- **Autor:** Carlos Eduardo Duarte Schwalm (krlsedu)