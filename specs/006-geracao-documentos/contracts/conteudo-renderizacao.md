# Contrato: conteúdo de renderização (feature 006)

Montado por `sgp/documents/content.py` a partir do documento; é o que o HTML do PDF e o DOCX
desenham. Na aprovação, é congelado em `FrozenRendering` com as assinaturas e a data de aprovação;
rascunhos usam a montagem do momento. Todo texto já vem resolvido (rótulos de lista, valores de
cadastro na versão referenciada, números com vírgula decimal, datas dd/mm/aaaa); nada é digitado
no gerador.

```json
{
  "format": 1,
  "kind": "subdocument",
  "type": "entrada",
  "title": "Entrada de Projeto",
  "product": "NOME DO PRODUTO",
  "project_code": "PD-2026-001",
  "version": "01",
  "changed_version": null,
  "new_version": null,
  "form_footer": "Formulário Versão: 05. Referência: PSG 20 - Pesquisa e Desenvolvimento de Produtos",
  "cover": {
    "columns": 2,
    "topics": [[1, "Amostras"], [2, "Funcionalidade"]],
    "approver_label": "Gestor de P&D:",
    "checklist": null,
    "sectors": null
  },
  "sections": [
    {
      "number": 1,
      "label": "Amostras",
      "not_applicable": false,
      "justification": "",
      "blocks": [
        {"kind": "values", "label": "Tipos de amostra", "lines": ["Soro", "Plasma"]},
        {"kind": "rich", "label": "Descrição", "items": [{"p": "texto"}, {"ul": ["a", "b"]}]},
        {"kind": "table", "number": "Tabela 01", "label": "Coleta…", "columns": ["…"], "rows": [["…"]], "totals": null, "notes": []},
        {"kind": "files", "label": "Matriz de risco", "files": [{"name": "matriz.pdf", "sha256": "…"}]},
        {"kind": "note", "text": "…"},
        {"kind": "empty", "label": "Campo", "text": "(não preenchido)"}
      ]
    }
  ],
  "optional_form": null,
  "signatures": [
    {"meaning": "Elaborado", "name": "…", "title": "…", "at": "08/11/2026 14:32", "delegation": ""}
  ],
  "approved_on": "08/11/2026"
}
```

Regras:

- `sections` segue a numeração da 004 (`numbering.visible_topics`) e a numeração de tabelas
  (`numbering.table_numbers`); tópico sem número (formulário opcional) vai para `optional_form`.
- Variante `checklist`: o tópico da tabela CHECK LIST sai em `cover.checklist` (colunas
  "REQUISITOS DE ENTRADA", "PREVISTO", "REALIZADO", "DISPOSIÇÃO (APROVADO, REPROVADO OU OUTROS)")
  e não se repete em `sections`.
- Variante `sectors`: `cover.sectors` lista todos os setores da lista `setor-transferencia` em duas
  colunas, com `checked` nos escolhidos.
- TAP e Plano de Negócios: `type` = `charter` ou `business_plan`, `form_footer` vazio, `cover.topics`
  vazio e `sections` com os campos da 002 na ordem do formulário.
- `signatures`: assinaturas da versão em ordem de data; o bloco da capa usa a "Elaborado" mais
  recente válida e a "Aprovado"; as "Revisado" só aparecem na relação final.
- Resumo: SHA-256 do JSON canônico da feature 005 (`signatures.canonical.content_hash`).
