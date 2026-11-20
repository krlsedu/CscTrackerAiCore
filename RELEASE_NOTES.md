Release Notes - v26.47.002

Abaixo estão as notas de atualização para a versão v26.47.002. Esta versão introduz a capacidade de definir limites opcionais de tentativas ou quotas na estratégia de fallback de tiers para a API do Google, aprimorando a resiliência e o controle de consumo de chaves no componente ApiKeyRotator. A mudança é acompanhada de cobertura abrangente de testes unitários e atualização completa da documentação e memórias de arquitetura do projeto.

## 🚀 Features
* **ApiKeyRotator / Fallback de Tiers:** Implementação de suporte a limites opcionais configuráveis na variável de ambiente/definição de `GOOGLE_TIER_FALLBACKS`, permitindo delimitar a quantidade de tentativas ou quota máxima de uso por nível de fallback antes da rotação definitiva de tier. Esta evolução visa conferir controle granular sobre a degradação graciosa do serviço ao consumir modelos do Google, evitando custos excessivos ou esgotamento prematuro de chaves prioritárias, além de incluir suíte de testes unitários dedicada para validar a nova lógica de chaveamento (`csctracker_ai_core/service/ApiKeyRotator.py`).
  * *Commit: `3688ae1` | Autor: @krlsedu*

## 🐛 Fixes
*(Nenhuma alteração desta categoria nesta versão)*

## 🔧 Chore
*(Nenhuma alteração desta categoria nesta versão)*