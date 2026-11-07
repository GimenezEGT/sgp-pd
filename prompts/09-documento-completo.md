# Feature 009 — Documento completo do projeto

Com um clique, o sistema monta o registro histórico do projeto exigido pelo art. 61 da RDC 665/2022: todos os subdocumentos aprovados, o histórico do caderno, o quadro de versões e o resumo da auditoria.

```text
/speckit-specify Documento completo do projeto, que é o registro histórico do projeto exigido pela RDC 665/2022 (art. 61), montado automaticamente. Leia docs/contexto/03-padroes-formatacao.md e 04-requisitos-regulatorios.md.

Objetivo: gerar com um clique o documento consolidado que hoje é montado à mão, incluindo o histórico de experimentos do caderno de laboratório.

Histórias:
1. Como líder ou gestor, gero o documento completo de um projeto com capa geral, sumário automático, TAP e Plano de Negócios, cada subdocumento aprovado na versão vigente (com sua capa), alterações de projeto, verificação final, saída, histórico do caderno e lista de anexos.
2. Escolho se o histórico do caderno entra completo ou resumido (título, data, autor, conclusão e vínculos).
3. O documento traz um quadro de versões (subdocumento, versão, data de aprovação, signatários) e um resumo da trilha de auditoria do projeto.
4. Versões substituídas aparecem só no quadro de versões, não no corpo, a menos que eu peça o histórico completo.
5. Antes de gerar, o sistema mostra o que falta para o documento estar completo (subdocumentos não aprovados, pendências da Verificação Final).

Regras: só versões aprovadas entram no corpo; o documento gerado é arquivado com hash e versão; sumário e numeração de páginas são automáticos; dados financeiros do Plano de Negócios só entram para quem tem permissão.
```

Pontos que o `/speckit-clarify` deve fechar:

- A ordem oficial das partes; no projeto DBS a Alteração aparece logo após a capa da Entrada.
- Se o Plano de Negócios entra no documento completo ou fica num anexo restrito.
- Formato do resumo da auditoria (eventos por tipo ou lista completa).

```text
/speckit-plan Reutilize o gerador da feature 006 como composição de seções. Geração assíncrona com barra de progresso. PDFs de subdocumentos já gerados são reaproveitados quando a versão não mudou (cache por hash). Sumário com a numeração real das páginas, em duas passagens se a abordagem escolhida exigir. Meta: projeto de 300 páginas gerado em menos de 3 minutos no servidor de homologação.
```

Checklists sugeridos: regulatório (registro histórico do projeto) e desempenho.

Pronto quando:

- [ ] O documento completo de um projeto piloto é aprovado pela Qualidade.
- [ ] O sumário bate com as páginas.
- [ ] As pendências aparecem quando o projeto está incompleto.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
