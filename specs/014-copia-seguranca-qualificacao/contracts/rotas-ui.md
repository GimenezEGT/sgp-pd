# Contrato: telas, rotas e eventos (feature 014)

| Rota | Método | Quem | Comportamento | Eventos |
| --- | --- | --- | --- | --- |
| `/operacao/` | GET | Administrador, Garantia da Qualidade | painel: cópias (situação, tamanho, arquivos, resumo do manifesto, remoção), testes de restauração com as conferências, qualificações com o resultado e o relatório; avisos de cópia atrasada (mais de 26 horas) e de teste de restauração atrasado (mais de 32 dias) ou reprovado | — |
| `/operacao/copias/executar/` | POST | Administrador | enfileira uma cópia manual (recusa se houver uma em andamento) | `operations.backup_requested` |
| `/operacao/restauracao/executar/` | POST | Administrador | enfileira o teste de restauração da cópia mais recente | `operations.restore_requested` |
| `/operacao/qualificacao/instalacao/` | POST | Administrador | enfileira a qualificação de instalação (canal "tela") | `operations.qualification_requested` |
| `/operacao/qualificacao/operacao/` | POST | Administrador, Garantia da Qualidade | enfileira a qualificação de operação (canal "tela") | `operations.qualification_requested` |
| `/operacao/qualificacao/<id>/relatorio/` | GET | Administrador, Garantia da Qualidade | baixa o PDF do relatório (resumo conferido na leitura) | `operations.report_downloaded` |
| `/operacao/revisao-de-acessos/` | GET | Administrador, Garantia da Qualidade | `formato` = `csv` (";", UTF-8) ou `xlsx`: pessoa, nome, e-mail, conta ativa, perfis ativos (desde, concedido por), papéis por projeto, último acesso | `operations.access_review_exported` |

Nenhuma rota baixa cópias de segurança nem restaura sobre o banco em uso (FR-009, FR-010).

Menu: item "Operação e validação" para Administrador e Garantia da Qualidade.

Eventos das tarefas (ator: sistema, ou quem pediu): `operations.backup_completed`,
`operations.backup_failed`, `operations.backup_removed`, `operations.restore_tested` (com
`aprovado`), `operations.backup_stale`, `operations.qualification_executed` (com o resultado e o
resumo do relatório).
