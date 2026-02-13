# CscTrackerAiCore

CscTrackerAiCore é uma biblioteca Python desenvolvida para facilitar a integração com modelos de IA, especificamente o Google Gemini, oferecendo robustez através de rotação de chaves de API e observabilidade com ClickHouse.

## Principais Funcionalidades

- **Integração com Google Gemini**: Suporte para análise de textos e imagens (base64) utilizando os modelos generativos do Google, com suporte a filtragem por variante de modelo (`pro` ou `flash`) e controle de tier (forçar uso de chaves gratuitas ou pagas).
- **Rotação Inteligente de Chaves (API Key Rotation)**:
    - Gerenciamento automático de múltiplas chaves de API (gratuitas e pagas).
    - Mecanismo de fallback: tenta chaves gratuitas primeiro e migra para pagas se necessário.
    - Suporte a seleção específica de variante de modelo (ex: garantir uso de `pro` ou `flash`).
    - Possibilidade de forçar o uso exclusivo de um tier (`forced_free` ou `forced_paid`).
    - Tratamento de limites de quota (Error 429) com suspensão temporária de chaves/modelos atingidos.
    - Retry automático em caso de falhas.
- **Telemetria e Observabilidade**:
    - Integração nativa com **ClickHouse** para log de eventos.
    - Registro detalhado de uso de tokens (input, output e imagem).
    - Persistência dos prompts, respostas e metadados das tarefas para auditoria e análise.
- **Tratamento de Erros**: Exceções customizadas para lidar com falhas específicas do serviço de IA.

## Requisitos

- Python 3.10+
- Google GenAI SDK
- Clickhouse Connect

## Configuração e Uso

### Exemplo Básico

```python
from csctracker_ai_core.service.IaProcessor import IaProcessor

# Inicialização do processador
processor = IaProcessor(
    host="seu-clickhouse-host",
    google_free_keys=["chave1", "chave2"],
    google_paid_keys=["chave_paga1"]
)

# Realizando uma análise básica
resultado, tokens, event_id = processor.analisar_com_gemini(
    input_text="Qual a capital da França?",
    prompt="Responda de forma concisa.",
    task="pergunta_geral"
)

# Realizando uma análise forçando uma variante específica (ex: flash)
resultado_flash, tokens_flash, event_id_flash = processor.analisar_com_gemini(
    input_text="Resuma o histórico da IA.",
    prompt="Seja didático.",
    task="resumo_ia",
    model_variant="flash"
)

# Realizando uma análise forçando apenas chaves gratuitas
resultado_free, tokens_free, event_id_free = processor.analisar_com_gemini(
    input_text="Explique como funciona um motor a combustão.",
    task="explicacao_motor",
    forced_free=True
)

print(f"Resultado: {resultado}")
print(f"Tokens usados: {tokens}")
```

## Instalação

As dependências podem ser instaladas via `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Estrutura do Projeto

- `IaProcessor`: Classe principal para interface com a IA.
- `ApiKeyRotator`: Gerencia o ciclo de vida e seleção das chaves de API.
- `ClickHouseDb`: Responsável pela conexão e persistência de dados no ClickHouse.

## ⚠️ Aviso Legal e Termos de Uso (Disclaimer)

Esta biblioteca implementa **rotação de chaves de API** (`ApiKeyRotator`) como um mecanismo de **resiliência e estudo** para projetos de desenvolvimento, testes e aplicações de baixo volume.

### Sobre os Termos de Serviço do Google
O uso de múltiplas contas ou chaves gratuitas com o **único propósito de burlar os limites de taxa (Rate Limits/Quotas)** impostos pelo Google Gemini API pode ser interpretado como violação dos Termos de Serviço (ToS) da plataforma.

- **Uso Consciente:** Recomendamos o uso deste recurso para evitar interrupções em testes ou para distribuir carga em cenários educacionais e de pesquisa.
- **Ambientes de Produção:** Para aplicações críticas, comerciais ou de alto volume, **recomendamos fortemente o uso do tier pago (Pay-as-you-go)**. A biblioteca suporta nativamente o uso de chaves pagas, que oferecem limites maiores e estabilidade garantida por SLA.

**Isenção de Responsabilidade:** O autor desta biblioteca não se responsabiliza pelo uso indevido da ferramenta, nem por eventuais bloqueios, suspensões de conta ou cobranças decorrentes da violação dos termos da API do Google. Use com responsabilidade.

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.