---
name: csctracker
description: Execute ALWAYS whenever interacting with the CscTracker ecosystem (CscTrackerAndroid, CscTrackerVigilante, CscTrackerNotificationAI, CscTrackerMqtt, CscTrackerBackend, CscTrackerRepository, CscTrackerAiCore, CscTrackerIA, CscTrackerCicd, CscTrackerWhatsConversation, CscTrackerFFExtension) or when asked to analyze code, diagnose issues, or create patches/prompts for CscTracker projects. Enforces the canonical reading chain of projects/README.md -> spark.md -> <Project>.md -> projects/ideias/ -> projects/ai-memory/, pure Markdown/YAML file storage with absolute prohibition of Google Docs format, GitHub-first source resolution with Drive ZIP sync in projects/repositorys/, clean UI guidelines, direct codebase modification followed by mutual review and commit/push in Antigravity (generating .patch only on explicit request or inside web Gemini chats), standardized PT-BR commit messages (<=50 chars imperative subject + blank line + 2-3 sentence explanation), non-blocking git push with dynamic branch resolution and zero-force push tolerance, absolute fidelity over sanitization (never decide removals unilaterally), Gradle-only build control, the Markdown/CSV backlog lifecycle in projects/ideias/, continuous ai-memory lifecycle (Recall -> Checkpoint -> Consolidate -> Handoff), and automatic provisioning/versioning of .agents/skills/csctracker/SKILL.md, .ai-memory/, and .junie/guidelines.md in every CscTracker repository.
---
# CscTracker Governance and Execution Protocol

## Summary
Protocolo mestre de governança, ingestão de especificações, cláusulas pétreas de engenharia, ciclo de vida do backlog em `projects/ideias/`, memória contínua de longo e curto prazo (`projects/ai-memory/` no Drive + `.ai-memory/` no Git + `.junie/guidelines.md` para o JetBrains Junie), proibição estrita e absoluta de salvar arquivos como Google Docs (devem ser sempre arquivos de texto puro `.md` / `.yml` / `.csv`), resolução híbrida de código-fonte (GitHub-first com espelhamento de backup `.zip` em `projects/repositorys/` no Google Drive no Handoff), prioridade de alteração direta no código seguida de revisão conjunta e commit/push no Antigravity com padrão canônico de mensagens de commit em PT-BR (<=50 caracteres no imperativo + linha em branco + 2 a 3 frases explicativas), execução segura e não-bloqueante de push (`GIT_TERMINAL_PROMPT=0` e proibição de force push), reserva de patches `.patch` apenas sob solicitação expressa do desenvolvedor ou em chats web do Gemini, geração de prompts densos apenas quando delegado a agentes externos (Android Studio / Junie), e auto-provisionamento de `.agents/skills/csctracker/SKILL.md`, `.ai-memory/` e `.junie/guidelines.md` em todos os repositórios do ecossistema CscTracker.

## When to Use
- Qualquer menção a projetos do CscTracker: `CscTrackerAndroid`, `CscTrackerVigilante`, `CscTrackerNotificationAI`, `CscTrackerMqtt`, `CscTrackerBackend`, `CscTrackerRepository`, `CscTrackerAiCore`, `CscTrackerIA`, `CscTrackerCicd`, `CscTrackerWhatsConversation`, `CscTrackerFFExtension`.
- Ao analisar logs, investigar falhas, desenhar arquiteturas, gerenciar o backlog de Ideias, consultar/atualizar a `ai-memory` ou aplicar melhorias/correções diretamente no código para o desenvolvedor (Carlos Schwalm).

## 1. Pipeline de Ingestão Canônica (Ordem Obrigatória de Leitura)
Antes de responder qualquer pergunta técnica, analisar código ou formular alterações/patches/prompts, o assistente DEVE seguir esta sequência:
1. `projects/README.md`: Compreensão da malha do ecossistema, mapeamento de diretórios e roteamento.
2. `projects/AI_specs/spark.md`: Governança geral do assistente, princípios KISS, Clean UI, formato de respostas, fidelidade absoluta e gestão de Ideias.
3. `projects/AI_specs/<NomeDoProjeto>.md`: Especificação técnica do projeto com diretivas específicas de bloqueio e imutabilidade daquele repositório.
4. Diretório `projects/ideias/`: Fonte primária local do backlog:
   - `projects/ideias/ideias.csv`: Índice consolidado (`id,nome,status`).
   - `projects/ideias/<ID>.md`: Demandas e bugs pendentes/ativos.
   - `projects/ideias/prontas/<ID>.md`: Demandas concluídas/implementadas.
   - `projects/ideias/monetizar/<ID>.md`: Demandas de monetização/SaaS.
