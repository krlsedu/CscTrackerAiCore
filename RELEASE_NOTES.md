Aqui estão as Notas de Lançamento para a versão **v26.10.007**, focadas em melhorias de infraestrutura e automação.

---

# 📝 Release Notes - v26.10.007

## 🔧 Chore
- **CI/CD Pipeline:** Adicionado o gatilho `workflow_dispatch` ao pipeline de build no GitHub Actions. 
    - *Impacto:* Agora é possível disparar manualmente o processo de build através da interface do GitHub, proporcionando maior flexibilidade para validações pontuais e deploys fora do fluxo automatizado de push/PR.

---
**Detalhes técnicos:**
- **Commit:** `be315ab`
- **Arquivo alterado:** `.github/workflows/build.yml`
- **Autor:** Carlos Eduardo Duarte Schwalm (krlsedu)