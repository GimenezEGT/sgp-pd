"""Modelos versão 05 dos nove subdocumentos (docs/contexto/02-dicionario-documentos.md).

Os rótulos entre aspas no dicionário são os do formulário atual. Ajustes das decisões provisórias
do esclarecimento (spec 004): tópico 9 da Entrada "Classificação de Risco (RDC 830/2023)";
Análise Crítica com os 3 tópicos da capa; Saída numerada de 1 a 12 com os itens 6 e 7 só MAPA.
"""

REFERENCE = "PSG 20 - Pesquisa e Desenvolvimento de Produtos"
FORM_VERSION = 5


def rt(key, label, required=False, help_text=""):
    field = {"key": key, "type": "rich_text", "label": label}
    if required:
        field["required"] = True
    if help_text:
        field["help"] = help_text
    return field


def text(key, label, required=False, prefill=None):
    field = {"key": key, "type": "text", "label": label}
    if required:
        field["required"] = True
    if prefill:
        field["prefill"] = prefill
    return field


def vocab(key, label, vocabulary, multiple=False, required=False, prefill=None):
    field = {"key": key, "type": "vocabulary", "label": label, "vocabulary": vocabulary}
    if multiple:
        field["multiple"] = True
    if required:
        field["required"] = True
    if prefill:
        field["prefill"] = prefill
    return field


def ref(key, label, kind, multiple=True, required=False, filter_=None):
    field = {"key": key, "type": "reference", "label": label, "kind": kind, "multiple": multiple}
    if required:
        field["required"] = True
    if filter_:
        field["filter"] = filter_
    return field


def col(key, label, type_="text", **options):
    column = {"key": key, "label": label, "type": type_}
    column.update(options)
    return column


def table(key, label, columns, required=False):
    field = {"key": key, "type": "table", "label": label, "columns": columns}
    if required:
        field["required"] = True
    return field


def att(key, label, required=False):
    field = {"key": key, "type": "attachment", "label": label}
    if required:
        field["required"] = True
    return field


def topic(key, label, fields, **options):
    item = {"key": key, "label": label, "fields": fields}
    item.update(options)
    return item


REAGENTS = table(
    "reagentes",
    "Reagentes",
    [
        col("numero", "Número (R1…Rn)", required=True),
        col("nome", "Nome", required=True),
        col("composicao", "Composição resumida"),
    ],
    required=True,
)
PREPARATION = [
    table(
        "componentes",
        "Componentes por reagente",
        [
            col("reagente", "Reagente"),
            col("componente", "Componente", required=True),
            col("peso_molecular", "Peso molecular", "number"),
            col("mg_l", "mg/L", "number"),
            col("g_l", "g/L", "number"),
            col("mm", "mM", "number"),
            col("insumo", "Código do insumo", "reference", kind="insumos"),
        ],
    ),
    rt(
        "passos",
        "Modo de preparo",
        required=True,
        help_text="Passos numerados, densidade, armazenamento e validade de cada reagente.",
    ),
]

