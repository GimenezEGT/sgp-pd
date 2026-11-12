# Contrato: telas, rotas e eventos (feature 010)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/painel/` | GET | qualquer perfil | quatro totais (para quem aprova) e carteira dos projetos acessíveis; `?atualizar=1` ignora o cache | — |
| `/painel/exportar/` | GET | qualquer perfil | XLSX com as colunas da carteira (custo e retorno só com permissão) | `dashboard.exported` |
| `/projetos/<id>/linha-do-tempo/` | GET | acesso ao projeto | marcos planejados e eventos do projeto por categoria, paginados | — |
| `/pendencias/` | GET | qualquer perfil | minhas pendências: aprovar (fila da 005), devolvidos, caderno a assinar, testemunhas | — |
| `/notificacoes/preferencias/` | GET, POST | qualquer perfil | liga ou desliga devolução, aprovação e documento parado; assinatura pendente sempre ligada | `notifications.preference_changed` |

A fila do Gestor de P&D continua em `/assinaturas/fila/` (feature 005). Negações:
`auth.permission_denied` (`deny_access`).
