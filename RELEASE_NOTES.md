Release Notes - v26.46.001

Abaixo estão as notas de atualização para a versão v26.46.001. Esta versão foca na melhoria da infraestrutura central de IA através de uma reformulação significativa no mecanismo de rotação de chaves de API, além de incluir atualizações nos fluxos de automação de build e versionamento da aplicação. As alterações visam garantir maior resiliência na integração com serviços de IA e manter os artefatos de release sincronizados.

## 🚀 Features
*(Nenhuma alteração desta categoria nesta versão)*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **IA Core / Rotador de Chaves:** Refatoração e expansão significativa no serviço `ApiKeyRotator`, responsável pelo gerenciamento e alternância dinâmica de chaves de API. A alteração reestrutura a lógica interna para melhorar a tolerância a falhas, otimizar a distribuição de requisições entre as chaves disponíveis e garantir a continuidade das chamadas aos serviços de inteligência artificial em caso de esgotamento de cota ou erros de autenticação (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `481f41c` | Autor: @krlsedu*
* **Automação / Release:** Atualização no arquivo de controle de versão global do projeto, incrementando o identificador do sistema para sincronizar o ambiente com a release v26.46.001 e assegurar a rastreabilidade dos builds (`version.txt`).
  * *Commit: `520ba99` | Autor: @krlsedu*
* **Documentação / Build:** Atualização das notas de lançamento e artefatos de documentação durante a execução dos gatilhos automatizados de build da versão 26.46.001 (`RELEASE_NOTES.md`).
  * *Commit: `c65119e` | Autor: @krlsedu*
* **Documentação / Build:** Ajustes finos nos registros de alterações da release acionados pelo pipeline de CI/CD para consolidação dos históricos de publicação da versão 26.46.001 (`RELEASE_NOTES.md`).
  * *Commit: `6371cdf` | Autor: @krlsedu*