ENTRADA = {
    "cover": {"title": "Entrada de Projeto", "columns": 2},
    "topics": [
        topic(
            "amostras",
            "Amostras",
            [
                vocab("tipos", "Tipos de amostra", "tipo-amostra", multiple=True, required=True),
                rt("descricao", "Descrição"),
                table(
                    "coleta",
                    "Coleta, armazenamento e transporte por tipo de amostra",
                    [
                        col("tipo", "Tipo de amostra"),
                        col("coleta", "Coleta"),
                        col("armazenamento", "Armazenamento"),
                        col("transporte", "Transporte"),
                    ],
                ),
            ],
        ),
        topic(
            "funcionalidade",
            "Funcionalidade",
            [
                vocab("funcao", "Funcionalidade", "funcionalidade", multiple=True, required=True),
                rt("descricao", "Descrição"),
            ],
        ),
        topic(
            "apresentacoes",
            "Apresentações",
            [
                table(
                    "reagentes",
                    "Reagentes e apresentações",
                    [
                        col("reagente", "Reagente", required=True),
                        col("apresentacao", "Apresentação (volumes ou unidades)", required=True),
                    ],
                    required=True,
                )
            ],
            body_label="Apresentações e Composições",
        ),
        topic(
            "armazenamento",
            "Armazenamento",
            [
                table(
                    "faixas",
                    "Faixa de armazenamento por reagente",
                    [
                        col("reagente", "Reagente", required=True),
                        col(
                            "faixa",
                            "Faixa",
                            "vocabulary",
                            vocabulary="armazenamento",
                            required=True,
                        ),
                        col("apos_aberto", "Condição após aberto"),
                    ],
                    required=True,
                ),
                rt("descricao", "Descrição"),
            ],
        ),
        topic(
            "automacao",
            "Automação",
            [vocab("tipo", "Automação", "automacao", required=True), rt("descricao", "Descrição")],
        ),
        topic(
            "classificacao_uso",
            "Classificação de uso",
            [
                vocab("tipo", "Classificação de uso", "classificacao-uso", required=True),
                rt("descricao", "Descrição"),
            ],
        ),
        topic(
            "tipo_usuario",
            "Tipo de usuário",
            [
                vocab("tipo", "Usuário", "usuario", multiple=True, required=True),
                text("local_uso", "Local de uso"),
            ],
        ),
        topic(
            "filtros",
            "Filtros primário e secundário (se aplicável)",
            [
                vocab("primario", "Filtro primário", "filtro"),
                vocab("secundario", "Filtro secundário", "filtro"),
                table(
                    "alvos",
                    "Biologia molecular: alvo × detector × quencher",
                    [
                        col("alvo", "Alvo"),
                        col("detector", "Detector (fluoróforo)"),
                        col("quencher", "Quencher"),
                    ],
                ),
            ],
            allow_not_applicable=True,
        ),
        topic(
            "classificacao_risco",
            "Classificação de Risco (RDC 830/2023)",
            [
                vocab(
                    "classe",
                    "Classe de risco",
                    "classe-risco",
                    required=True,
                    prefill="project.risk_class",
                ),
                text(
                    "regra",
                    "Regra de classificação",
                    required=True,
                    prefill="project.classification_rule",
                ),
            ],
        ),
        topic(
            "requisitos_desempenho",
            "Requisitos de desempenho",
            [
                {
                    "key": "requisitos",
                    "type": "applicability",
                    "label": "Aplica / Não se aplica",
                    "vocabulary": "requisito-desempenho",
                    "required": True,
                }
            ],
        ),
        topic(
            "requisitos_regulatorios",
            "Requisitos regulatórios",
            [
                ref(
                    "normas",
                    "Normas técnicas (internacionais e nacionais)",
                    "normas",
                    required=True,
                )
            ],
        ),
        topic(
            "gerenciamento_risco",
            "Gerenciamento de risco",
            [att("matriz", "Matriz de risco (NBR ISO 14971)"), rt("descricao", "Descrição")],
        ),
        topic(
            "outros_dados",
            "Outros dados pertinentes",
            [
                rt(
                    "texto",
                    "Outros dados",
                    help_text="Metodologia, equipamentos, comercialização, fabricante, população alvo.",
                )
            ],
        ),
        topic(
            "formulario_opcional",
            "Formulário opcional de entrada",
            [
                text("analito", "Analito"),
                {"key": "data", "type": "date", "label": "Data"},
                vocab("classificacao_teste", "Classificação do teste", "classificacao-teste"),
                {
                    "key": "nota",
                    "type": "note",
                    "text": (
                        "Outras características do produto poderão ser avaliadas e discutidas "
                        "durante o desenvolvimento do projeto seguindo os requisitos da RDC "
                        "665/2022 e RDC 830/2023 da ANVISA, ISO 13485/2016"
                    ),
                },
            ],
            in_cover=False,
        ),
    ],
}

FORMULACAO = {
    "cover": {"title": "Elaboração de Formulação", "columns": 1},
    "topics": [
        topic(
            "nome_produto",
            "Nome do Produto",
            [text("produto", "Nome do produto", required=True, prefill="project.product_name")],
        ),
        topic("reagentes", "Nome e número do(s) Reagente(s)", [REAGENTS]),
        topic(
            "materias_primas",
            "Lista de matérias-primas utilizadas, conforme cadastro",
            [
                table(
                    "itens",
                    "Matérias-primas por reagente",
                    [
                        col("reagente", "Reagente"),
                        col(
                            "insumo", "Código do insumo", "reference", kind="insumos", required=True
                        ),
                    ],
                    required=True,
                )
            ],
        ),
        topic("modo_preparo", "Modo detalhado de preparo do(s) Reagente(s)", PREPARATION),
        topic(
            "complementares",
            "Informações complementares, quando aplicável",
            [rt("texto", "Informações complementares", required=True)],
            allow_not_applicable=True,
        ),
    ],
}

