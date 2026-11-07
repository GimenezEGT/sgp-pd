# Feature 010 — Painel do gestor e notificações

O Gestor de P&D acompanha todos os projetos sem pedir relatórios, e ninguém perde prazo de revisão ou assinatura.

```text
/speckit-specify Painel do Gestor de P&D e notificações. Leia docs/contexto/01-visao-geral.md.

Objetivo: o gestor vê o andamento de todos os projetos sem pedir relatórios, e ninguém perde prazo de revisão ou assinatura.

Histórias:
1. Como Gestor de P&D, vejo a carteira de projetos com etapa atual, percentual de subdocumentos aprovados, marcos planejados × realizados, atraso em dias e líder.
2. Abro um projeto e vejo a linha do tempo: marcos, subdocumentos e versões, assinaturas, alterações e atividade do caderno.
3. Vejo minha fila de pendências: documentos aguardando minha revisão ou assinatura, com o tempo de espera.
4. Como analista ou líder, vejo minhas pendências e recebo e-mail quando um documento é devolvido, aprovado ou fica parado além do prazo configurado.
5. Exporto a carteira em planilha.

Regras: o painel respeita as permissões (quem não vê dados financeiros não vê custo nem retorno); notificações podem ser desligadas por tipo, exceto as de assinatura pendente.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os indicadores que o gestor quer na primeira tela.
- E-mail imediato ou resumo diário.
- Se haverá custo realizado (vindo do Sankhya) para comparar com o custo planejado do Plano de Negócios.

```text
/speckit-plan Consultas agregadas com índices dedicados e cache de 5 minutos. Gráficos simples em SVG gerado no servidor, sem build de front-end. E-mails pelo SMTP interno em tarefa agendada (Celery beat), com resumo diário. Exportação XLSX com openpyxl.
```

Checklists sugeridos: permissões e usabilidade.

Pronto quando:

- [ ] O painel abre em menos de 2 s com 100 projetos.
- [ ] O e-mail de pendência chega no dia seguinte ao vencimento do prazo.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
