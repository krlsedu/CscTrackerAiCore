Aqui está o Release Notes técnico para a versão **v26.15.005**, focado em clareza e impacto técnico.

---

# 📦 Release Notes - v26.15.005

## Resumo
Esta versão foca no refinamento da camada de telemetria do core de IA, trazendo maior precisão e legibilidade ao cálculo de custos para tiers de serviço específicos.

---

## 🐛 Fixes
*   **Telemetry Service:** Ajustada a lógica de cálculo de custos no módulo de telemetria. A alteração visa eliminar ambiguidades no processamento de métricas para o tier de serviço `flex`, garantindo que o faturamento ou reporte de consumo reflita corretamente as regras de negócio da camada.

## 🔧 Chore
*   **Refatoração de Código:** Melhoria na legibilidade e manutenção do arquivo `Telemetry.py` dentro do `csctracker_ai_core`.

---

### 🛠 Detalhes Técnicos (Diff Summary)
- **Arquivo modificado:** `csctracker_ai_core/service/Telemetry.py`
- **Impacto:** 2 inserções e 1 deleção.
- **Commit ID:** `8e0765a`

---
*Documentação gerada automaticamente com base no histórico de commits.*