5. Diretório `projects/ai-memory/` (ID no Drive: `1noA7dlsUx4GfaytEZaczaZeOk_r_9p8v`) e `.ai-memory/` do repositório (`Recall` obrigatório):
   - `projects/ai-memory/00_INDEX.md`, `WIP_GLOBAL.md`, `INBOX_INTEGRACOES.md` e `GLOBAL_ECOSSISTEMA.md` (mais `gotchas_globais.md` quando envolver infra/deploy).
   - `.ai-memory/handoff.md`, `.ai-memory/gotchas.md` e `.ai-memory/decisions.md` do projeto alvo (ou o espelho em `projects/ai-memory/projects/<NomeDoProjeto>/`).

## 2. Separação de Responsabilidades dos Documentos
- `spark.md`: Define como o **Spark (assistente)** deve se comportar. Nunca armazena regras exclusivas de um único repositório.
- `AI_specs/<Projeto>.md`: Define como o **código do projeto** deve se comportar e quais partes são intocáveis (ex: no Android, imutabilidade de canais, sons, agrupamento por tríade, descarte por acessibilidade e fidelidade de desarquivamento; no Repository, auto-recuperação de conexões).
- `ai-memory/` (`.ai-memory/`): Guarda a **memória viva episódica, semântica e de trabalho** (onde paramos na última sessão, tentativas que falharam para não repetir erros, armadilhas descobertas em produção, decisões arquiteturais recentes e avisos cruzados de integração entre projetos).

## 3. Diretriz 3.13 — Fidelidade Absoluta Prevalece sobre Limpeza e Sanitização (Mandatória)
- **REGRA DE OURO:** Priorize SEMPRE fidelidade absoluta ao código, composes e configurações fornecidas pelo desenvolvedor, em detrimento de qualquer ímpeto de "limpeza", "simplificação" ou "organização" autônoma.
- **PROIBIÇÃO DE DECISÃO UNILATERAL:** É terminantemente proibido remover, omitir ou alterar flags de infraestrutura (como `external: true`, nomes físicos de volumes, portas, networks, aliases, variáveis de ambiente ou configs do compose) sem validação prévia.
- **PROTOCOLO DE CONSULTA OBRIGATÓRIA:** Caso o assistente identifique qualquer elemento potencialmente sanitizável, redundante, obsoleto ou passível de otimização, o assistente **DEVE OBRIGATORIAMENTE APONTAR E PERGUNTAR** ao desenvolvedor, apresentando a observação para decisão consciente do usuário. NUNCA tome decisões de sanitização por conta própria.

## 4. Diretriz 3.9 — Design Limpo de UI e Anti-Poluição Visual
- A interface móvel deve ser minimalista e elegante.
- Proibição de detalhes de infraestrutura na UI (rotas de BFF, portas, nomes de microsserviços internos, parênteses redundantes como "(CFTV & IA)").
- Nomes limpos e diretos (ex: "Vigilante").
- Se houver dúvida sobre nomenclatura ou rótulos, **pergunte obrigatoriamente ao desenvolvedor**.

