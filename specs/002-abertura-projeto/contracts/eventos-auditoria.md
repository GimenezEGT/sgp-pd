# Contrato: eventos de auditoria (feature 002)

Todos levam `project_id`, o que permite filtrar a trilha por projeto.

| Código | Rótulo | Valor anterior → novo |
| --- | --- | --- |
| `projects.created` | Projeto criado | — → dados do produto |
| `projects.updated` | Dados do produto alterados | campos alterados |
| `projects.charter_updated` | TAP alterado | campos alterados |
| `projects.business_plan_updated` | Plano de Negócios alterado | campos alterados (financeiros mascarados para quem não tem permissão) |
| `projects.member_added` | Membro incluído na equipe | — → `{pessoa, papel, inicio}` |
| `projects.member_ended` | Vigência de membro encerrada | `{fim: null}` → `{fim}`; motivo em `reason` |
| `projects.milestone_added` | Marco incluído | — → `{subdocumento, data_planejada}` |
| `projects.milestone_updated` | Marco alterado | campos alterados |
| `projects.milestone_canceled` | Marco cancelado | motivo em `reason` |
| `projects.submitted` | Projeto submetido | `{situacao}` anterior → `submitted` |
| `projects.returned` | Projeto devolvido | `submitted` → `returned`; comentário em `reason` |
| `projects.approved` | Projeto aprovado e aberto | `submitted` → `{situacao: open, codigo, versao}` |

Campos sensíveis registrados no mascaramento da trilha para `projects.business_plan_updated`:
`total_cost`, `forecasts`, `forecast_total`, `competitor_price_min`, `competitor_price_max`,
`max_production_cost`, `sale_price_min`, `sale_price_max`, `annual_sales_tests`.