LOTE_PILOTO = {
    "cover": {"title": "Elaboração de Lote Piloto", "columns": 1},
    "topics": [
        topic(
            "lote",
            "Nome do Produto e Lote de Produção",
            [
                text("produto", "Nome do produto", required=True, prefill="project.product_name"),
                ref("lotes", "Lotes de produção", "lotes", required=True),
            ],
        ),
        topic(
            "reagentes",
            "Nome e número do(s) Reagente(s)",
            [REAGENTS],
            inherit={"subdocument": "formulacao", "topic": "reagentes"},
        ),
        topic(
            "materias_primas",
            "Lista de matérias-primas utilizadas, com código, lote e fabricante",
            [
                table(
                    "itens",
                    "Matérias-primas (código, lote e fabricante do cadastro)",
                    [
                        col(
                            "insumo", "Código do insumo", "reference", kind="insumos", required=True
                        ),
                        col("quantidade", "Quantidade"),
                    ],
                    required=True,
                )
            ],
        ),
        topic(
            "modo_preparo",
            "Modo detalhado de preparo do(s) Reagente(s)",
            PREPARATION,
            inherit={"subdocument": "formulacao", "topic": "modo_preparo"},
        ),
        topic(
            "responsavel",
            "Responsável pela Produção do lote piloto e local de fabricação",
            [
                {
                    "key": "lotes",
                    "type": "lots_production",
                    "label": "Responsável e local (cadastro dos lotes)",
                    "source_field": "lote.lotes",
                },
                rt("complemento", "Complemento"),
            ],
        ),
        topic(
            "complementares",
            "Informações complementares, quando aplicável",
            [
                rt("texto", "Informações complementares"),
                table(
                    "embalagem",
                    "Materiais de embalagem por apresentação",
                    [
                        col("reagente", "Reagente"),
                        col("volume", "Volume por apresentação"),
                        col("frasco", "Frasco"),
                        col("tampa", "Tampa"),
                        col("colmeia", "Colmeia"),
                        col("caixa", "Caixa"),
                        col("rotulo", "Rótulo"),
                    ],
                ),
            ],
            allow_not_applicable=True,
        ),
    ],
}

RAPD = {
    "cover": {
        "title": "Relatório de Avaliação de Produto em Desenvolvimento (RAPD)",
        "columns": 1,
    },
    "topics": [
        topic("formulacoes", "Formulações propostas", [rt("texto", "Formulações", required=True)]),
        topic(
            "testes_preliminares",
            "Testes e avaliações preliminares",
            [
                ref("paineis", "Painéis utilizados", "paineis"),
                ref("amostras", "Amostras", "amostras"),
                rt(
                    "texto",
                    "Testes e avaliações",
                    required=True,
                    help_text=(
                        "Origem e qualificação das amostras, armazenamento, equipamentos, "
                        "critérios, resultados e conclusão."
                    ),
                ),
            ],
        ),
        topic(
            "referencias",
            "Referências bibliográficas consultadas (quando aplicável)",
            [ref("referencias", "Referências", "referencias", required=True)],
            allow_not_applicable=True,
        ),
        topic(
            "exatidao",
            "Análise de Exatidão / Inexatidão (Comparativo de métodos)",
            [ref("kits", "Kits de referência", "kits"), rt("texto", "Análise", required=True)],
        ),
    ],
}

ANALISE_CRITICA = {
    "cover": {"title": "Análise Crítica", "columns": 1},
    "topics": [
        topic(
            "evolucao",
            "Análise sistemática da evolução do projeto (Cumprimento das atividades delineadas no planejamento)",
            [
                {
                    "key": "marcos",
                    "type": "derived_table",
                    "label": "Marcos planejados × realizados",
                    "source": "milestones",
                    "columns": [],
                },
                rt("texto", "Análise", required=True),
            ],
        ),
        topic(
            "comparacao",
            "Comparação dos resultados iniciais com os dados de entrada",
            [
                {
                    "key": "requisitos",
                    "type": "derived_table",
                    "label": "Requisitos da Entrada × resultados",
                    "source": "entry_requirements",
                    "columns": [col("resultado", "Resultado")],
                },
                rt("texto", "Comparação", required=True),
            ],
        ),
        topic(
            "complementares",
            "Dados complementares, quando aplicável",
            [rt("texto", "Dados complementares", required=True)],
            allow_not_applicable=True,
        ),
    ],
}

