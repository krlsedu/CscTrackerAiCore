# CscTrackerAiCore

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

# Realizando uma análise
resultado, tokens, event_id = processor.analisar_com_gemini(
    input_text="Qual a capital da França?",
    prompt="Responda de forma concisa.",
    task="pergunta_geral"
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

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.