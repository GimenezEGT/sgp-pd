# Contrato: telas e rotas (feature 005)

`<tipo>` ∈ `subdocument`, `charter`, `business_plan`. Toda assinatura pede a senha de rede.

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/assinaturas/<tipo>/<id>/enviar/` | GET, POST | editores do documento | confere completude, assina "elaborado", põe em revisão | `signatures.submitted`, `signatures.signed` |
| `/assinaturas/<tipo>/<id>/revisar/` | POST | acesso ao projeto, nem elaborador nem aprovador | assina "revisado" | `signatures.signed` |
| `/assinaturas/<tipo>/<id>/aprovar/` | GET, POST | Gestor de P&D ou delegado (≠ elaborador) | assina "aprovado", congela a versão | `signatures.signed`, `signatures.approved`, `catalog.locked` |
| `/assinaturas/<tipo>/<id>/devolver/` | POST | Gestor de P&D ou delegado | comentário obrigatório; volta a editável | `signatures.returned` |
| `/assinaturas/<tipo>/<id>/nova-versao/` | POST | editores | motivo obrigatório; versão seguinte em rascunho | `signatures.new_version` |
| `/assinaturas/<tipo>/<id>/verificar/` | POST | acesso ao projeto | recalcula e compara | `signatures.verified` |
| `/assinaturas/<tipo>/<id>/versoes/<n>/` | GET | acesso ao projeto (Plano: dados financeiros só com permissão) | conteúdo e assinaturas da versão | — |
| `/assinaturas/fila/` | GET | Gestor de P&D ou delegado vigente | documentos em revisão e dias de espera | — |
| `/assinaturas/delegacoes/` | GET, POST | RD_MANAGER | lista e cria delegação | `signatures.delegation_created` |
| `/assinaturas/delegacoes/<id>/encerrar/` | POST | RD_MANAGER | encerra com motivo | `signatures.delegation_ended` |
| `/projetos/<id>/submeter/` (002) | POST | líder | agora pede a senha e assina TAP e Plano | `projects.submitted`, `signatures.signed` |
| `/projetos/<id>/aprovar/` (002) | POST | RD_MANAGER | agora pede a senha e assina TAP e Plano | `projects.approved`, `signatures.approved` |
| `/subdocumentos/<id>/aprovar/` (004) | — | — | retirada: a aprovação passa pela assinatura | — |
