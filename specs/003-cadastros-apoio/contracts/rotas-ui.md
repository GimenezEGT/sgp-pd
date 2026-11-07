# Contrato: telas e rotas (feature 003)

`<tipo>` ∈ `lotes`, `insumos`, `kits`, `amostras`, `paineis`, `normas`, `referencias`.
Editores = Analista/Pesquisador, Líder de projeto, Gestor de P&D e Qualidade/AR. Lotes também
exigem acesso ao projeto.

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/cadastros/` | GET | qualquer perfil | atalhos dos cadastros | — |
| `/cadastros/<tipo>/` | GET | qualquer perfil (lotes: projetos acessíveis) | lista com busca (`q`), filtro `projeto` em lotes e `inativos=1` | — |
| `/cadastros/<tipo>/buscar/` | GET | qualquer perfil | fragmento HTML com até 20 resultados ativos e vigentes (`q`) | — |
| `/cadastros/<tipo>/novo/` | GET, POST | editores | cria a versão 1 | `catalog.created`, `files.uploaded` |
| `/cadastros/<tipo>/<id>/` | GET | qualquer perfil (lote: acesso ao projeto) | dados da versão, alertas, todas as versões e eventos | — |
| `/cadastros/<tipo>/<id>/editar/` | GET, POST | editores | corrige no lugar ou cria nova versão (motivo obrigatório se bloqueado) | `catalog.updated` ou `catalog.versioned` |
| `/cadastros/<tipo>/<id>/situacao/` | POST | editores | desativa ou reativa com motivo | `catalog.deactivated`, `catalog.reactivated` |
| `/cadastros/insumos/importar/` | GET, POST | editores | envio da planilha → pré-visualização | `catalog.import_previewed` |
| `/cadastros/insumos/importar/<lote>/` | GET, POST | editores | pré-visualização e confirmação | `catalog.import_confirmed`, `catalog.created` |
| `/cadastros/insumos/importar/<lote>/rejeicoes.csv` | GET | editores | relatório das linhas rejeitadas | — |
| `/cadastros/insumos/modelo.csv` | GET | editores | planilha modelo com o cabeçalho do contrato | — |
| `/arquivos/<id>/` | GET | quem pode ver o registro dono do arquivo (certificado: qualquer perfil; planilha importada: editores); sem dono conhecido, negado | entrega o arquivo depois de conferir o SHA-256 | `files.integrity_failed` (falha) |
| `/listas/` | GET | QUALITY | listas controladas e versões | — |
| `/listas/<codigo>/` | GET, POST | QUALITY | termos; POST inclui termo | `vocab.term_created` |
| `/listas/termos/<id>/` | POST | QUALITY | corrige rótulo, desativa ou reativa, sempre com motivo | `vocab.term_updated`, `vocab.term_deactivated`, `vocab.term_reactivated` |
