Release Notes - v26.47.003

Abaixo estão as notas de atualização para a versão v26.47.003. Esta versão introduz melhorias substanciais de resiliência e estabilidade arquitetural no núcleo de processamento de inteligência artificial, blindando as transições entre tiers de modelos e prevenindo loops infinitos em fluxos de fallback. Além disso, a telemetria operacional via ClickHouse foi aprimorada com novas validações estruturais, cobertura de testes automatizados e integração de notificações de CI/CD via GitHub Actions.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **Resiliência e Telemetria (AI Core):** Implementação de mecanismos de proteção contra loops cíclicos de fallback e aprimoramento da estratégia de rotação de credenciais (`ApiKeyRotator`), assegurando que falhas em provedores de IA acionem a degradação graciosa para tiers secundários sem interrupções operacionais. Foi refinada a ingestão de telemetria no `ClickHouseDb` para garantir rastreabilidade detalhada dos consumos e execuções, além de implementada nova suíte de testes de estresse/resiliência (`test_resilience_and_telemetry.py` e `test_tier_fallback.py`), workflow de notificação de CI/CD (`notify-cicd.yml`) e atualização abrangente das documentações de arquitetura e skills (`csctracker_ai_core/service/IaProcessor.py`).
  * *Commit: `61998f4` | Autor: @krlsedu*