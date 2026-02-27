Aqui estão as Notas de Lançamento (Release Notes) para a versão **v26.09.001**, elaboradas com foco técnico e clareza.

---

# 📝 Release Notes - v26.09.001

## Resumo
Esta versão foca na resiliência do processamento de dados provenientes de modelos de IA, garantindo que a ausência de metadados de consumo não interrompa o fluxo principal da aplicação.

---

## 🐛 Fixes

*   **Tratamento de Metadados no `IaProcessor`**: Implementada uma proteção para casos onde o campo `output_tokens` não é retornado pelo provedor de IA. 
    *   Agora, o sistema atribui um valor padrão (fallback) em vez de lançar uma exceção.
    *   Adicionada uma sinalização via log (Warning) para monitoramento de inconsistências nas respostas da API.
    *   *Arquivo afetado:* `csctracker_ai_core/service/IaProcessor.py`

---

## 🚀 Features
*   *Nenhuma nova funcionalidade nesta versão.*

---

## 🔧 Chore
*   *Nenhuma alteração de infraestrutura ou manutenção nesta versão.*

---

**Build Info:**
- **Versão:** `v26.09.001`
- **Commit Base:** `7b26a92`
- **Data:** 2026