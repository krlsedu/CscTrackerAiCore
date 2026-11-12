Release Notes - v26.46.001

Abaixo estão as notas de atualização para a versão v26.46.001. Esta versão foca na otimização e endurecimento da infraestrutura do gerenciador de chaves de API do módulo de inteligência artificial. A reformulação do componente melhora a resiliência e a eficiência na rotação de credenciais, garantindo maior estabilidade no consumo de serviços externos de IA.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **IA Core / Autenticação:** Refatoração estrutural abrangente no utilitário `ApiKeyRotator`, aprimorando a lógica de chaveamento e controle de estado do ciclo de vida das chaves de API. A mudança foi motivada pela necessidade de mitigar falhas de taxa limite (*rate limit*) e otimizar o tempo de resposta do serviço através de uma estratégia de alternância de credenciais mais eficiente, eliminando gargalos de concorrência e garantindo alta disponibilidade nas requisições aos provedores de IA. (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `481f41c` | Autor: @krlsedu*