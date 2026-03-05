Aqui estão as Notas de Lançamento para a versão **v26.10.008**, formatadas conforme os padrões de engenharia.

---

# 📝 Release Notes - v26.10.008

## Resumo
Esta versão foca em melhorias na infraestrutura de CI/CD, proporcionando maior flexibilidade para a equipe de desenvolvimento ao gerenciar os ciclos de build.

---

## 🚀 Features
*Nenhuma funcionalidade de negócio foi implementada nesta versão.*

## 🐛 Fixes
*Nenhuma correção de bug foi aplicada nesta versão.*

## 🔧 Chore & DevOps
*   **Pipeline de Build:** Adicionado suporte para gatilho manual (`workflow_dispatch`) no GitHub Actions. Isso permite que a equipe dispare builds sob demanda sem a necessidade de novos commits.
*   **Versionamento:** Atualização dos arquivos de controle (`version.txt`) e sincronização do histórico de lançamentos.

---

### Detalhes Técnicos dos Commits:
*   `be315ab`: Adição do trigger `workflow_dispatch` em `.github/workflows/build.yml`.
*   `0c254ec`: Incremento de versão e manutenção de metadados de release.

**Tech Lead:** Carlos Eduardo Duarte Schwalm (krlsedu)