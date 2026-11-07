# Contrato: eventos de auditoria (feature 003)

Nos eventos de cadastro, `object_id` é a linhagem (UUID) e `new_value` traz `versao` e `registro`
(id da linha), para que o histórico junte todas as versões. Lotes levam `project_id`.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `catalog.created` | Cadastro criado | — → dados da versão 1 |
| `catalog.updated` | Cadastro corrigido | campos alterados (mesma versão) |
| `catalog.versioned` | Nova versão de cadastro | campos alterados; motivo em `reason` |
| `catalog.locked` | Cadastro bloqueado por documento assinado | — → `{versao}`; motivo em `reason` |
| `catalog.deactivated` / `catalog.reactivated` | Cadastro desativado / reativado | `{ativo}`; motivo em `reason` |
| `catalog.import_previewed` | Importação de insumos pré-visualizada | — → `{arquivo, linhas, validas, rejeitadas}` |
| `catalog.import_confirmed` | Importação de insumos confirmada | — → `{criados, rejeitadas}` |
| `catalog.import_rejections_exported` | Relatório de rejeições exportado | — → `{arquivo, linhas}` |
| `files.uploaded` | Arquivo anexado | — → `{nome, tipo, tamanho, sha256}` |
| `files.integrity_failed` | Arquivo com resumo divergente | `{sha256 esperado}` → `{sha256 lido}` |
| `vocab.term_created` / `vocab.term_updated` | Termo incluído / alterado na lista | rótulo; versão da lista |
| `vocab.term_deactivated` / `vocab.term_reactivated` | Termo desativado / reativado | `{ativo}` |
