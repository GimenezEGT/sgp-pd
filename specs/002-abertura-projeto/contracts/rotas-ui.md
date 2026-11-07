# Contrato: telas e rotas (feature 002)

Regras gerais: toda rota de projeto confere `can_access_project` (403 registrado quando falha);
edição só do líder e só em `draft` ou `returned` (TAP e plano) ou em `open` (equipe e data
realizada dos marcos).

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/projetos/` | GET | qualquer perfil | lista com filtros `status`, `lider`, `produto`; só projetos acessíveis; coluna de custo só com permissão financeira | — |
| `/projetos/novo/` | GET, POST | PROJECT_LEADER, RD_MANAGER | cria rascunho com dados do produto | `projects.created` |
| `/projetos/<id>/` | GET | acesso ao projeto | produto, TAP, plano (financeiros mascarados sem permissão), equipe, marcos, pendências e histórico de decisões | — |
| `/projetos/<id>/editar/` | GET, POST | líder; `draft`/`returned` | dados do produto | `projects.updated` |
| `/projetos/<id>/tap/` | GET, POST | líder; `draft`/`returned` | TAP | `projects.charter_updated` |
| `/projetos/<id>/plano-de-negocios/` | GET, POST | líder; `draft`/`returned` | Plano de Negócios e previsões | `projects.business_plan_updated` |
| `/projetos/<id>/equipe/incluir/` | POST | líder | pessoa, papel, início | `projects.member_added` |
| `/projetos/<id>/equipe/<membro>/encerrar/` | POST | líder | fim da vigência e motivo | `projects.member_ended` |
| `/projetos/<id>/marcos/incluir/` | POST | líder; `draft`/`returned` | subdocumento, descrição, data planejada | `projects.milestone_added` |
| `/projetos/<id>/marcos/<marco>/` | POST | líder | data planejada (`draft`/`returned`) ou data realizada (`open`) | `projects.milestone_updated` |
| `/projetos/<id>/marcos/<marco>/cancelar/` | POST | líder; `draft`/`returned` | motivo | `projects.milestone_canceled` |
| `/projetos/<id>/submeter/` | POST | líder | recusa com pendências | `projects.submitted` |
| `/projetos/<id>/aprovar/` | POST | RD_MANAGER ≠ líder | código, versão 01, acesso da equipe | `projects.approved` |
| `/projetos/<id>/devolver/` | POST | RD_MANAGER ≠ líder | comentário obrigatório | `projects.returned` |

A trilha de auditoria (`/auditoria/`) passa a oferecer no filtro `projeto` a lista de projetos
(código ou, sem código, nome).
