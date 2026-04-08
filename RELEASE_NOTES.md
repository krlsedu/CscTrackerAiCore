Aqui está o Release Notes técnico para a versão **v26.15.004**, estruturado conforme as boas práticas de engenharia.

---

# 📦 Release Notes - v26.15.004

## 📝 Resumo
Esta versão foca na manutenção preventiva e refinamento da camada de persistência de dados (ClickHouse), corrigindo inconsistências nos logs de erro durante operações de migração de esquema.

---

## 🐛 Fixes
*   **ClickHouseDb Service:** Correção de erro de digitação (*typo*) nas mensagens de log disparadas durante a adição da coluna `service_tier`. Essa correção melhora a rastreabilidade e a análise de logs em ambientes de produção.

## 🔧 Chore
*   **Refatoração de Código:** Limpeza técnica no arquivo `csctracker_ai_core/service/ClickHouseDb.py` para garantir conformidade com os padrões de escrita do projeto.

---

### 🛠 Detalhes Técnicos
*   **Commit:** `81302db`
*   **Impacto:** Baixo (Apenas logs).
*   **Arquivos alterados:** 1 arquivo (`ClickHouseDb.py`).
*   **Autor:** Carlos Eduardo Duarte Schwalm (krlsedu)