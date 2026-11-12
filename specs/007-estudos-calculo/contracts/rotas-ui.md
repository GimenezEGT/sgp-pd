# Contrato: telas, rotas e eventos (feature 007)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/projetos/<id>/estudos/` | GET, POST | acesso ao projeto; criar: editores do projeto | lista e cria estudo (tipo, título, vínculo ao tópico, arredondamento, IC, corte) | `studies.created` |
| `/estudos/<id>/` | GET | acesso ao projeto | configuração, critérios, linhas, resultados com conclusão | — |
| `/estudos/<id>/editar/` | POST | editores, estudo em elaboração | grava critérios (só sem linhas) e linhas; recalcula | `studies.updated`, `studies.criteria_set` |
| `/estudos/<id>/nao-aplicavel/` | POST | editores | justificativa obrigatória; sem linhas | `studies.not_applicable` |
| `/estudos/<id>/importar/` | GET, POST | editores | arquivo + equipamento + mapeamento → pré-visualização assinada → confirmação | `studies.imported`, `studies.mapping_saved` |
| `/estudos/<id>/nova-versao/` | POST | editores, estudo bloqueado | motivo obrigatório; copia critérios e linhas | `studies.new_version` |

Na aprovação do subdocumento (005): `studies.locked` para cada estudo vinculado.
