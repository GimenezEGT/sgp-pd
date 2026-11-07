# Research: Revisão, versões e assinatura eletrônica

## R1. Documento genérico com adaptadores

- **Decision**: `sgp/signatures/documents.py` registra adaptadores para `subdocument`, `charter`
  (TAP) e `business_plan` (Plano de Negócios). Cada um informa: projeto, rótulo, versão, situação,
  conteúdo canônico, anexos, completude, referências a bloquear, quem edita e o que fazer na
  aprovação. O serviço de assinatura é um só.
- **Alternatives considered**: tabela "documento" única para os três (reescrever 002 e 004).

## R2. Situações

- **Decision**: Subdocument ganha `in_review` e `returned`; TAP e Plano ganham `doc_status` e
  `doc_version` (migração). Editável: rascunho e devolvido. "Substituída" é a situação de uma versão
  aprovada quando existe outra aprovada mais nova (calculada em `ApprovedVersion`).
- No projeto (002): submeter põe TAP e Plano em revisão (assinatura "elaborado" do líder em cada);
  devolver põe os dois em devolvido; aprovar exige a assinatura "aprovado" nos dois. Depois do
  projeto aberto, nova versão de TAP ou Plano segue o ciclo do próprio documento.

## R3. Conteúdo canônico e resumo

- **Decision**: `canonical_json` = `to_jsonable` da trilha (sem ponto flutuante) + `json.dumps`
  com chaves ordenadas, separadores compactos e UTF-8; SHA-256 em hexadecimal. O conteúdo inclui
  tipo, versão, projeto, modelo usado (subdocumento), dados e `{id, nome, sha256}` dos anexos
  (contrato `conteudo-canonico.md`).

## R4. Assinatura e reautenticação

- **Decision**: `django.contrib.auth.authenticate` com o backend LDAP da 001 e o `username` da
  pessoa logada; precisa devolver a mesma pessoa. A senha não é guardada nem registrada. AD
  indisponível (sinal `ldap_error`) recusa sem contar falha. `SignatureAttempt` (append-only)
  guarda cada tentativa; na terceira falha seguida nasce `SignatureLock` (expira em
  `SIGNATURE_LOCK_MINUTES`, padrão 15) e o evento `signatures.blocked`.
- Assinatura (`Signature`, append-only): tipo e id do documento, versão, resumo, significado,
  pessoa, nome e função no momento, data e hora do servidor, delegação.

## R5. Aprovação

- **Decision**: exige situação "em revisão", assinatura "elaborado" da versão com o mesmo resumo do
  conteúdo atual, aprovador ≠ elaborador, Gestor de P&D ou delegado vigente com acesso ao
  projeto. Grava a assinatura "aprovado", o `ApprovedVersion` (conteúdo e resumo), muda a situação,
  bloqueia os cadastros referenciados e aplica os efeitos do tipo (Alteração de Projeto da 004).
  A aprovação provisória da 004 deixa de ser rota pública.

## R6. Imutabilidade e verificação

- **Decision**: `ApprovedVersion` e `Signature` são `AppendOnlyModel` com gatilho; o papel da
  aplicação não tem UPDATE/DELETE. A verificação recalcula o resumo de cada versão, confere as
  assinaturas, compara o conteúdo atual do documento aprovado com o congelado e confere os anexos
  pelo SHA-256 (feature 003); grava `signatures.verified` com o resultado.

## R7. Delegação e prazo

- **Decision**: `ApprovalDelegation` (`ProtectedModel`, encerramento registrado): delegador
  Gestor de P&D, delegado com perfil Gestor, Líder ou Qualidade, período ≤ 30 dias, motivo.
  Fila de revisão em `/assinaturas/fila/` com dias em revisão; atrasado acima de
  `REVIEW_ALERT_DAYS` (padrão 5).
