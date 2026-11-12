Release Notes - v26.46.001

Abaixo estão as notas de atualização para a versão v26.46.001. Esta versão foca na evolução da infraestrutura central de inteligência artificial, reformulando o mecanismo de rotação de chaves de API para garantir maior resiliência e disponibilidade do serviço. Além disso, foram executadas as rotinas automatizadas de atualização de versão e sincronização do histórico de alteração do sistema.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **AI Core / API Key Rotator:** Refatoração abrangente no mecanismo de rotação e gerenciamento de chaves de API (`ApiKeyRotator.py`), aprimorando a lógica de chaveamento dinâmico, tratamento de limites de taxa (rate limits) e resiliência no consumo de serviços de LLM. A mudança amplia o controle de concorrência e falhas, garantindo alta disponibilidade no processamento da inteligência artificial e mitigando interrupções por exaustão ou invalidação de credenciais (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `481f41c` | Autor: @krlsedu*
* **Build & Release:** Atualização automatizada dos arquivos de controle de versão e notas de lançamento para a publicação oficial da tag v26.46.001, mantendo o rastreamento do ciclo de vida e a integridade da esteira de CI/CD (`RELEASE_NOTES.md`).
  * *Commit: `520ba99` | Autor: @krlsedu*