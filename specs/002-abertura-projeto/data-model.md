# Data Model: Abertura de projeto — TAP e Plano de Negócios

Todos os modelos são `ProtectedModel` (sem exclusão), exceto `ProjectDecision` (*append-only*).
Datas/horas em UTC; dinheiro `Decimal(14,2)` ≥ 0.

## vocab.Vocabulary / vocab.Term — listas controladas

| Campo | Tipo | Regras |
| --- | --- | --- |
| Vocabulary.code | slug, único | `tecnologia`, `tipo-subdocumento` |
| Vocabulary.name / version | texto / inteiro | versão sobe a cada mudança de termos |
| Term.vocabulary | FK | |
| Term.code / label | slug / texto(200) | único por vocabulário |
| Term.position / is_active | inteiro / booleano | termo inativo não aparece em novos registros |

Carga inicial: `tecnologia` = bioquimica "Bioquímica", imunologia "Imunologia",
biologia-molecular "Biologia molecular", outras "Outras"; `tipo-subdocumento` = entrada "Entrada
de Projeto", formulacao "Elaboração de Formulação", lote-piloto "Elaboração de Lote Piloto", rapd
"Relatório de Avaliação de Produto em Desenvolvimento (RAPD)", analise-critica "Análise Crítica",
validacao "Validação do Produto", verificacao-final "Verificação Final de Validação", saida "Saída
de Projeto", alteracao "Alteração de Projeto".

## projects.Project — "Projeto"

| Campo | Tipo | Regras |
| --- | --- | --- |
| title | texto(200) | "nome do projeto", obrigatório |
| product_name / product_family | texto(200) / texto(200, opcional) | |
| technology | FK Term (`tecnologia`) | obrigatório |
| regulatory_body | `ANVISA` ou `MAPA` | obrigatório |
| risk_class | `I`–`IV` ou vazio | obrigatório só em ANVISA |
| classification_rule | texto(200) | obrigatória só em ANVISA (ex.: "Regra 5, item d") |
| regime (calculado) | — | Notificação (I, II), Registro (III, IV), vazio em MAPA |
| leader | FK User | quem cria com perfil Líder de projeto |
| status | `draft`, `submitted`, `returned`, `open` | máquina de estados (research R1) |
| code | texto(20), único, nulo até a aprovação | PD-AAAA-NNN |
| version | inteiro, nulo até a aprovação | 1 na aprovação; exibido "01" |
| created_by / created_at / updated_at | | |
| submitted_at / approved_at / approved_by | | |
| row_version | inteiro | controle otimista |

## projects.ProjectCharter — "TAP" (1:1 com Project)

| Campo | Tipo |
| --- | --- |
| justification, objective | texto |
| scope_included, scope_excluded, deliverables, assumptions, constraints | JSONB lista de textos |
| risks | JSONB lista de `{risco, impacto, resposta}` |
| stakeholders | JSONB lista de `{nome_area, interesse}` |
| updated_at, updated_by, row_version | |

## projects.BusinessPlan — "Plano de Negócios" (1:1 com Project)

| Campo | Tipo | Financeiro |
| --- | --- | --- |
| plan_date | data | |
| objective, description, target_market | texto | |
| total_cost | Decimal(14,2) | sim |
| execution_months / execution_end_date | inteiro / data (ao menos um) | |
| competitors, competitor_presentations | JSONB lista de textos | |
| competitor_price_min / competitor_price_max | Decimal(14,2) (mín ≤ máx) | sim |
| max_production_cost | Decimal(14,2) | sim |
| sale_price_min / sale_price_max | Decimal(14,2) (mín ≤ máx) | sim |
| annual_sales_tests | inteiro ≥ 0 | sim |
| factory_structure, production_team, quality_control | texto | |
| forecast_total (calculado) | soma das previsões | sim |
| updated_at, updated_by, row_version | | |

## projects.AnnualForecast — "Previsão anual"

| Campo | Tipo | Regras |
| --- | --- | --- |
| business_plan | FK | |
| year_index | 1 a 5 | único por plano; as 5 linhas nascem com o plano |
| amount | Decimal(14,2) ≥ 0, nulo | receita líquida prevista; financeiro |

## projects.ProjectMember — "Membro do projeto"

| Campo | Tipo | Regras |
| --- | --- | --- |
| project / user | FK | no máximo um vínculo ativo por pessoa e projeto |
| role | texto(200) | papel no projeto |
| start_date / end_date | data / data nula | vigência; encerrar exige motivo |
| end_reason, added_by, added_at, ended_by, ended_at | | |

## projects.Milestone — "Marco"

| Campo | Tipo | Regras |
| --- | --- | --- |
| project | FK | |
| subdocument_type | FK Term (`tipo-subdocumento`) | |
| description | texto(200, opcional) | |
| planned_date / actual_date | data / data nula | realizada não pode ser futura nem anterior à criação do projeto |
| canceled_at, canceled_by, cancel_reason | | cancelamento com motivo |
| created_by, created_at | | |

## projects.ProjectDecision — "Decisão do projeto" (*append-only*)

| Campo | Tipo |
| --- | --- |
| project, actor | FK |
| action | `submitted`, `returned`, `approved` |
| occurred_at | data/hora |
| comment | texto (obrigatório em `returned`) |

## projects.ProjectCodeSequence

| Campo | Tipo |
| --- | --- |
| year | inteiro, PK |
| last_value | inteiro |