## 5. Diretriz 3.5, 3.10 e 3.8 — Regra de Entrega: Alteração Direta ➔ Revisão Conjunta ➔ Commit/Push (Antigravity), Padrão de Commit e Cláusulas Pétreas
- **1. Fluxo Padrão no Antigravity (IDE / CLI / Remote Agents — PRIORIDADE MÁXIMA):**
  - No ambiente Antigravity, o assistente possui acesso direto ao sistema de arquivos e ferramentas de execução (`write_to_file`, `replace_file_content`, `run_command`). Portanto, **NÃO** deve emitir blocos de `.patch` na resposta do chat por padrão.
  - O ciclo de entrega padrão e obrigatório é:
    1. **Alteração Direta:** O assistente aplica as alterações cirúrgicas ou melhorias diretamente nos arquivos de código-fonte do repositório.
    2. **Revisão Conjunta:** O assistente apresenta ao desenvolvedor (Carlos Schwalm) um resumo claro, objetivo e contextualizado dos arquivos tocados e do rationale das alterações para validação e alinhamento mútuo.
    3. **Commit & Push:** Após a revisão/validação conjunta (ou aprovação do usuário), executar o `git commit` seguindo rigorosamente o **Padrão Canônico de Mensagens de Commit (Seção 5.2)** e o **Protocolo de Push Seguro (Seção 5.3)** no repositório do GitHub (além de sincronizar o espelho `.zip` em `projects/repositorys/<Projeto>/` e atualizar a `ai-memory`).
- **2. Padrão Canônico de Mensagens de Commit (Obrigatório em Todo o Ecossistema CscTracker):**
  - Todas as mensagens de commit geradas pelo assistente ou sugeridas ao desenvolvedor DEVEM seguir estritamente as seguintes regras:
    1. **Língua:** Obrigatoriamente em português (PT-BR).
    2. **Sem Prolixidade:** Evitar descrições prolixas, listas desnecessárias de arquivos ou detalhes redundantes.
    3. **Primeira Linha (Assunto):**
       - Deve ser exatamente **uma única frase** no modo imperativo (ex.: `Atualiza...`, `Corrige...`, `Adiciona...`, `Remove...`, `Refatora...`).
       - Limite estrito de comprimento: **no máximo 50 caracteres**.
    4. **Linha em Branco:** Uma linha vazia obrigatória separando a primeira linha do corpo.
    5. **Corpo (Explicação Detalhada):**
       - Composto por **no máximo duas ou três frases**.
       - Focado diretamente no que foi feito e na justificativa técnica/funcional.
    - **Template canônico:**
      ```git
      <Ação no imperativo com no máximo 50 caracteres>

      <Primeira frase contextualizando a alteração e impacto principal. Segunda frase com detalhes técnicos ou exceções relevantes. Terceira frase opcional de fechamento se estritamente necessário.>
      ```
- **3. Protocolo de Execução Segura de Git Push e Tolerância a Falhas de Prompt/Credenciais:**
  - **Execução Não-Bloqueante:** O assistente DEVE executar o comando de push configurando o terminal para não bloquear aguardando prompts interativos de credenciais (`GIT_TERMINAL_PROMPT=0` ou flags não-interativas), evitando que a sessão trave indefinidamente.
  - **Identificação Dinâmica da Branch:** NUNCA chumbar `master` ou `main` cegamente. O assistente deve identificar a branch ativa via `git branch --show-current` e realizar o push para ela:
    ```bash
    git push origin HEAD
    # ou
    git push origin $(git branch --show-current)
    ```
  - **Proibição Absoluta de Force Push:** É expressamente proibido usar `git push --force` ou `-f` em qualquer repositório CscTracker, a menos que o desenvolvedor solicite expressamente com todas as letras.
  - **Conduta em Caso de Falha de Push (Falta de Credencial / Prompt Abortado / Divergência):**
    1. O assistente certifica que o commit local foi concluído com sucesso e permanece seguro no histórico (`git log -1`);
    2. Jamais tentar injetar tokens, alterar arquivos sensíveis (`.gitconfig`, `.ssh`) ou rodar comandos interativos de login;
    3. Informar ao desenvolvedor o motivo da recusa do push e fornecer o comando exato pronto para colar no terminal local autenticado dele (onde o Git Credential Manager ou chaves SSH já estão configuradas):
       ```powershell
       git push origin <branch-correta>
       ```
    4. Anotar o status `[COMMIT_LOCAL_OK - PUSH_PENDENTE: <branch>]` em `.ai-memory/handoff.md` para preservar o contexto.
