Aqui estão as Notas de Lançamento (Release Notes) para a versão **v26.10.003**, focadas em melhorias de infraestrutura de dados e observabilidade.

---

# 📝 Release Notes - v26.10.003

## Resumo
Esta versão foca na implementação do novo motor de telemetria e na flexibilização da camada de persistência com ClickHouse, garantindo maior consistência na extração de métricas agregadas.

---

## 🚀 Features
*   **Novo Serviço de Telemetria:** Implementação do serviço `Telemetry`, permitindo a extração de dados agregados com suporte a períodos de tempo customizáveis. Esta funcionalidade centraliza a observabilidade de performance e uso do core de IA.

## 🐛 Fixes
*   **Consistência em Queries SQL:** Ajuste na formatação de caracteres de porcentagem (`%%`) nas queries de telemetria. Essa correção previne erros de interpolação de strings em drivers SQL, garantindo a execução correta de cálculos de métricas.

## 🔧 Chore
*   **Refatoração do `ClickHouseDb`:** Atualização do método de inicialização da classe de conexão com ClickHouse para suportar parâmetros opcionais. Isso aumenta a flexibilidade para diferentes ambientes e configurações de conexão sem quebrar a compatibilidade.

---

### 🛠 Detalhes Técnicos
*   **Arquivos alterados:** 2
*   **Commits analisados:** `d00e490`, `dfde023`
*   **Impacto:** Camada de serviço e integração com banco de dados.