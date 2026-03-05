Aqui estão as Notas de Lançamento para a versão **v26.10.010**, focadas na melhoria da integridade de dados e processamento temporal do motor de IA.

---

# 📝 Release Notes - v26.10.010

## 🐛 Fixes

*   **Telemetry Service:** Refinamento do motor de processamento de datas (`date parsing`) para garantir maior consistência e precisão analítica.
    *   **Priorização ISO:** O sistema agora prioriza o formato ISO para evitar ambiguidades em entradas internacionais.
    *   **Gestão de Time Zones:** Implementado tratamento robusto de fusos horários, mitigando erros de conversão em ambientes distribuídos.
    *   **Ajuste de Datas Finais:** Correção na lógica de inputs que contêm apenas a data (sem hora), garantindo que o limite final do período seja ajustado corretamente para cobrir o intervalo total do dia.

## 🚀 Features
*   *Nenhuma nova funcionalidade nesta versão.*

## 🔧 Chore
*   *Nenhuma alteração de infraestrutura ou dependências nesta versão.*

---
**Tech Lead Note:** 
Esta atualização é crítica para a confiabilidade dos relatórios de telemetria. A normalização do parsing de datas no `csctracker_ai_core` previne discrepâncias em filtros temporais e garante que a agregação de dados reflita com precisão o comportamento do sistema em diferentes regiões.