- **4. Exceção Estrita para Geração de Patch Unificado (`.patch` / `diff`):**
  - O assistente DEVE gerar e entregar o bloco de `.patch` no formato IntelliJ/Git diretamente no corpo da resposta do chat **SOMENTE** em duas situações:
    a) **Quando o desenvolvedor pedir expressamente:** (ex.: *"me dê o patch"*, *"gere o diff"*, *"manda em patch"*); OU
    b) **Dentro dos chats web do Google Gemini:** Onde o assistente opera sem acesso a ferramentas locais de edição direta no sistema de arquivos.
  - Ao gerar `.patch`, manter estrita validação (sem tocar em `build_number.properties`).
- **5. Alterações Muito Grandes e Complexas / Agentes Externos (VIA PROMPT DE IMPLEMENTAÇÃO):**
  - Caso uma demanda seja muito ampla ou o desenvolvedor decida delegá-la expressamente a agentes externos (Android Studio ou JetBrains Junie), seguir os formatos direcionados:
  - **Android (Agente do Google no Android Studio):**
    - Prompt altamente explicativo, verboso e detalhista nas regras de negócio e fluxos, com código enxuto (apenas pequenos snippets cirúrgicos de exemplo, sem classes inteiras ou XMLs completos).
    - **Inclusão Obrigatória das 9 Cláusulas Pétreas de Imutabilidade (`CscTrackerAndroid.md` Seção 3.8)** (que também devem ser rigorosamente respeitadas pelo assistente em qualquer alteração direta ou patch):
      1. **Imutabilidade Absoluta de Canais e Sons (Diretriz 3.1):** Proibido criar, recriar ou alterar `NotificationChannel` ou manipular sons/vibrações via builder.
      2. **Bloqueio Estrito de Roteamento (Diretriz 3.1):** Proibido alterar `getChannelId` ou mapeamento de severidade.
      3. **Imutabilidade de Agrupamento por Tríade (Diretriz 3.7):** Agrupamento estrito por `App + Conversa + Importância` (`csc_grp_<app>_<chat>_<importance>`), atribuição incondicional de `.setGroup(contactGroupKey)`, summary apenas com `childCount >= 2` com identidade do app de origem, e isolamento da persistente (`csc_grp_persistent_service`).
      4. **Preservação Visual e Emojis Canônicos (Diretriz 3.2):** Exclusivamente círculos coloridos (🔴 `CRITICAL`, 🟡 `IMPORTANT`, 🔵 `NORMAL`, 🟢 `LOW`, ⚪ `IRRELEVANT`, ❓ contingência).
      5. **Preservação de Banco e Histórico Insert-Only (Diretriz 3.1 / ID 36):** Respeito à tabela `notification_history` do SQLite sem `db.update` bloqueante.
      6. **Protocolo de Violação (Diretriz 3.1 / 3.7):** Apontar expressamente em destaque qualquer diretiva violada antes de propor código ou patch.
      7. **Controle Exclusivo de Build pelo Gradle (Diretriz 3.12 / 3.15):** Proibido tocar ou instruir alteração em `build_number.properties`.
      8. **Cláusula Pétrea de Descarte por Acessibilidade e Metadados Canônicos (Diretriz 3.11 / ID 10):** Isolamento estrito do motor de comunicadores (Strategy) e preservação obrigatória dos `repostExtras` (`csc_orig_pkg`, `csc_orig_app`, `csc_orig_sender`, `csc_orig_text`, `csc_orig_is_chat`, `csc_orig_uuid`, `csc_orig_sbn_key`, `csc_chat_key`, `csc_orig_importance`) e da whitelist `NotificationSettings.autoRemoveApps`.
      9. **Fidelidade Integral no Desarquivamento de Transbordo (Diretriz 3.5 / ID 45):** Notificações restauradas do `OverflowManager` (`checkAndPerformBackfillPop`) jamais podem voltar com aparência genérica, duplicar prefixo `"Remetente: "` no texto ou perder o destino original abrindo a `NotificationsActivity` do CscTracker; devem preservar o snapshot visual completo (`archivedNotification`), ações nativas (`RemoteInput`), `repostExtras` e o `contentIntent` / `launchIntent` do app de origem.
  - **Python / Backend (JetBrains Junie — tokens pagos):**
    - Iniciar obrigatoriamente com: *"Economize tokens de pensamento, seja direto, rápido e siga rigorosamente o princípio KISS."*
    - Fornecer código pré-pronto completo e verbatim para economizar tokens e tempo de processamento do Junie.

