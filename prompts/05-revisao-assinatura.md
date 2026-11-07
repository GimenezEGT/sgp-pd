# Feature 005 — Revisão, versões e assinatura eletrônica

As assinaturas do analista e do Gestor de P&D passam a ser eletrônicas, com valor de registro, e cada versão aprovada fica congelada; acaba a impressão para assinar.

```text
/speckit-specify Ciclo de revisão, versões e assinatura eletrônica dos subdocumentos, do TAP e do Plano de Negócios. Leia docs/contexto/04-requisitos-regulatorios.md.

Objetivo: eliminar a impressão para assinatura. Todo documento tem versão, Analista Responsável (nome/função), Gestor de P&D e data; as assinaturas desses dois papéis passam a ser eletrônicas.

Histórias:
1. Como analista, envio um documento em rascunho para revisão; ele fica bloqueado para edição enquanto estiver em revisão.
2. Como Gestor de P&D, aprovo ou devolvo com comentário obrigatório; os comentários ficam no histórico do documento.
3. Para assinar, informo de novo minha senha de rede e escolho o significado (elaborado, revisado, aprovado); a assinatura guarda nome, função, data e hora do servidor e a identificação exata do conteúdo assinado.
4. Documento assinado pelos dois papéis fica "Aprovado" e imutável. Para corrigir, crio nova versão (02, 03...) com motivo; a anterior fica "Substituída" e continua consultável.
5. Como qualquer pessoa autorizada, verifico se um documento foi alterado depois de assinado.
6. Como Gestor de P&D, delego a aprovação a outra pessoa por um período, com motivo registrado.

Regras: quem elaborou não aprova o mesmo documento; uma assinatura nunca vale para outra versão; três falhas de senha seguidas bloqueiam a assinatura e geram alerta; a Validação do Produto usa o rótulo "Gestor de P&D responsável pela Aprovação", como no formulário atual.

Fora do escopo: certificado ICP-Brasil individual (avaliar depois) e geração do PDF (006), que exibirá as assinaturas.
```

Pontos que o `/speckit-clarify` deve fechar:

- Os significados de assinatura aceitos pela Garantia da Qualidade.
- Se a delegação de aprovação é permitida pelo PSG 20.
- Se a Qualidade também assina algum documento, como a Saída de Projeto.
- Prazo máximo de revisão antes de gerar alerta.

```text
/speckit-plan Máquina de estados por documento (rascunho, em revisão, aprovado, devolvido, substituído) com transições permitidas por perfil e testadas. Na assinatura, reautentique no AD por bind LDAP, sem guardar a senha. Calcule SHA-256 de uma representação canônica do conteúdo (JSON com chaves ordenadas mais os hashes dos anexos) e grave Assinatura com esse hash. Versão aprovada vira registro imutável (sem UPDATE por permissão de banco). A verificação de integridade recalcula o hash e compara. Eventos de assinatura vão para a trilha da feature 001. Limite de tentativas com bloqueio temporário.
```

Checklists sugeridos: integridade de dados e assinatura eletrônica (Lei 14.063/2020, art. 4º).

Pronto quando:

- [ ] Alterar no banco o conteúdo de uma versão aprovada é detectado.
- [ ] O elaborador não consegue aprovar o próprio documento.
- [ ] A versão substituída continua consultável.

---

Depois do `/speckit-plan`: rode `/speckit-checklist` com os temas sugeridos, `/speckit-tasks`, `/speckit-analyze` e `/speckit-implement`; repita `/speckit-implement` e `/speckit-converge` até o relatório dizer Converged. Faça commit ao fim de cada etapa.
