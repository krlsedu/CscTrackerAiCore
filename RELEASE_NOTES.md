Aqui está o Release Notes técnico estruturado para a versão **v26.21.001**, focado em clareza para a equipe de engenharia e stakeholders.

---

# 📦 Release Notes - v26.21.001

## 📝 Sumário
Esta versão foca no refinamento da lógica de seleção e rotação de chaves de API no core de IA, permitindo um controle mais granular sobre as variantes de modelos e famílias de provedores.

---

## 🚀 Features

### Refinamento no `ApiKeyRotator`
Implementada a capacidade de filtragem avançada durante a seleção de slots de chaves de API. 
- **Parâmetro `variant_family`**: Agora é possível agrupar e selecionar chaves baseadas na família da variante do modelo, facilitando a gestão de modelos multimodais ou de diferentes capacidades dentro do mesmo provedor.
- **Parâmetro `exact_match`**: Adicionado suporte para busca exata, garantindo que o seletor de chaves retorne apenas credenciais que correspondam rigorosamente aos critérios definidos, evitando fallbacks indesejados em ambientes de produção.

---

## 🔧 Chore

- **Refatoração Interna**: Otimização do serviço `ApiKeyRotator.py` com a adição de 42 novas linhas de lógica de validação e filtragem, melhorando a robustez do sistema de rotação.

---

## 🛠 Detalhes Técnicos
- **Arquivos Alterados:** `csctracker_ai_core/service/ApiKeyRotator.py`
- **ID do Commit:** `e5d130f`
- **Autor:** Carlos Eduardo Duarte Schwalm

---
*Gerado automaticamente pelo Tech Lead Bot.*