## 6. Diretriz 3.11 e 3.14 — Governança e Ciclo de Vida do Backlog em `projects/ideias/`
- **Estrutura Canônica em `projects/ideias/`:**
  - `projects/ideias/<ID>.md`: Demandas pendentes/ativas.
  - `projects/ideias/prontas/<ID>.md`: Demandas concluídas (movidas da raiz `ideias/` para `ideias/prontas/` ao concluir).
  - `projects/ideias/monetizar/<ID>.md`: Demandas da trilha de monetização/SaaS.
  - `projects/ideias/ideias.csv`: Índice mestre (`id,nome,status`) sempre atualizado a cada criação ou mudança de status.
- **Captura Preventiva em Rascunho (Diretriz 3.14):** Ideias exploratórias nascem como `Rascunho` até confirmação expressa do desenvolvedor (`Nova` ➔ `Em refinamento` ➔ `Em Andamento` ➔ `Em homologação` ➔ `Concluída`). Sempre varrer `projects/ideias/` por similaridade e perguntar antes de fundir ou criar duplicatas.
- **Fechamento Automático de Ideias no Handoff:** Ao concluir a entrega de uma demanda que resolve uma Ideia ativa, o assistente DEVE perguntar proativamente ao desenvolvedor se a demanda pode ser movida para `projects/ideias/prontas/<ID>.md` com a atualização correspondente de status no `ideias.csv`.
- **Sincronia Bidirecional:** Manter sincronizados os arquivos em `projects/ideias/`, o `ideias.csv` e a seção "4. Matriz de Priorização e Mapeamento de Ideias" nos MDs de cada projeto (`AI_specs/<Projeto>.md`).

## 7. Diretriz 3.12 — Gestão Híbrida de Fontes (GitHub vs. `projects/repositorys/`), Sincronismo de `.zip` e Ciclo de Entregas
- **1. Leitura / Obtenção do Código-Fonte (Prioridade GitHub-First):**
  - **Com acesso ao GitHub (`git` / `gh` ativos):** O assistente DEVE obter/clonar o código diretamente do **GitHub** (ignorando o `.zip` da pasta `projects/repositorys/<Projeto>/` na leitura inicial, pois a pasta `repositorys/` serve como espelho/backup para o chat do Gemini).
  - **Sem acesso ao GitHub (ex.: chat do Gemini Web ou ambiente sem plugin GitHub):** O assistente DEVE buscar e descompactar o `.zip` do projeto localizado em `projects/repositorys/<Projeto>/` no Google Drive (ID da pasta `repositorys`: `1M8fP4RiZoXYwlgkDJB-JXHm9qnB_e0Qe`).
- **2. Fechamento e Sincronização ao Concluir Alterações (Cadência Otimizada):**
  - **No GitHub (Imediato):** O `git commit` e `git push` ocorrem imediatamente após a revisão conjunta a cada alteração aprovada.
  - **No Google Drive (Backup `.zip` no Handoff):** Para evitar esperas desnecessárias de compactação/upload em cada micro-commit, a compactação do código atualizado (sem pastas de ambiente/build como `.git/`, `.gradle/`, `build/`, `.venv/`, `__pycache__/`) e o envio/atualização do arquivo `.zip` dentro de `projects/repositorys/<Projeto>/` no Drive são executados preferencialmente no **fechamento da sessão ou conclusão da demanda (`Handoff`)**.
  - **Caso NÃO tenha acesso ao GitHub:** Atualizar diretamente o `.zip` no Drive e fornecer `.patch` quando solicitado.
- **3. Consulta Obrigatória na Dúvida:** Em caso de dúvida sobre a paridade do código com a build atual em execução (especialmente quando houver alterações locais ainda não commitadas pelo desenvolvedor), **perguntar obrigatoriamente ao desenvolvedor**: *"O código atual (GitHub/Drive) está alinhado com a sua build em execução ou houve novos ajustes locais?"*

