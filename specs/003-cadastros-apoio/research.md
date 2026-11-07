# Research: Cadastros de apoio

## R1. Versões numa tabela por cadastro

- **Decision**: cada linha da tabela é uma versão. Campos comuns (`VersionedRecord`): `lineage`
  (UUID do cadastro ao longo das versões), `version`, `is_current`, `is_active`, `locked_at`,
  `locked_by`, `lock_reason`, `version_reason`, autor e datas. Referências de outros documentos
  apontam para a linha (a versão). Correção: se a versão vigente não está bloqueada, altera a
  própria linha (trilha com valor anterior e novo); se está bloqueada, exige motivo, marca a linha
  atual como não vigente e cria a linha `version+1`. Índices únicos parciais (`WHERE is_current`)
  garantem código único entre os vigentes.
- **Rationale**: atende "corrigir lote assinado cria nova versão e o documento assinado continua
  com o valor original" sem tabelas duplicadas por cadastro; o papel de banco não tem DELETE.
- **Alternatives considered**: tabela de identidade + tabela de versões por cadastro (14
  tabelas, mesma semântica); JSON genérico por tipo (perde integridade e consulta).

## R2. Bloqueio

- **Decision**: `lock_version(row, by, reason)` grava `locked_at/by/reason` e o evento
  `catalog.locked`; bloquear um painel bloqueia as versões de amostras dele. A feature 005 chama o
  bloqueio ao assinar documentos que referenciam cadastros. Código de lote e de insumo não muda em
  versão nova depois do bloqueio.

## R3. Arquivos com SHA-256

- **Decision**: app `files` com `StoredFile` (*append-only*: nome original, tipo, tamanho, SHA-256,
  quem e quando). O conteúdo fica em `MEDIA_ROOT/aa/bb/<sha256>` (endereçado pelo conteúdo); a
  leitura recalcula o SHA-256 e recusa o arquivo divergente, gravando `files.integrity_failed`.
  Tipos aceitos por assinatura do arquivo (PDF `%PDF`, PNG, JPEG) e extensão; tamanho máximo
  `FILE_MAX_MB` (20).
- **Rationale**: plano pede "hash SHA-256 conferido na leitura"; reaproveitado em 004, 006 e 008.

## R4. Importação de insumos

- **Decision**: `ImportBatch` guarda o arquivo enviado, o resultado da validação de cada linha
  (JSONB) e a situação (`preview`, `confirmed`). CSV em UTF-8 (com ou sem BOM) ou Latin-1,
  separador `;` ou `,` detectado; XLSX pela primeira planilha (openpyxl `read_only`). Cabeçalhos
  comparados sem acento e sem diferença de caixa (contrato `importacao-insumos.md`). A confirmação
  cria as linhas válidas que continuam válidas (código ainda livre) e grava um evento por insumo e
  um da importação. O relatório de rejeições é um CSV gerado a partir das linhas rejeitadas.

## R5. Busca enquanto digita

- **Decision**: extensão `pg_trgm` e índices GIN `gin_trgm_ops` nos campos de busca; `icontains`
  em código e descrição; campo de busca com HTMX (`hx-trigger="keyup changed delay:300ms"`) e
  endpoint `/cadastros/<tipo>/buscar/` que devolve fragmento HTML para os formulários das features
  seguintes.

## R6. LGPD nas amostras

- **Decision**: não existe campo de identificação do paciente. O identificador interno segue
  `^[A-Za-z0-9][A-Za-z0-9._/-]{0,29}$` e precisa ter ao menos um dígito (um nome de pessoa não
  passa). Os textos (origem, caracterização, detalhe do armazenamento) recusam CPF, e-mail,
  telefone e as palavras "paciente" e "nome".
- **Rationale**: critério de pronto "nenhum campo de amostra aceita nome de paciente"; dados
  mínimos decididos no clarify.

## R7. Telas genéricas

- **Decision**: `catalog/kinds.py` registra cada tipo (modelo, formulário, rótulos, colunas,
  campos de busca, se pertence a projeto); listas, formulários, detalhe com histórico, desativação
  e busca são views únicas parametrizadas pelo tipo da URL.

## R8. Listas controladas

- **Decision**: telas em `/listas/` só para Qualidade/AR: incluir termo (código gerado do rótulo),
  corrigir rótulo, desativar e reativar; cada mudança incrementa `Vocabulary.version` e grava
  evento `vocab.*`. Carga inicial nova: `tipo-amostra` e `armazenamento` (05-vocabularios).

## R9. Nomes do plano

cadastros → `catalog`; Lote → `Lot`; Insumo → `Material`; KitReferencia → `ReferenceKit`;
Amostra → `Sample`; Painel → `Panel`; Norma → `Standard`; Referencia → `BibliographicReference`.
