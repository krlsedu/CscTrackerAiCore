# CscTrackerAiCore

[![PyPI version](https://img.shields.io/pypi/v/csctracker-ai-core.svg)](https://pypi.org/project/csctracker-ai-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/csctracker-ai-core.svg)](https://pypi.org/project/csctracker-ai-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/pepy/dt/csctracker-ai-core?label=downloads&color=green)](https://pepy.tech/project/csctracker-ai-core)

CscTrackerAiCore é uma biblioteca Python desenvolvida para facilitar a integração com modelos de IA, especificamente o Google Gemini, oferecendo robustez através de rotação de chaves de API e observabilidade com ClickHouse.

## Principais Funcionalidades

- **Integração com Google Gemini**: Suporte para análise de textos e imagens (base64) utilizando os modelos generativos do Google.
- **Rotação Inteligente de Chaves (API Key Rotation)**:
    - Gerenciamento automático de múltiplas chaves de API (gratuitas e pagas).
    - Mecanismo de fallback: tenta chaves gratuitas primeiro e migra para pagas se necessário.
    - **Fallback de Modelo por Tier (`GOOGLE_TIER_FALLBACKS`)**: após 2 erros consecutivos não-cota (exceções de API/5xx/timeout ou `JSONDecodeError`), ativa o modelo fallback do tier (`lite`, `flash`, `pro`, `ultra`) por **5 minutos (`300s`)**, com estado isolado por `service_tier` (`standard` e `flex` independentes) e alternância de volta ao principal se o próprio fallback falhar 2x seguidas.
    - Tratamento de limites de quota (Error 429) com suspensão temporária de chaves/modelos atingidos.
    - Retry automático em caso de falhas.
- **Telemetria e Observabilidade**:
    - Integração nativa com **ClickHouse** para log de eventos.
    - Registro detalhado de uso de tokens (input, output e imagem).
    - Persistência dos prompts, respostas e metadados das tarefas para auditoria e análise.

## Requisitos

- Python 3.11+ (validado até Python 3.15)
- Google GenAI SDK (`google-genai>=3.6.0,<4`)
- ClickHouse Connect (`clickhouse-connect>=1.13.0,<2`)
- CscTrackerPyCore (`csctracker-py-core>=26.47.3`)

## Instalação

As dependências podem ser instaladas via `pip`:

```bash
pip install csctracker-ai-core
```

Ou via `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Configuração

A biblioteca pode ser configurada tanto via parâmetros no construtor quanto via variáveis de ambiente.

### Variáveis de Ambiente

As seguintes variáveis de ambiente são suportadas:

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `CLICKHOUSE_HOST` | Host do banco de dados ClickHouse | `localhost` |
| `CLICKHOUSE_PORT` | Porta do ClickHouse | `8123` |
| `CLICKHOUSE_USER` | Usuário do ClickHouse | `admin` |
| `CLICKHOUSE_PASSWORD` | Senha do ClickHouse | `senha123` |
| `CLICKHOUSE_DB` | Nome do banco de dados | `default` |
| `GOOGLE_FREE_KEYS` | Lista de chaves gratuitas (separadas por vírgula) | `key1,key2` |
| `GOOGLE_PAID_KEYS` | Lista de chaves pagas (separadas por vírgula) | `key_paga1` |
| `GOOGLE_MODEL_LIMITS` | Limites de concorrência por modelo (aceita tag opcional `:tier`) | `gemini-4-hydrogen:flash=5,gemini-4-argon:pro=2` |
| `GOOGLE_TIER_FALLBACKS` | Modelo fallback por tier canônico (`lite`, `flash`, `pro`, `ultra`), com `:limite` opcional | `pro=gemini-4-neon:15,flash=gemini-4-hydrogen:50,lite=gemini-3.5-flash-lite:500` |
| `GOOGLE_TIMEOUT_STANDARD_SECONDS` | Timeout HTTP (em segundos) para chamadas `standard` (default: `300`) | `300` |
| `GOOGLE_TIMEOUT_FLEX_SECONDS` | Timeout HTTP (em segundos) para chamadas `flex` (default: `600`) | `600` |
| `GOOGLE_RETRY_BACKOFF_BASE_SECONDS` | Atraso base (s) do backoff exponencial com jitter em erros transitórios (default: `0.5`) | `0.5` |
| `GOOGLE_RETRY_BACKOFF_MAX_SECONDS` | Teto (s) do backoff exponencial em erros transitórios (default: `4.0`) | `4.0` |
| `GOOGLE_MAX_NON_QUOTA_ERRORS` | Teto rígido de erros não-cota por requisição antes de abortar (default: `4`) | `4` |
| `GOOGLE_MAX_NO_SLOT_RETRIES` | Teto rígido de esperas consecutivas por slot indisponível antes de abortar (default: `5`) | `5` |
| `CLICKHOUSE_CONNECT_TIMEOUT` | Timeout de conexão (s) com o ClickHouse (default: `5`) | `5` |
| `CLICKHOUSE_SEND_RECEIVE_TIMEOUT` | Timeout de leitura/escrita (s) no ClickHouse (default: `30`) | `30` |
| `CLICKHOUSE_ASYNC_TELEMETRY` | Habilita telemetria assíncrona em fila com batching (default: `true`) | `true` |
| `CLICKHOUSE_QUEUE_MAXSIZE` | Limite máximo de eventos na fila assíncrona (default: `10000`) | `10000` |
| `CLICKHOUSE_QUEUE_MAX_MB` | Teto de RAM (MB) aproximado para `payload + result` na fila (default: `500`) | `500` |
| `CLICKHOUSE_BATCH_SIZE` | Quantidade de eventos por lote de inserção no ClickHouse (default: `20`) | `20` |
| `CLICKHOUSE_FLUSH_INTERVAL_SECONDS` | Intervalo máximo (s) para flush do lote pendente (default: `5.0`) | `5.0` |

> **Nota sobre `GOOGLE_MODEL_LIMITS`**: Aceita o formato simples `modelo=limite,modelo2=limite2` (com tag opcional `:tier`) ou um JSON `{"modelo": limite}`. Mantenha aqui apenas os modelos **titulares**.
>
> **Nota sobre `GOOGLE_TIER_FALLBACKS`**: Aceita o formato simples `tier=modelo[:limite],tier2=modelo2[:limite]` ou um JSON `{"flash": "gemini-4-hydrogen:50"}`. Se `:limite` for omitido e o modelo não estiver em `GOOGLE_MODEL_LIMITS`, ele recebe automaticamente o **limite padrão de `20` slots** e só é utilizado quando o fallback do tier estiver ativo (sem entrar na fila dos titulares). O cooldown de **5 minutos (`300s`)** após 2 erros consecutivos é mantido de forma **independente por `service_tier`** (`flex` não afeta `standard` e vice-versa).

## Uso Didático

### 1. Inicialização do `IaProcessor`

A classe `IaProcessor` é o ponto de entrada principal.

```python
from csctracker_ai_core.service.IaProcessor import IaProcessor

processor = IaProcessor(
    host="seu-clickhouse.com", # Opcional se usar ENV
    google_free_keys=["chave1"], # Opcional se usar ENV
    google_paid_keys=["chave_paga1"] # Opcional se usar ENV
)
```

**Parâmetros do Construtor:**
- `host`, `port`, `username`, `password`: Credenciais do ClickHouse.
- `google_free_keys`: String separada por vírgulas com chaves API do Google AI Studio (tier gratuito).
- `google_paid_keys`: String separada por vírgulas com chaves API faturadas (tier pago).
- `google_models_limits`: Dicionário ou string mapeando o nome do modelo ao limite de requisições simultâneas.
- `google_tier_fallbacks`: Dicionário ou string mapeando cada tier (`lite`, `flash`, `pro`, `ultra`) ao seu modelo fallback após 2 erros consecutivos.

### 2. Método `analisar_com_gemini`

Este método centraliza a lógica de chamada à IA com retry e rotação automática.

```python
resultado, tokens, event_id = processor.analisar_com_gemini(
    input_text="O que é o sol?",
    prompt="Responda como um cientista para uma criança.",
    task="explicacao_infantil",
    model_variant="flash",
    return_json=False
)
```

**Parâmetros Detalhados:**

- `input_text` (str): O conteúdo ou pergunta do usuário.
- `prompt` (str): A instrução de sistema (System Prompt) para orientar o comportamento da IA.
- `file_base64` (str, opcional): Imagem codificada em base64 para análise multimodal.
- `task` (str, opcional): Nome da tarefa para categorização nos logs do ClickHouse.
- `return_json` (bool, default `True`): Se `True`, força a IA a responder em formato JSON e tenta converter para um dicionário Python.
- `model_variant` (str, opcional): Filtra modelos que contenham o termo informado (ex: `"pro"` ou `"flash"`).
- `forced_free` (bool, default `False`): Se `True`, ignora chaves pagas mesmo que as gratuitas estejam esgotadas.
- `forced_paid` (bool, default `False`): Se `True`, ignora chaves gratuitas e usa apenas o tier pago.
- `mime_type` (str, default `"image/jpeg"`): Tipo do arquivo enviado em `file_base64`.
- `thinking_level` (str, default `"high"`): Nível de raciocínio enviado em `ThinkingConfig`.
- `service_tier` (str, default `"standard"`): Modo de execução (`"standard"` ou `"flex"`). O controle de fallback por tier (2 erros consecutivos + cooldown de 5 min) é isolado por `service_tier`.
- `timeout` (float, opcional): Override pontual do timeout HTTP em segundos para esta chamada (quando omitido, utiliza `GOOGLE_TIMEOUT_STANDARD_SECONDS` ou `GOOGLE_TIMEOUT_FLEX_SECONDS`).

**Retorno:**
- `resultado`: Resposta da IA (dict se `return_json=True`, str caso contrário).
- `tokens`: Total de tokens de entrada (prompt + imagem).
- `event_id`: UUID único gerado para esta operação, útil para rastreio no banco de dados.

## Estrutura do Projeto

- `IaProcessor`: Orquestrador que recebe a requisição, seleciona a melhor chave e persiste a telemetria.
- `ApiKeyRotator`: Motor de inteligência que gerencia as cotas, suspende chaves temporariamente em caso de Erro 429 e decide qual o melhor modelo disponível baseado em custo (prioriza gratuito e, no pago, prioriza o mais barato).
- `ClickHouseDb`: Gerencia a conexão e a criação automática da tabela `ai_events`.

## ⚠️ Aviso Legal e Termos de Uso (Disclaimer)

Esta biblioteca implementa **rotação de chaves de API** (`ApiKeyRotator`) como um mecanismo de **resiliência e estudo** para projetos de desenvolvimento, testes e aplicações de baixo volume.

### Sobre os Termos de Serviço do Google
O uso de múltiplas contas ou chaves gratuitas com o **único propósito de burlar os limites de taxa (Rate Limits/Quotas)** impostos pelo Google Gemini API pode ser interpretado como violação dos Termos de Serviço (ToS) da plataforma.

- **Uso Consciente:** Recomendamos o uso deste recurso para evitar interrupções em testes ou para distribuir carga em cenários educacionais e de pesquisa.
- **Ambientes de Produção:** Para aplicações críticas, comerciais ou de alto volume, **recomendamos fortemente o uso do tier pago (Pay-as-you-go)**. A biblioteca suporta nativamente o uso de chaves pagas, que oferecem limites maiores e estabilidade garantida por SLA.

**Isenção de Responsabilidade:** O autor desta biblioteca não se responsabiliza pelo uso indevido da ferramenta, nem por eventuais bloqueios, suspensões de conta ou cobranças decorrentes da violação dos termos da API do Google. Use com responsabilidade.

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.