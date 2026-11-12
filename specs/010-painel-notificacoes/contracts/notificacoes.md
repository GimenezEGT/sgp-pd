# Contrato: notificações por e-mail (feature 010)

| Tipo | Quando | Destinatários | Pode desligar |
| --- | --- | --- | --- |
| `returned` – Documento devolvido | imediato, no evento `signatures.returned` ou `projects.returned` | elaborador da versão (ou quem criou o subdocumento); líder no TAP, no Plano e no projeto | sim |
| `approved` – Documento aprovado | imediato, no evento `signatures.approved` ou `projects.approved` | elaborador da versão e líder do projeto | sim |
| `stalled` – Documento parado na revisão | resumo diário | elaborador de documento em revisão há mais de `REVIEW_ALERT_DAYS` dias | sim |
| `pending_signature` – Assinatura pendente | resumo diário | Gestor de P&D e delegados (documentos em revisão além do prazo); autor de entrada do caderno aberta além de `NOTEBOOK_SIGN_DAYS`; líder do projeto de entrada relevante aguardando testemunha além do mesmo prazo | não |

Conteúdo do e-mail (português, sem dados financeiros): assunto "[SGP-P&D] <tipo>: <registro>",
projeto, registro, quem e quando, comentário da devolução quando houver e o endereço da tela
(`SITE_URL`). O resumo diário lista todos os itens vencidos da pessoa num só e-mail.

Situações: `pending` (na fila), `sent`, `failed` (depois de 3 tentativas), `skipped` (preferência
desligada ou pessoa sem e-mail). Eventos: `notifications.sent`, `notifications.failed`,
`notifications.skipped`.
