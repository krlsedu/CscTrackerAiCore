# CscTrackerAiCore

[![PyPI version](https://img.shields.io/pypi/v/csctracker-ai-core.svg)](https://pypi.org/project/csctracker-ai-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/csctracker-ai-core.svg)](https://pypi.org/project/csctracker-ai-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


CscTrackerAiCore é uma biblioteca Python desenvolvida para facilitar a integração com modelos de IA, especificamente o Google Gemini, oferecendo robustez através de rotação de chaves de API e observabilidade com ClickHouse.

## Principais Funcionalidades

- **Integração com Google Gemini**: Suporte para análise de textos e imagens (base64) utilizando os modelos generativos do Google.
- **Rotação Inteligente de Chaves (API Key Rotation)**:
    - Gerenciamento automático de múltiplas chaves de API (gratuitas e pagas).
    - Mecanismo de fallback: tenta chaves gratuitas primeiro e migra para pagas se necessário.
    - Tratamento de limites de quota (Error 429) com suspensão temporária de chaves/modelos atingidos.
    - Retry automático em caso de falhas.
- **Telemetria e Observabilidade**:
    - Integração nativa com **ClickHouse** para log de eventos.
    - Registro detalhado de uso de tokens (input, output e imagem).
    - Persistência dos prompts, respostas e metadados das tarefas para auditoria e análise.

## Requisitos

- Python 3.10+
- Google GenAI SDK
- Clickhouse Connect

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
| `GOOGLE_MODEL_LIMITS` | Limites de concorrência por modelo | `gemini-1.5-flash=15,gemini-1.5-pro=2` |

> **Nota sobre `GOOGLE_MODEL_LIMITS`**: Aceita o formato simples `modelo=limite,modelo2=limite2` ou um JSON `{"modelo": limite}`.

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
- `google_free_keys`: Lista de strings com chaves API do Google AI Studio (tier gratuito).
- `google_paid_keys`: Lista de strings com chaves API faturadas (tier pago).
- `google_models_limits`: Dicionário ou string mapeando o nome do modelo ao limite de requisições simultâneas.

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