## 8. Diretriz 3.15 — Controle Exclusivo do Número de Build pelo Gradle (Proibição de Manipulação Manual)
- **Controle 100% Automático via Gradle:** No CscTrackerAndroid, o `build_number` e o `versionName` são calculados e incrementados automaticamente pelo script do Gradle (`calculateVersionName()` em `app/build.gradle`), persistindo em `build_number.properties` a cada compilação da IDE.
- **Proibição Estrita:** É terminantemente proibido instruir o desenvolvedor ou o agente da IDE a alterar manualmente o arquivo `build_number.properties`, incluir incrementos de `build_number` em commits/prompts/patches ou tentar gerenciá-lo manualmente. O assistente NUNCA deve tocar nem mandar alterar `build_number.properties`.

## 9. Diretriz 3.16 — Auto-Provisionamento e Versionamento nos Repositórios (`.agents/skills/csctracker/SKILL.md`, `.ai-memory/` e `.junie/guidelines.md`)
- **Verificação Automática em Todos os Projetos CscTracker:** Sempre que interagir com qualquer repositório do ecossistema CscTracker, o assistente DEVE verificar se os 3 itens abaixo existem e estão atualizados na raiz do repositório:
  1. `.agents/skills/csctracker/SKILL.md`: Cópia fiel de `projects/SKILL.md` do Google Drive (ID: `1zccc1imMWMiobP4iY0KOmds97OLTUaNW` — ou de `~/.gemini/skills/csctracker/SKILL.md`).
  2. `.ai-memory/` (`handoff.md`, `gotchas.md`, `decisions.md`, `changelog_sessoes.md`): Memória viva daquele projeto, sincronizada com `projects/ai-memory/projects/<Projeto>/` no Google Drive (ID da pasta `ai-memory/projects`: `1iNcywMpN7MHjQ45iTL1EKGaVkUTyOQvH`).
  3. `.junie/guidelines.md`: Arquivo de instruções automáticas para o **JetBrains Junie** (baseado em `projects/ai-memory/TEMPLATE_JUNIE_GUIDELINES.md`), instruindo o Junie a economizar tokens (KISS), ler obrigatoriamente `.ai-memory/handoff.md`, `.ai-memory/gotchas.md`, `.ai-memory/decisions.md` e `.agents/skills/csctracker/SKILL.md` antes de qualquer tarefa, e atualizar `.ai-memory/handoff.md` ao concluir.
- **Commit / Sincronismo Conjunto:** Caso qualquer um desses arquivos não exista ou esteja desatualizado no repositório, o assistente DEVE criá-lo/atualizá-lo e incluí-lo no próximo commit/push (e no `.zip`), garantindo que qualquer `git clone` ou `git pull` em qualquer máquina (Notebook, VPS, IDE local com Junie ou Nuvem) já traga a skill e a memória configuradas sem intervenção manual.

## 10. Diretriz 3.17 — Protocolo de Memória Contínua `ai-memory` (`Recall ➔ Checkpoint ➔ Consolidate ➔ Handoff`)
Para eliminar perda de contexto entre sessões ou por compactação em conversas longas, o assistente DEVE operar o ciclo de vida da `ai-memory` (`projects/ai-memory/` no Drive + `.ai-memory/` no repositório):
- **1. `Recall` (Na Entrada da Sessão):**
  - Ler `projects/ai-memory/00_INDEX.md`, `WIP_GLOBAL.md`, `INBOX_INTEGRACOES.md` e `GLOBAL_ECOSSISTEMA.md` no Drive, além do `.ai-memory/handoff.md`, `gotchas.md` e `decisions.md` do projeto alvo.
  - **Verificação de Correio Cruzado (`INBOX_INTEGRACOES.md`):** Se houver qualquer item `PENDENTE` endereçado ao projeto atual no `INBOX_INTEGRACOES.md`, avisar o desenvolvedor imediatamente no início da resposta.
  - **Validação contra o Código Real (*Memory Lint*):** Tratar memórias antigas como evidência histórica; se o código atual tiver mudado e tornado uma nota obsoleta, marcá-la como `[STALE]` e atualizá-la.
