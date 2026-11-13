# Research: Versionamento do documento final do projeto

## R1. Onde a versão nasce

- Decision: chamada explícita de `sgp.fulldoc.versioning.register` dentro de `approve` (uma parte) e
  de `approve_project` (TAP e Plano juntos, uma versão), na mesma transação, depois do congelamento
  da versão aprovada; numeração com `select_for_update` na linha do projeto.
- Rationale: a aprovação do projeto produz dois eventos `signatures.approved`; um sinal da trilha
  geraria duas versões. A chamada explícita garante uma versão por aprovação e atomicidade.
- Alternatives considered: sinal `post_save` da trilha (como na 012), com agrupamento por transação.

## R2. Composição e resumo

- Decision: composição = para cada parte na ordem do documento (TAP, Plano, subdocumentos na ordem
  da 009), a versão aprovada mais recente: tipo, identificador, nome da parte, versão, data da
  aprovação e resumo do conteúdo aprovado (`ApprovedVersion.content_hash`); resumo SHA-256 do JSON
  canônico da composição.
- Rationale: as versões aprovadas congeladas (005/006) são a fonte única do conteúdo do documento.

## R3. Recomposição

- Decision: `ensure_current` antes de gerar o documento completo: se a composição vigente difere da
  última versão registrada (aprovações gravadas por fora do fluxo, como cargas ou testes), registra a
  versão com o motivo "recomposição" e a diferença como mudança.
- Rationale: FR-010; o documento gerado sempre aponta para uma versão registrada.

## R4. Reconstrução do histórico

- Decision: migração `0005` chama `sgp.fulldoc.history.rebuild(apps)` com os modelos históricos:
  por projeto, as aprovações em ordem de data; aprovações do mesmo aprovador com menos de 5
  segundos de diferença (TAP e Plano na aprovação do projeto) formam uma versão; versões marcadas
  como reconstruídas, com a data e o aprovador da aprovação. A mesma função é testada com o registro
  de modelos atual.
- Evento na trilha (FR-005): a trilha não aceita data passada, então a migração não grava evento;
  logo depois das migrações (sinal `post_migrate` do app, com o banco na última migração e os
  modelos atuais), `history.record_missing_events` grava `fulldoc.version_created` para cada
  versão reconstruída que ainda não tem evento: ator "sistema", motivo "Reconstrução a partir das
  aprovações registradas (feature 016)" e, no valor, a data e o aprovador originais; sem repetir.
  Encontrado na conferência da pilha real (0 eventos depois da migração) e corrigido.
- Rationale: resposta do usuário no esclarecimento (reconstruir).

## R5. Documento gerado

- Decision: `FullDocument.final_version` (nulo para os gerados antes); capa com "VERSÃO DO DOCUMENTO
  FINAL" e "VERSÃO DO PROJETO"; nome do arquivo e código de verificação pela versão do documento
  final; o número entra no resumo de reaproveitamento, então um documento gerado antes da 016 não é
  reaproveitado para uma versão registrada; quadro "Versões do documento final" depois do quadro de
  versões das partes.

## R6. Histórico das partes

- Decision: etiqueta de template `historico_de_versoes tipo objeto` (app da 009) com versão,
  situação (Vigente, Substituída, Rascunho, Em revisão, Devolvido), motivo e autor da abertura
  (evento `signatures.new_version`; a versão 01 usa a criação da parte), aprovação (versão aprovada)
  e as versões do documento final em que a versão entrou; incluída nas telas do subdocumento e do
  projeto (TAP e Plano).
