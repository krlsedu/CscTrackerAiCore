Release Notes - v26.46.002

Abaixo estão as notas de atualização para a versão v26.46.002. Esta versão implementa o controle de vigência temporal na precificação do serviço de Telemetria, garantindo maior precisão contábil e conformidade no cálculo de custos operacionais com base no período de consumo. Além disso, a documentação interna, memórias técnicas e diretrizes de agentes de IA foram amplamente atualizadas para suportar e padronizar as novas regras arquiteturais do sistema.

## 🚀 Features
* **Telemetria e Custos:** Implementação da lógica de vigência temporal de preços no serviço de telemetria, permitindo que a contabilização e faturamento do consumo de recursos considerem tabelas de preços indexadas por período de validade (`csctracker_ai_core/service/Telemetry.py`). A alteração foi motivada pela necessidade de refletir reajustes e variações históricas de tarifas sem distorcer registros passados ou futuros. Como impacto prático, o sistema ganha maior fidelidade financeira e rastreabilidade nos relatórios de custos de telemetria, acompanhado da atualização das diretrizes de arquitetura e documentações de IA para suportar o novo fluxo.
  * *Commit: `14468ad` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*