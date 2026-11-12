"""Dados de exemplo da pré-visualização do modelo de layout (fictícios; não são arquivados)."""

from sgp.formtemplates.schema import numbered_topics

from .content import FORMAT, TITLES

DASH = chr(0x2013)
EXAMPLE_ROWS = 30


def _example_sections(first_label: str) -> list[dict]:
    rows = [
        [f"{index:02d}", f"Item de exemplo {index:02d}", f"{index * 1.5:.2f}".replace(".", ",")]
        for index in range(1, EXAMPLE_ROWS + 1)
    ]
    return [
        {
            "number": 1,
            "label": first_label,
            "not_applicable": False,
            "justification": "",
            "blocks": [
                {"kind": "values", "label": "Campo de exemplo", "lines": ["Valor de exemplo"]},
                {
                    "kind": "rich",
                    "label": "Texto de exemplo",
                    "items": [
                        {"p": "Parágrafo de exemplo para conferir fonte, tamanho e espaçamento."},
                        {"ul": ["Primeiro item de exemplo", "Segundo item de exemplo"]},
                    ],
                },
                {
                    "kind": "table",
                    "number": "Tabela 01",
                    "label": "Tabela de exemplo",
                    "columns": ["Nº", "Descrição", "Valor"],
                    "rows": rows,
                    "totals": None,
                    "notes": [],
                },
            ],
        },
        {
            "number": 2,
            "label": "Tópico não aplicável de exemplo",
            "not_applicable": True,
            "justification": "Justificativa de exemplo.",
            "blocks": [],
        },
    ]


def sample_content(target: str) -> dict:
    base = {
        "format": FORMAT,
        "kind": target,
        "product": "NOME DO PRODUTO",
        "project_code": "PD-AAAA-NNN",
        "version": "01",
        "changed_version": None,
        "new_version": None,
        "form_template": None,
        "optional_form": None,
        "signatures": [],
        "approved_on": "",
    }
    if target != "subdocument":
        return {
            **base,
            "type": target,
            "title": TITLES[target],
            "form_footer": "",
            "cover": {
                "columns": 1,
                "topics": [],
                "approver_label": "Aprovado (Nome/Função):",
                "author_label": "Elaborado (Nome/Função):",
                "checklist": None,
                "sectors": None,
            },
            "sections": _example_sections("Seção de exemplo"),
        }
    from sgp.formtemplates.services import current_template
    from sgp.vocab.models import get_term

    template = current_template(get_term("tipo-subdocumento", "entrada"))
    if template is not None:
        topics = [[n, t["label"]] for n, t in numbered_topics(template.definition) if n]
        title, footer = template.cover.get("title", ""), template.footer
        columns = template.cover.get("columns", 1)
    else:
        topics, title, columns = [[1, "Tópico de exemplo"]], "Subdocumento de exemplo", 1
        footer = f"Formulário Versão: NN. Referência: referência do formulário {DASH} exemplo"
    return {
        **base,
        "type": "entrada",
        "title": title,
        "form_footer": footer,
        "cover": {
            "columns": columns,
            "topics": topics,
            "approver_label": "Gestor de P&D:",
            "author_label": "Analista Responsável (Nome/Função):",
            "checklist": None,
            "sectors": None,
        },
        "sections": _example_sections(topics[0][1]),
    }
