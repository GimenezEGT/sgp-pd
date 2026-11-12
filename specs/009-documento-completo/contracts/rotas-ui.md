# Contrato: telas, rotas e eventos (feature 009)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/projetos/<id>/documento-completo/` | GET | acesso ao projeto | pendências, opções (caderno completo ou resumido, histórico completo de versões), pedido em andamento com progresso e documentos já gerados | — |
| `/projetos/<id>/documento-completo/` | POST | líder do projeto e Gestor de P&D | cria o pedido assíncrono (um ativo por projeto) | `fulldoc.requested`; depois `fulldoc.generated`, `fulldoc.reused` ou `fulldoc.failed` |
| `/documentos-completos/pedidos/<id>/` | GET | acesso ao projeto | trecho de progresso (HTMX, a cada 2 s enquanto ativo) | — |
| `/documentos-completos/<id>/baixar/` | GET | acesso ao projeto; com dados financeiros, só quem os vê | PDF com conferência do resumo | `fulldoc.downloaded` |

A verificação pública da 006 (`/documentos/verificar/`) passa a reconhecer também o código do
documento completo oficial. Negações: `auth.permission_denied` (`deny_access`).
