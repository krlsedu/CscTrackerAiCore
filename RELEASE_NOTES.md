Aqui está o Release Notes técnico para a versão **v26.15.001**, estruturado com foco em clareza para a equipe de engenharia e stakeholders.

---

# 📝 Release Notes - v26.15.001
**Data:** 2026  
**Responsável:** Tech Lead  
**Commit:** `d5e1ab0`

---

## 🚀 Features

### Suporte a Service Tiers no Processamento de IA
Implementada a segmentação por níveis de serviço (`service_tier`) no componente central de processamento.
- **IaProcessor:** Adicionado suporte nativo para identificar e tratar diferentes camadas de serviço durante a execução.
- **Database Schema:** Atualização do esquema do banco de dados para persistência e suporte aos novos atributos de tiering.

### Telemetria Avançada
Refatoração significativa no módulo de telemetria para suportar observabilidade granular por nível de serviço.
- **Telemetry.py:** Implementação de logs detalhados que agora incluem o `service_tier`, permitindo análises de custo e performance por categoria de usuário/serviço.
- **ClickHouseDb:** Otimização das queries e estrutura de inserção para suportar os novos campos de telemetria de forma performática.

---

## 🐛 Fixes
*Nenhuma correção de bug reportada nesta versão.*

---

## 🔧 Chore

### Atualização de Dependências
- **Google GenAI:** Upgrade da biblioteca `google-genai` no `requirements.txt` para garantir compatibilidade com as últimas APIs e melhorias de estabilidade nos modelos generativos.

---

### 📊 Resumo de Alterações
- **Arquivos modificados:** 4
- **Inserções:** 119
- **Deleções:** 34

> **Nota Técnica:** Esta versão foca na fundação para monetização e controle de cotas, permitindo que o sistema diferencie o processamento baseado no tier do serviço contratado. A atualização do ClickHouse é crítica para manter a integridade dos dados analíticos.