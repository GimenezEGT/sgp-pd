# Research: Correções do ciclo de revisão e assinatura

## R1. Revisão única por pessoa e versão

- Decision: `sign_review` recusa quando já existe assinatura "Revisado" da pessoa na versão corrente
  (as assinaturas da 005 já são filtradas por versão); o bloco de assinaturas esconde a opção para
  quem já revisou.
- Rationale: FR-005; recusa no serviço cobre envio repetido do formulário e acesso direto.
- Alternatives considered: restrição única no banco (as assinaturas "Revisado" repetidas gravadas
  antes da correção impediriam a migração, e registros assinados não são alterados).

## R2. Gestor que elaborou

- Decision: o bloco de assinaturas ganha `own_submission` (documento em revisão elaborado pela
  pessoa) e `can_return_own` (pessoa com poder de aprovação e acesso ao projeto); mostra o aviso, o
  caminho para Delegações (só para quem tem o perfil Gestor de P&D) e o formulário de devolução com
  comentário, que usa a rota de devolução existente. A Fila de revisão ganha a seção "Elaborados por
  você — aguardam outro aprovador". A tela de aprovação não mostra o formulário de aprovação para quem
  elaborou (mostra o aviso e a devolução). A tela de envio avisa quem tem poder de aprovação.
- Rationale: respostas provisórias do esclarecimento (devolução pela própria pessoa; aviso sem
  bloqueio); a devolução da 005 já é permitida a aprovadores e exige comentário.
- Alternatives considered: ação nova de "recolher envio" (rota e evento novos sem necessidade).

## R3. Situação pelo nome

- Decision: `STATUS_LABELS` em `sgp/signatures/documents.py` (Rascunho, Em revisão, Devolvido,
  Aprovado) e `status_label` no contexto das telas de envio e aprovação.
- Rationale: FR-006; os códigos são os mesmos para subdocumentos, TAP e Plano de Negócios.
