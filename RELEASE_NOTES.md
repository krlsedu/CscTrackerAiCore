Release Notes - v26.48.002

Abaixo estão as notas de atualização para a versão v26.48.002. Esta versão introduz um mecanismo essencial de controle de acesso baseado em lista de usuários permitidos (`allowed_users`) no fluxo de processamento de inteligência artificial, garantindo maior governança e segurança na execução de operações. Além disso, realiza a atualização da dependência do pacote interno central da plataforma, assegurando compatibilidade com as melhorias mais recentes do ecossistema.

## 🚀 Features
* **IaProcessor / Controle de Acesso:** Implementada a validação de permissão de execução baseada no parâmetro `allowed_users` dentro do fluxo de processamento de IA, acompanhada da cobertura completa de testes unitários e atualização das instruções operacionais de skills e memórias de contexto. A alteração atende à necessidade de restringir o acionamento de processamentos e ferramentas a identidades autorizadas, mitigando riscos de execuções indevidas e garantindo conformidade nas chamadas automatizadas (`csctracker_ai_core/service/IaProcessor.py`).
  * *Commit: `f0676c4` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
* **Dependências / Core:** Atualizada a versão da biblioteca compartilhada `csctracker-py-core` para a versão `26.48.1` nos arquivos de manifesto de requisitos e na documentação do projeto. Esta manutenção técnica visa incorporar correções, aprimoramentos de compatibilidade e manter a consistência de dependências internas utilizadas pelo serviço (`requirements.txt`).
  * *Commit: `25216dc` | Autor: @krlsedu*