# Contrato: dados financeiros (FR-010)

| Dado | Campo | Onde aparece |
| --- | --- | --- |
| Custo total do projeto | `total_cost` | detalhe, edição do plano, lista (coluna Custo), trilha |
| Retorno esperado ano 1–5 e total | `AnnualForecast.amount`, `forecast_total` | detalhe, edição, trilha |
| Preço por teste dos concorrentes (faixa) | `competitor_price_min/max` | detalhe, edição, trilha |
| Custo máximo de produção | `max_production_cost` | detalhe, edição, trilha |
| Preço de venda previsto (faixa) | `sale_price_min/max` | detalhe, edição, trilha |
| Venda anual prevista (testes/ano) | `annual_sales_tests` | detalhe, edição, trilha |

Quem vê: perfil Gestor de P&D, o líder do projeto e perfis listados em
`FINANCIAL_DATA_PROFILES` (vazio por padrão). Para os demais:

- detalhe do projeto e lista: o valor é trocado por "Restrito"; a coluna Custo não aparece;
- edição do plano (`/projetos/<id>/plano-de-negocios/`): só o líder; os demais recebem 403;
- trilha (tela e CSV/XLSX): as chaves acima nos valores anterior e novo aparecem como
  `"[restrito]"`; o hash não muda, porque a máscara é só de apresentação.