VALIDACAO = {
    "cover": {
        "title": "Validação do Produto",
        "columns": 1,
        "approver_label": "Gestor de P&D responsável pela Aprovação:",
    },
    "topics": [
        topic(
            "dados_desenvolvimento",
            "Dados de desenvolvimento incluindo estudo de precisão, linearidade, sensibilidade analítica, sensibilidade e especificidade clínica, interferentes, reatividade cruzada, efeito pró-zona (quando aplicável)",
            [
                {
                    "key": "pendencias",
                    "type": "derived_table",
                    "label": "Requisitos da Entrada e evidências",
                    "source": "entry_requirements",
                    "columns": [col("evidencia", "Evidência (estudo ou documento)", required=True)],
                },
                rt("texto", "Dados de desenvolvimento"),
            ],
        ),
        topic(
            "lotes",
            "Lotes utilizados no processo de validação",
            [ref("lotes", "Lotes", "lotes", required=True)],
        ),
        topic(
            "estabilidade",
            "Dados de Estabilidade Acelerada e Após Aberto",
            [rt("texto", "Estabilidade", required=True)],
        ),
        topic(
            "custo",
            "Estudo do custo do produto final",
            [
                table(
                    "custos",
                    "Custo do produto final",
                    [
                        col("item", "Item", required=True),
                        col("categoria", "Categoria (insumos, embalagem, mão de obra)"),
                        col("valor", "Valor (R$)", "number", sum=True, decimals=2, required=True),
                    ],
                    required=True,
                )
            ],
        ),
        topic(
            "outras",
            "Outras informações pertinentes",
            [
                rt("texto", "Outras informações"),
                table(
                    "validacao_externa",
                    "Validação externa",
                    [
                        col("laboratorio", "Laboratório parceiro"),
                        col("equipamento", "Equipamento"),
                        col("kit", "Kit de referência"),
                        col("metodologia", "Metodologia"),
                        col("resultados", "Resultados"),
                        col("conclusao", "Conclusão do cliente"),
                        col("observacoes", "Observações"),
                    ],
                ),
            ],
        ),
    ],
}

VERIFICACAO_FINAL = {
    "cover": {"title": "VERIFICAÇÃO FINAL DE VALIDAÇÃO", "columns": 1},
    "topics": [
        topic(
            "checklist",
            "CHECK LIST",
            [
                {
                    "key": "requisitos",
                    "type": "derived_table",
                    "label": "Requisitos de entrada × previsto × realizado × disposição",
                    "source": "entry_topics",
                    "rows": [
                        "amostras",
                        "funcionalidade",
                        "apresentacoes",
                        "armazenamento",
                        "automacao",
                        "classificacao_uso",
                        "tipo_usuario",
                        "filtros",
                        "classificacao_risco",
                        "requisitos_desempenho",
                        "outros_dados",
                    ],
                    "columns": [
                        col("realizado", "Realizado", required=True),
                        col(
                            "disposicao",
                            "Disposição (Aprovado, Reprovado ou Outros)",
                            "vocabulary",
                            vocabulary="disposicao",
                            required=True,
                        ),
                        col("justificativa", "Justificativa"),
                    ],
                    "justify_unless": {
                        "column": "disposicao",
                        "value": "aprovado",
                        "justification": "justificativa",
                    },
                }
            ],
        )
    ],
}