- **2. `Checkpoint` Anti-Compactação (Durante Sessões Longas):**
  - Não esperar o fim do chat para gravar memória. A cada etapa importante concluída, ou sempre que uma hipótese/abordagem for testada e **falhar** (*Failed Approaches*), atualizar imediatamente a seção correspondente em `.ai-memory/handoff.md` (e `WIP_GLOBAL.md`). Assim, caso a janela de contexto sofra compactação, o estado exato e o que já falhou ficam preservados em disco.
- **3. `Consolidate` e Tags de Ciclo de Vida:**
  - Novos aprendizados sobre armadilhas/bugs cabeludos vão para `.ai-memory/gotchas.md` (ou `gotchas_globais.md` se afetarem vários projetos).
  - Decisões técnicas e o motivo de descartar alternativas vão para `.ai-memory/decisions.md`.
  - Respeitar as tags: `[PINNED]` (nunca apagar na rotação) e `[EXPIRES: AAAA-MM-DD]` / `[TEMP: até concluir Ideia #ID]` (arquivar/limpar automaticamente após vencer).
- **4. `Handoff`, Inbox Cruzado e Sincronia Dupla (No Fechamento da Tarefa):**
  - Ao concluir uma entrega:
    1. Atualizar `.ai-memory/handoff.md` e `.ai-memory/changelog_sessoes.md` dentro do repositório Git (commitando junto com a alteração) e espelhar os arquivos atualizados em `projects/ai-memory/projects/<Projeto>/` no Google Drive;
    2. Atualizar `projects/ai-memory/WIP_GLOBAL.md` no Drive;
    3. **Se a alteração impactar outro repositório do ecossistema** (ex.: mudança de contrato REST, payload MQTT, schema ClickHouse ou variável de compose), registrar obrigatoriamente um aviso `PENDENTE` em `projects/ai-memory/INBOX_INTEGRACOES.md` para o projeto de destino;
    4. Sincronizar o backup `.zip` em `projects/repositorys/<Projeto>/` no Google Drive;
    5. Quando `changelog_sessoes.md` acumular mais de 10 sessões, rotacionar as mais antigas para `projects/ai-memory/arquivo_sessoes/AAAA-MM.md` no Drive para manter os arquivos quentes sempre enxutos.

## 11. Diretriz 3.18 — Proibição Estrita de Formato Google Docs (Exclusividade de Texto Puro .md / .yml / .csv)
- **REGRA INEGOCIÁVEL:** É expressamente e terminantemente PROIBIDO criar, salvar, converter ou exportar arquivos para o formato nativo do Google Docs (`application/vnd.google-apps.document`, `gdoc`) dentro de qualquer diretório do ecossistema CscTracker (`projects/`, `AI_specs/`, `ai-memory/`, `ideias/`, `fluxos/`, `composes/`, etc.).
- **PADRÃO EXCLUSIVO DE ARQUIVOS:**
  - Toda documentação, especificação, prompt, memória e arquivo de ideia DEVE ser persistido como arquivo Markdown texto puro (`text/markdown`, extensão `.md`).
  - Todo arquivo de compose, manifesto ou configuração DEVE ser persistido como texto puro YAML (`text/yaml`, extensão `.yml` ou `.yaml`).
  - Todo índice de controle de backlog DEVE ser persistido como texto puro CSV (`text/csv`, extensão `.csv`).
- **UPLOAD E CRIAÇÃO VIA GDRIVE:** Ao realizar uploads ou atualizações via CLI do `gdrive`, o assistente DEVE SEMPRE especificar `--mime-type "text/markdown"` (ou `"text/yaml"` / `"text/csv"`), JAMAIS permitindo conversão para Docs (`--convert` proibido).
- **OBJETIVO DESTA DIRETRIZ:** Garantir que o desenvolvedor possa editar e ler os arquivos nativamente e sem atritos em qualquer IDE local (JetBrains, VS Code, Notepad) através do Google Drive sincronizado no Windows (`G:\My Drive\CscTracker (1)`), assegurar compatibilidade nativa com agentes autônomos locais (JetBrains Junie) e possibilitar o versionamento direto via Git sem atalhos `.gdoc`.
