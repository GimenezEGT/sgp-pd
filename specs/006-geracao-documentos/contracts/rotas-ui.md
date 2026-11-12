# Contrato: telas e rotas (feature 006)

`<tipo>` ∈ `subdocument`, `charter`, `business_plan`. "Vê o documento" = acesso ao projeto
(feature 001); no Plano de Negócios, também permissão de dados financeiros (002). Toda negação usa
`deny_access` (`auth.permission_denied`).

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/documentos/<tipo>/<id>/` | GET | vê o documento | botões "Gerar PDF" e "Gerar DOCX", pedidos em andamento e histórico de gerações (quem, quando, formato, versão, modelos, resumos, igual à primeira) | — |
| `/documentos/<tipo>/<id>/gerar/` | POST | vê o documento | `formato` = `pdf` ou `docx`; cria ou reaproveita o pedido e enfileira; responde com o painel do pedido (HTMX) ou redireciona | `documents.requested` |
| `/documentos/pedidos/<id>/` | GET | vê o documento do pedido | situação do pedido; enquanto na fila ou gerando, o painel se recarrega a cada 2 s | — |
| `/documentos/arquivos/<id>/baixar/` | GET | vê o documento | confere a integridade e entrega o arquivo arquivado | `documents.downloaded` (ou `files.integrity_failed` com página de erro 409) |
| `/documentos/verificar/` | GET | qualquer pessoa autenticada com perfil | formulário do código; com `?codigo=`, mostra o resultado (dados do projeto e download só com acesso) | `documents.verification_lookup` |
| `/modelos-layout/` | GET | qualquer perfil | modelos de layout por alvo, com versão vigente e rascunho | — |
| `/modelos-layout/<id>/` | GET | qualquer perfil | parâmetros, logotipo e situação da versão | — |
| `/modelos-layout/<id>/nova-versao/` | POST | QUALITY | rascunho com o conteúdo da versão | `layouts.draft_created` |
| `/modelos-layout/<id>/editar/` | GET, POST | QUALITY | formulário dos parâmetros e envio de logotipo (PNG ou JPEG); só rascunho | `layouts.draft_updated` |
| `/modelos-layout/<id>/previa/` | GET | QUALITY | PDF de pré-visualização com dados de exemplo e marca d'água; não arquivado | — |
| `/modelos-layout/<id>/publicar/` | POST | QUALITY | valida e publica com a vigência do rascunho | `layouts.published` |
| `/modelos-layout/<id>/logotipo/` | GET | qualquer perfil | imagem do logotipo da versão | — |

Integrações nas telas existentes:

- Detalhe do subdocumento (004) e do projeto (002): link "Documentos gerados" para
  `/documentos/<tipo>/<id>/`.
- Aprovação (005): congela o conteúdo de renderização na mesma transação (`documents.frozen`).
- Criação de subdocumento (004), nova versão (005) e criação de projeto (002): vinculam o layout
  vigente à versão que começa.
