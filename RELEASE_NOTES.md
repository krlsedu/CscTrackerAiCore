Release Notes - v26.47.001

Abaixo estão as notas de atualização para a versão v26.47.001. Esta versão foca no aumento da robustez, observabilidade e tolerância a falhas na camada de integração com modelos de inteligência artificial. Foram implementados pools de chaves dedicados com fallback automático por tiers de modelo e mecanismos avançados de telemetria e persistência no ClickHouse.

## 🚀 Features
* **IaProcessor & Telemetry:** Implementação de pool de recursos dedicado para o Gemini, integração avançada com ClickHouseDb para armazenamento de métricas operacionais e aprimoramento na camada de resiliência e telemetria de chamadas de IA. A alteração visa viabilizar a rastreabilidade em tempo real de latência, consumo e falhas, aumentando a confiabilidade na ingestão de dados e suportando uma cobertura extensiva de testes de estresse e resiliência (`csctracker_ai_core/service/ClickHouseDb.py`).
  * *Commit: `12f3b6d` | Autor: @krlsedu*
* **ApiKeyRotator & IaProcessor:** Introdução de estratégia de degradação graciosa com fallback dinâmico entre tiers de modelos após a ocorrência de duas falhas consecutivas, aliada ao rodízio de chaves de API. Essa abordagem mitiga indisponibilidades e esgotamento de cotas em provedores de LLM, redirecionando as requisições de forma transparente para modelos de contingência sem interrupção do processamento (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `d84e789` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*