SAIDA = {
    "cover": {"title": "Saída de Projeto", "columns": 1},
    "topics": [
        topic(
            "lotes",
            "Lotes utilizados no processo de validação",
            [ref("lotes", "Lotes", "lotes", required=True)],
        ),
        topic(
            "prazos_validade",
            "Prazos de validade do produto",
            [
                table(
                    "prazos",
                    "Prazos de validade",
                    [
                        col("reagente", "Reagente ou produto", required=True),
                        col("prazo", "Prazo de validade", required=True),
                        col(
                            "condicao",
                            "Condição de armazenamento",
                            "vocabulary",
                            vocabulary="armazenamento",
                        ),
                    ],
                    required=True,
                )
            ],
        ),
        topic(
            "novas_materias_primas",
            "Cadastro de nova(s) matéria(s)-prima(s), quando aplicável (anexar certificado)",
            [
                ref(
                    "insumos",
                    "Matérias-primas novas para a empresa",
                    "insumos",
                    required=True,
                    filter_={"material_type": "raw", "new_to_company": True},
                )
            ],
            allow_not_applicable=True,
        ),
        topic(
            "novos_materiais_embalagem",
            "Cadastro de novo(s) material(is) de embalagem(ns), quando aplicável (especificar)",
            [
                ref(
                    "insumos",
                    "Materiais de embalagem novos para a empresa",
                    "insumos",
                    required=True,
                    filter_={"material_type": "packaging", "new_to_company": True},
                ),
                rt("especificacao", "Especificação"),
            ],
            allow_not_applicable=True,
        ),
        topic(
            "matriz_risco",
            "Matriz de Gerenciamento de Risco",
            [att("matriz", "Matriz de gerenciamento de risco", required=True)],
        ),
        topic(
            "lotes_piloto_producao",
            "Solicitação de lote(s) piloto(s) para Produção, quando aplicável (MAPA)",
            [rt("texto", "Solicitação", required=True)],
            allow_not_applicable=True,
            regulatory_body="MAPA",
        ),
        topic(
            "testes_cq",
            "Teste(s) preliminar(es) do(s) lote(s) piloto(s) pelo Controle de Qualidade, quando aplicável (MAPA)",
            [rt("texto", "Testes do Controle de Qualidade", required=True)],
            allow_not_applicable=True,
            regulatory_body="MAPA",
        ),
        topic(
            "envio_lotes",
            "Dados de envio de lote(s) piloto(s) para clientes ou assessores externos, se aplicável",
            [
                table(
                    "envios",
                    "Envios de lotes piloto",
                    [
                        col("destino", "Destino", required=True),
                        col("lote", "Lote", "reference", kind="lotes", required=True),
                        col("data", "Data", "date"),
                        col("retorno", "Retorno"),
                    ],
                    required=True,
                )
            ],
            allow_not_applicable=True,
        ),
        topic(
            "prazo_transferencia",
            "Prazo de Transferência (Imediata ou não)",
            [
                vocab("prazo", "Prazo de transferência", "prazo-transferencia", required=True),
                text("condicao", "Condição (ex.: após registro)"),
            ],
        ),
        topic(
            "formulario_validacao",
            "Formulário de Validação de Produto em anexo",
            [
                {
                    "key": "validacao",
                    "type": "subdocuments",
                    "label": "Validação do Produto do projeto",
                    "required": True,
                }
            ],
        ),
        topic(
            "documentos",
            "Instrução de Uso, FISPQ, Dossiê Técnico, modelo de rótulos e Bula Prática (quando aplicável)",
            [att("anexos", "Documentos", required=True)],
            allow_not_applicable=True,
        ),
        topic(
            "setores",
            "Setores que receberão a Transferência:",
            [
                vocab(
                    "setores",
                    "Setores de transferência",
                    "setor-transferencia",
                    multiple=True,
                    required=True,
                )
            ],
        ),
    ],
}

ALTERACAO = {
    "cover": {"title": "Alteração de Projeto", "columns": 1, "change_versions": True},
    "topics": [
        topic(
            "justificativa",
            "Justificativa de alteração",
            [rt("texto", "Justificativa (lista de alterações)", required=True)],
        ),
        topic(
            "requisitos_entrada",
            "Requisitos de entrada (quando aplicável)",
            [
                {
                    "key": "afetados",
                    "type": "entry_topics",
                    "label": "Tópicos da Entrada afetados",
                    "required": True,
                },
                rt("novo_conteudo", "Novo conteúdo"),
            ],
            allow_not_applicable=True,
        ),
        topic("outros_dados", "Outros dados pertinentes", [rt("texto", "Outros dados")]),
        topic(
            "analise_risco",
            "Análise de risco (RDC 665/2022, art. 60)",
            [rt("texto", "Avaliação de risco"), att("anexos", "Anexos da análise de risco")],
            in_cover=False,
            require_any=["texto", "anexos"],
        ),
        topic(
            "subdocumentos_afetados",
            "Subdocumentos afetados",
            [
                {
                    "key": "subdocumentos",
                    "type": "subdocuments",
                    "label": "Subdocumentos que ficam marcados para revisão",
                }
            ],
            in_cover=False,
        ),
    ],
}

DEFINITIONS = {
    "entrada": ENTRADA,
    "formulacao": FORMULACAO,
    "lote-piloto": LOTE_PILOTO,
    "rapd": RAPD,
    "analise-critica": ANALISE_CRITICA,
    "validacao": VALIDACAO,
    "verificacao-final": VERIFICACAO_FINAL,
    "saida": SAIDA,
    "alteracao": ALTERACAO,
}


def load(apps, valid_from, published_at) -> None:
    """Publica a versão 05 de cada tipo (usado pela migração de dados)."""
    Term = apps.get_model("vocab", "Term")
    FormTemplate = apps.get_model("formtemplates", "FormTemplate")
    for code, definition in DEFINITIONS.items():
        term = Term.objects.get(vocabulary__code="tipo-subdocumento", code=code)
        FormTemplate.objects.get_or_create(
            subdocument_type=term,
            form_version=FORM_VERSION,
            defaults={
                "reference": REFERENCE,
                "valid_from": valid_from,
                "status": "published",
                "definition": definition,
                "published_at": published_at,
                "published_note": "Carga inicial da versão 05 (docs/contexto/02-dicionario-documentos.md)",
            },
        )
