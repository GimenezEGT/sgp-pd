# Feature 001 — Fundação: acesso, perfis e trilha de auditoria

A primeira feature entrega o esqueleto seguro: login pela rede, perfis, acesso por projeto e a trilha de auditoria que todas as outras features vão usar.

```text
/speckit-specify Fundação do SGP-P&D: acesso, perfis e trilha de auditoria. Leia docs/contexto/01-visao-geral.md e docs/contexto/04-requisitos-regulatorios.md.

Contexto: o sistema roda na intranet e guarda registros de controle de projeto sujeitos às Boas Práticas de Fabricação (RDC 665/2022). Só pessoas autorizadas entram, e tudo o que acontece precisa ser rastreável.

Perfis: Administrador do sistema; Gestor de P&D; Líder de projeto; Analista/Pesquisador; Qualidade/Assuntos Regulatórios (leitura ampla e revisão); Leitor (consulta). Uma pessoa pode ter mais de um perfil. O acesso a cada projeto depende de ser membro dele, exceto para Gestor de P&D, Qualidade e Administrador.

Histórias:
1. Como colaborador, entro com meu usuário e senha de rede; sem perfil no sistema, vejo como pedir acesso.
2. Como administrador, concedo e revogo perfis; cada mudança de permissão registra quem fez, quando e por quê.
3. Como usuário, minha sessão expira após inatividade configurável e o login bloqueia após tentativas inválidas, conforme a política da TI.
4. Como auditor da Qualidade, consulto a trilha de auditoria por usuário, projeto, período e tipo de evento, e exporto o resultado.
5. Como Garantia da Qualidade, preciso provar que a trilha não foi adulterada: o sistema verifica a integridade da cadeia de eventos e aponta qualquer quebra.

Regras: nenhum registro é apagado fisicamente; data e hora vêm do servidor sincronizado; eventos guardam valor anterior, valor novo e motivo quando houver; colaborador desativado na rede perde o acesso no próximo login.

Fora do escopo: projetos e documentos (features seguintes).
```

Pontos que o `/speckit-clarify` deve fechar:

- Tempo de inatividade e número de tentativas, conforme a política da TI.
- Quem aprova a concessão de perfil.
- Retenção da trilha: tempo de vida do produto, nunca menos de 2 anos (RDC 665/2022, art. 37).
- Necessidade de acesso para consultores externos sem conta na rede.

```text
/speckit-plan Use Python 3.12+ e Django (versão LTS vigente), PostgreSQL 16+, templates do Django com HTMX, sem SPA. Autenticação LDAP/Active Directory com django-auth-ldap e grupos do AD mapeados para perfis; sessões no servidor com expiração configurável. Trilha de auditoria em tabela append-only (sem UPDATE e DELETE por permissão do usuário de banco), cada evento com hash SHA-256 do anterior, e job diário que verifica a cadeia. Datas em UTC no banco, exibidas em America/Sao_Paulo. Monólito modular com apps core, contas e auditoria. Testes com pytest e pytest-django, cobertura mínima de 90% em core e auditoria. Docker Compose com app, banco e Nginx com TLS interno. Configuração por variáveis de ambiente, sem segredos no repositório.
```

Checklists sugeridos: segurança (autenticação e sessão) e integridade de dados (ALCOA+).

Pronto quando:

- [ ] Login pelo AD funciona em homologação e usuário sem perfil é barrado.
- [ ] Uma alteração feita direto no banco é revelada pela verificação da cadeia.
- [ ] A trilha exporta com filtros.
- [ ] `/speckit-converge` reporta Converged.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
