# Contrato: telas, rotas e eventos (feature 008)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/caderno/` | GET | qualquer perfil | busca nos projetos acessíveis: palavra, projeto, lote, amostra, pesquisador, período, situação, aberta há mais de N dias; 20 por página, "carregar mais" (HTMX) | — |
| `/projetos/<id>/caderno/` | GET | acesso ao projeto | linha do tempo do caderno do projeto com os mesmos filtros | — |
| `/projetos/<id>/caderno/nova/` | GET, POST | editores do projeto aberto | título, modelo (opcional) e relevância; nasce aberta com número e hora do servidor | `notebook.created` |
| `/caderno/entradas/<id>/` | GET | acesso ao projeto | conteúdo, materiais, anexos, assinaturas (com conferência do resumo), adendos, vínculos | — |
| `/caderno/entradas/<id>/editar/` | GET, POST | autor, entrada aberta | grava textos sanitizados (controle de versão da linha) | `notebook.updated` |
| `/caderno/entradas/<id>/materiais/` | POST | autor, entrada aberta | tipo e código; código inexistente recusado | `notebook.material_added` |
| `/caderno/materiais/<id>/retirar/` | POST | autor, entrada aberta | retirada lógica | `notebook.material_removed` |
| `/caderno/entradas/<id>/anexos/` | POST | autor, entrada aberta | arquivo (PDF, PNG, JPEG, CSV, XLSX; limite da 003); com `Accept: application/json`, imagem colada no texto devolve `{"url", "name"}` | `files.uploaded`, `notebook.attachment_added` |
| `/caderno/anexos/<id>/retirar/` | POST | autor, entrada aberta | retirada lógica | `notebook.attachment_removed` |
| `/caderno/entradas/<id>/relevancia/` | POST | autor ou Gestor de P&D, sem testemunha | marca ou desmarca relevante | `notebook.relevance_changed` |
| `/caderno/entradas/<id>/assinar/` | POST | autor, entrada aberta | senha de rede (005); bloqueia | `notebook.signed` (falhas: `signatures.failed`, `signatures.blocked`) |
| `/caderno/entradas/<id>/testemunhar/` | POST | acesso ao projeto, não autor; entrada relevante e assinada | senha de rede; resumo tem de conferir | `notebook.witnessed` |
| `/caderno/entradas/<id>/adendos/` | POST | editores do projeto; entrada assinada | texto e senha; adendo assinado e imutável | `notebook.addendum_added` |
| `/caderno/entradas/<id>/vinculos/` | POST | editores do projeto | subdocumento, lote ou estudo do mesmo projeto | `notebook.linked` |
| `/caderno/vinculos/<id>/retirar/` | POST | editores do projeto | motivo obrigatório; promoção não é retirada | `notebook.unlinked` |
| `/caderno/entradas/<id>/promover/` | GET, POST | editores do projeto | anexo CSV/XLSX + estudo em elaboração + mapeamento → pré-visualização → confirmação | `notebook.promoted`, `studies.imported` |
| `/caderno/modelos/` | GET, POST | Qualidade/AR e Gestor de P&D | lista e cria modelo de entrada | `notebook.template_created` |
| `/caderno/modelos/<id>/` | GET, POST | Qualidade/AR e Gestor de P&D | altera (nova versão com motivo) | `notebook.template_updated` |
| `/caderno/modelos/<id>/desativar/` | POST | Qualidade/AR e Gestor de P&D | tira da escolha; entradas antigas não mudam | `notebook.template_deactivated` |

Negações: `auth.permission_denied` (`deny_access`). O subdocumento, o estudo e o lote mostram as
entradas ligadas.
