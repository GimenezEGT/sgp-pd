# Contrato: telas e rotas (feature 013)

`<kind>` ∈ `form`, `layout`; `<pk>` é a versão do modelo. Negações por `deny_access`.

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/revisoes-modelos/` | GET | qualquer perfil | revisões em andamento (enviadas destacadas para o Gestor) e retiradas pedidas | — |
| `/revisoes-modelos/<kind>/<pk>/enviar/` | POST | QUALITY | motivo e impacto obrigatórios; recusa sem mudança ou com erro de regra | `templates.submitted` |
| `/revisoes-modelos/<kind>/<pk>/devolver/` | POST | RD_MANAGER | comentário obrigatório; volta a rascunho | `templates.returned` |
| `/revisoes-modelos/<kind>/<pk>/aprovar/` | GET, POST | RD_MANAGER (≠ quem elaborou ou enviou) | comparação com a vigente, senha de rede e vigência (imediata ou data futura); publica | `templates.approved`, `formtemplates.published`/`layouts.published`, `templates.became_current` |
| `/revisoes-modelos/<kind>/<pk>/descartar/` | POST | QUALITY | motivo obrigatório; só rascunho em elaboração | `templates.discarded` |
| `/revisoes-modelos/<kind>/<pk>/verificar/` | POST | QUALITY, RD_MANAGER | recalcula o resumo da versão publicada | `templates.verified` |
| `/revisoes-modelos/<kind>/<pk>/historico/` | GET | qualquer perfil | todas as versões da família com situação, etapas, pessoas, motivo, impacto, comentários e documentos iniciados | — |
| `/revisoes-modelos/<kind>/<pk>/comparar/` | GET | qualquer perfil | `?com=<pk>`: incluídos, retirados e alterados | — |
| `/revisoes-modelos/retirada/<pk>/pedir/` | POST | QUALITY | `<pk>` = versão vigente do tipo; motivo obrigatório | `templates.retirement_requested` |
| `/revisoes-modelos/retirada/<pk>/aprovar/` | POST | RD_MANAGER | `<pk>` = pedido; senha de rede | `templates.retirement_approved` |
| `/revisoes-modelos/retirada/<pk>/devolver/` | POST | RD_MANAGER | comentário obrigatório | `templates.retirement_returned` |
| `/modelos/<pk>/publicar/` (004), `/modelos-layout/<pk>/publicar/` (006) | — | — | retiradas: publicar é efeito da aprovação | — |
