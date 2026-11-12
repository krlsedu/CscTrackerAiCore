Release Notes - v26.46.001

Abaixo estão as notas de atualização para a versão v26.46.001. Esta versão foca na melhoria da resiliência e estabilidade da infraestrutura de IA através de uma reformulação significativa no serviço de rotação de chaves de API. Além disso, foram executadas as atualizações operacionais de versão e artefatos de documentação para suporte ao fluxo de integração e deployment contínuo.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **IA Core / Rotação de Chaves:** Reformulação completa no mecanismo de rotação de credenciais (`ApiKeyRotator.py`), aprimorando o tratamento de falhas, alternância de chaves expiradas ou limitadas por quota e garantindo maior disponibilidade nas chamadas aos serviços de inteligência artificial (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `481f41c` | Autor: @krlsedu*
* **Release & Versionamento:** Atualização do arquivo de versionamento do sistema (`version.txt`) para a tag oficial `v26.46.001`, alinhando os artefatos da aplicação para a esteira de deployment (`version.txt`).
  * *Commit: `520ba99` | Autor: @krlsedu*
* **Documentação de Release:** Atualização e estruturação dos registros históricos de alterações no documento `RELEASE_NOTES.md` para inclusão dos detalhes do build `26.46.001` (`RELEASE_NOTES.md`).
  * *Commit: `c65119e` | Autor: @krlsedu*