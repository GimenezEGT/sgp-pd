# Contrato: definição do modelo de formulário (JSON)

```json
{
  "cover": {"title": "Entrada de Projeto", "columns": 2, "approver_label": "Gestor de P&D:"},
  "topics": [
    {
      "key": "amostras",
      "label": "Amostras",
      "body_label": "",
      "in_cover": true,
      "allow_not_applicable": false,
      "regulatory_body": "",
      "help": "",
      "fields": [
        {"key": "tipos", "type": "vocabulary", "label": "Tipos de amostra",
         "vocabulary": "tipo-amostra", "multiple": true, "required": true},
        {"key": "descricao", "type": "rich_text", "label": "Descrição"},
        {"key": "coleta", "type": "table", "label": "Coleta, armazenamento e transporte",
         "columns": [{"key": "tipo", "label": "Tipo de amostra", "type": "text"}]}
      ]
    }
  ]
}
```

| Chave do tópico | Regra |
| --- | --- |
| `key` | `^[a-z][a-z0-9_]{0,39}$`, única no modelo |
| `label` | rótulo da capa, único no modelo (sem diferença de caixa) |
| `body_label` | título no corpo, quando diferente da capa |
| `in_cover` | se entra na lista "ESTE RELATÓRIO DEVE CONTER" (padrão sim) |
| `allow_not_applicable` | se aceita "não aplicável" com justificativa |
| `regulatory_body` | vazio ou `MAPA`: tópico só aparece e só é exigido em projetos desse órgão |

| Tipo de campo | Valor gravado | Opções |
| --- | --- | --- |
| `rich_text` | texto (parágrafos e "- " para listas) | `required` |
| `text` | texto curto (até 500) | `required`, `prefill` (`project.product_name`, `project.title`, `project.classification_rule`) |
| `list` | lista de textos | `required` |
| `table` | lista de linhas `{coluna: valor}` | `columns` (`text`, `number`, `date`, `reference` com `kind`), `sum` por coluna numérica |
| `vocabulary` | código do termo ou lista | `vocabulary`, `multiple`, `prefill` (`project.risk_class`) |
| `reference` | id da versão do cadastro ou lista | `kind` (`lotes`, `insumos`, `kits`, `amostras`, `paineis`, `normas`, `referencias`), `multiple`, `filter` (`material_type`, `new_to_company`) |
| `attachment` | lista de ids de arquivo | `required` |
| `date` | data ISO | |
| `number` | decimal em texto | `decimals` |
| `applicability` | lista `{codigo, aplica, criterio, justificativa}` | `vocabulary` (`requisito-desempenho`) |
| `derived_table` | linhas derivadas + colunas editáveis | `source` (`entry_topics`, `entry_requirements`, `milestones`), `rows` (tópicos da Entrada), `columns` editáveis, `justify_unless` |
| `entry_topics` | lista de chaves de tópico da Entrada | — |
| `subdocuments` | lista de ids de subdocumento do projeto | — |
| `lots_production` | (só exibição) responsável e local dos lotes de `source_field` | `source_field` |
| `note` | (só exibição) texto fixo | `text` |

Regras de publicação: definição válida no schema, chaves e rótulos únicos, listas controladas e
tipos de cadastro existentes, `rows` de `entry_topics` existentes no modelo vigente da Entrada.
