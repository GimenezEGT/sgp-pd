# Research: Revisão controlada dos modelos de documentos e subdocumentos

## R1. Ciclo sobre os modelos que já existem

- **Decision**: cada versão de modelo de formulário (004, `FormTemplate`) e de layout (006,
  `LayoutTemplate`) é a "versão de modelo" da revisão. Os dois ganham os mesmos campos de revisão
  (mixin abstrato `RevisableTemplate` da app nova `sgp.revisions`): situação da revisão (em
  elaboração ou enviada), motivo, impacto, envio, descarte e resumo aprovado; e a situação
  `discarded` ao lado de `draft` e `published`. A publicação direta das features 004 e 006 deixa de
  existir nas telas e nos serviços públicos: publicar passa a ser efeito da aprovação.
- **Rationale**: a vigência, a imutabilidade (serviço e gatilho), o vínculo dos documentos à versão
  e a migração entre versões já funcionam nesses modelos; a 013 acrescenta só o ciclo.
- **Alternatives considered**: tabela genérica de "revisões" com cópia do conteúdo (duplicaria a
  fonte do conteúdo e a vigência).

## R2. Situação calculada de cada versão

| Situação | Regra |
| --- | --- |
| Rascunho | `draft` e revisão em elaboração |
| Enviada | `draft` e revisão enviada |
| Aprovada aguardando vigência | `published` e vigência futura |
| Vigente | a versão que `current_template`/`current_layout` devolve hoje |
| Substituída | `published`, vigência já iniciada e não vigente |
| Descartada | `discarded` |

Só uma revisão em andamento por modelo (rascunho, enviada ou aprovada aguardando vigência): FR-006.

## R3. Assinatura da aprovação

- **Decision**: aprovação e retirada exigem a reautenticação da feature 005
  (`sgp.signatures.reauth.reauthenticate`, com as mesmas regras de tentativas e bloqueio) e gravam
  `TemplateSignature` (somente de inclusão): modelo, versão, finalidade (aprovação ou retirada),
  resumo do conteúdo, pessoa, função, significado "Aprovado", data e hora do servidor.
- **Rationale**: `signatures.Signature` exige projeto; modelo não pertence a projeto.

## R4. Resumo e verificação de integridade

- **Decision**: SHA-256 do JSON canônico da feature 005 sobre tipo, família, versão, referência
  (formulário), vigência, definição e SHA-256 do logotipo (layout), gravado na versão
  (`approved_hash`) e na assinatura. A verificação recalcula e compara com os dois e registra
  `templates.verified`.

## R5. Entrada em vigência

- **Decision**: aprovação com vigência imediata registra a etapa "entrou em vigência" na hora; com
  vigência futura, a tarefa diária do Celery (`sgp.revisions.record_due`, agendador embutido do
  worker) registra a etapa e o evento `templates.became_current` quando a data chega. A vigência não
  pode ser anterior a hoje nem à da versão vigente.

## R6. Comparação entre versões

- **Decision**: a definição é achatada em caminhos rotulados ("tópico Amostras › campo Tipos de
  amostra › rótulo"); listas de objetos com `key` são casadas pela chave; o resto pelo valor. A
  comparação lista incluídos, retirados e alterados (valor anterior e novo), mais referência,
  vigência e logotipo. O mesmo achatamento decide se a revisão "não muda nada" (FR-007).

## R7. Retirada de uso

- **Decision**: só modelos de subdocumento (esclarecimento de 2026-11-11). `TemplateRetirement`
  por tipo de subdocumento: pedida pela Qualidade/AR com motivo, aprovada pelo Gestor com assinatura
  ou devolvida com comentário. Tipo retirado não tem versão vigente: criar subdocumento desse tipo é
  recusado; os existentes continuam com a versão deles; tudo continua consultável.

## R8. Onde cada versão é usada

- **Decision**: formulário: subdocumentos com `template` = versão (lista e contagem); layout:
  vínculos `LayoutBinding` da versão (documentos distintos por tipo).

## R9. Permissões

- **Decision**: Qualidade/AR abre, altera, envia, descarta e pede retirada; Gestor de P&D aprova ou
  devolve revisões e retiradas; quem criou ou enviou a revisão não a aprova; Administrador não
  elabora nem aprova; os demais perfis consultam modelos, histórico e comparação. Negações passam
  por `deny_access` (trilha).
