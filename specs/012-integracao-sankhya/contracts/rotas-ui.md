# Contrato: telas, rotas e eventos (feature 012)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/integracoes/` | GET | Administrador (TI) | fila: situação, tentativas, último erro, próxima tentativa; filtros por situação e registro | — |
| `/integracoes/mensagens/<id>/reprocessar/` | POST | Administrador (TI) | reenvia com a mesma chave | `integration.reprocessed`, `integration.sent` ou `integration.failed` |
| `/integracoes/exportar/` | GET | Administrador (TI) | `registro` e `formato` (`csv`, `xlsx`, `json`) | `integration.exported` |
| `/integracoes/mapeamento/` | GET, POST | Administrador (TI) | YAML validado, nova versão | `integration.mapping_published` |
| `/integracoes/produto/` | GET | qualquer perfil | `codigo` → descrição, unidade e situação no Sankhya, ou aviso de não conferido (trecho HTMX) | — |
