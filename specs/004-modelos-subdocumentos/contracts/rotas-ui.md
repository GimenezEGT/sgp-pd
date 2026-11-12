# Contrato: telas e rotas (feature 004)

Editores de subdocumento = membros da equipe com perfil Analista/Pesquisador ou Líder de projeto e
o Gestor de P&D, em projeto aberto. Consulta = quem acessa o projeto.

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/modelos/` | GET | qualquer perfil | modelos por tipo, com versões e vigência | — |
| `/modelos/<id>/` | GET | qualquer perfil | capa, tópicos numerados e campos | — |
| `/modelos/<id>/nova-versao/` | POST | QUALITY | rascunho da versão seguinte (cópia) | `formtemplates.draft_created` |
| `/modelos/<id>/editar/` | GET, POST | QUALITY | metadados e definição do rascunho | `formtemplates.draft_updated` |
| `/modelos/<id>/publicar/` | POST | QUALITY | valida e publica | `formtemplates.published` |
| `/projetos/<id>/subdocumentos/` | GET | acesso ao projeto | lista com situação, ordem do fluxo e pendências | — |
| `/projetos/<id>/subdocumentos/novo/` | GET, POST | editores | cria; fora da ordem pede autorização | `subdocuments.created` |
| `/projetos/<id>/subdocumentos/autorizar/` | POST | RD_MANAGER | autoriza criação fora da ordem, com motivo | `subdocuments.flow_authorized` |
| `/subdocumentos/<id>/` | GET | acesso ao projeto | documento com numeração, tabelas e anexos | — |
| `/subdocumentos/<id>/editar/` | GET, POST | editores (rascunho) | formulário do modelo usado | `subdocuments.updated`, `files.uploaded` |
| `/subdocumentos/<id>/linha/` | GET | editores | fragmento HTMX com nova linha de tabela | — |
| `/subdocumentos/<id>/atualizar-derivados/` | POST | editores | recompõe linhas derivadas da Entrada aprovada | `subdocuments.derived_refreshed` |
| `/subdocumentos/<id>/migrar/` | POST | RD_MANAGER | migra rascunho para o modelo vigente, com motivo | `subdocuments.template_migrated` |
| `/subdocumentos/<id>/aprovar/` | POST | RD_MANAGER (≠ criador) | confere completude e aprova (provisório até a 005) | `subdocuments.approved`, `catalog.locked`, `projects.version_changed` |
| `/arquivos/<id>/` (feature 003) | GET | acesso ao projeto do subdocumento que anexou o arquivo (política registrada pela app) | anexo conferido | `files.integrity_failed` (falha) |
