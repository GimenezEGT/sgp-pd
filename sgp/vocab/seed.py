"""Carga inicial das listas controladas (docs/contexto/05-vocabularios.md e 02-dicionario)."""

MINUS = chr(0x2212)

SEED = {
    "tecnologia": (
        "Tecnologia do produto",
        [
            ("bioquimica", "Bioquímica"),
            ("imunologia", "Imunologia"),
            ("biologia-molecular", "Biologia molecular"),
            ("outras", "Outras"),
        ],
    ),
    "tipo-subdocumento": (
        "Tipos de subdocumento do PSG 20",
        [
            ("entrada", "Entrada de Projeto"),
            ("formulacao", "Elaboração de Formulação"),
            ("lote-piloto", "Elaboração de Lote Piloto"),
            ("rapd", "Relatório de Avaliação de Produto em Desenvolvimento (RAPD)"),
            ("analise-critica", "Análise Crítica"),
            ("validacao", "Validação do Produto"),
            ("verificacao-final", "Verificação Final de Validação"),
            ("saida", "Saída de Projeto"),
            ("alteracao", "Alteração de Projeto"),
        ],
    ),
}


# Feature 003: listas das amostras (docs/contexto/05-vocabularios.md).
SAMPLE_SEED = {
    "tipo-amostra": (
        "Tipos de amostra",
        [
            ("soro", "Soro"),
            ("plasma", "Plasma"),
            ("sangue-total", "Sangue total"),
            ("urina", "Urina"),
            ("liquor", "Líquor"),
            ("dna", "DNA"),
            ("rna", "RNA"),
            ("outros", "Outros"),
        ],
    ),
    "armazenamento": (
        "Condições de armazenamento",
        [
            ("menos-20", MINUS + "20 °C"),
            ("2-8", "2 a 8 °C"),
            ("2-30", "2 a 30 °C"),
            ("15-30", "15 a 30 °C"),
            ("37", "37 °C"),
        ],
    ),
}

# Feature 004: listas do formulário de entrada, da Verificação Final e da Saída
# (docs/contexto/05-vocabularios.md).
SUBDOCUMENT_SEED = {
    "funcionalidade": (
        "Funcionalidade",
        [
            ("triagem", "Triagem"),
            ("monitoramento", "Monitoramento"),
            ("diagnostico", "Diagnóstico"),
            ("auxilio-diagnostico", "Auxílio diagnóstico"),
        ],
    ),
    "classificacao-teste": (
        "Classificação do teste",
        [
            ("quantitativo", "Quantitativo"),
            ("qualitativo", "Qualitativo"),
            ("semi-quantitativo", "Semi-quantitativo"),
            ("semi-qualitativo", "Semi-qualitativo"),
            ("nao-aplicavel", "Não aplicável"),
        ],
    ),
    "automacao": (
        "Automação",
        [
            ("manual", "Manual"),
            ("automatico", "Automático"),
            ("semiautomatico", "Semiautomático"),
            ("outros", "Outros (especificar)"),
        ],
    ),
    "usuario": ("Usuário", [("profissional", "Profissional"), ("leigo", "Leigo")]),
    "classificacao-uso": ("Classificação de uso", [("unico", "Único"), ("multiplo", "Múltiplo")]),
    "filtro": (
        "Filtros primário e secundário",
        [("na", "N/A")]
        + [
            (f"{nm}nm", f"{nm} nm")
            for nm in (280, 340, 380, 405, 412, 450, 505, 546, 570, 605, 660, 700, 740, 800)
        ]
        + [("outro", "Outro (especificar)")],
    ),
    "requisito-desempenho": (
        "Requisitos de desempenho (Aplica / Não se aplica)",
        [
            ("metodologia", "Metodologia"),
            ("prazo-validade", "Prazo de validade"),
            ("estabilidade-transporte", "Estabilidade de transporte"),
            ("estabilidade-on-board", "Estabilidade on board / pós aberto"),
            ("exatidao", "Exatidão"),
            ("precisao", "Precisão"),
            ("sensibilidade-analitica", "Sensibilidade analítica"),
            ("especificidade-analitica", "Especificidade analítica"),
            ("linearidade", "Linearidade"),
            ("cut-off", "Cut-off"),
            ("sensibilidade-clinica", "Sensibilidade clínica"),
            ("especificidade-clinica", "Especificidade clínica"),
            ("rastreabilidade", "Rastreabilidade"),
            ("efeito-prozona", "Efeito prozona"),
            ("gerenciamento-risco", "Gerenciamento de risco"),
            ("outros", "Outros"),
        ],
    ),
    "classe-risco": (
        "Classe de risco (RDC 830/2023)",
        [("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV")],
    ),
    "disposicao": (
        "Disposição (Verificação Final)",
        [("aprovado", "Aprovado"), ("reprovado", "Reprovado"), ("outros", "Outros (justificar)")],
    ),
    "prazo-transferencia": (
        "Prazo de transferência",
        [("imediata", "Imediata"), ("nao-imediata", "Não imediata (com condição)")],
    ),
    "setor-transferencia": (
        "Setores de transferência",
        [
            ("producao-i", "Produção I"),
            ("supply-chain", "Supply Chain"),
            ("controle-qualidade", "Controle de Qualidade"),
            ("sac", "SAC"),
            ("comercial", "Comercial"),
            ("marketing", "Marketing"),
            ("sop", "S&OP"),
        ],
    ),
}

ALL_SEEDS = {**SEED, **SAMPLE_SEED, **SUBDOCUMENT_SEED}


def load(apps, seed: dict) -> None:
    Vocabulary = apps.get_model("vocab", "Vocabulary")
    Term = apps.get_model("vocab", "Term")
    for code, (name, terms) in seed.items():
        vocabulary, _ = Vocabulary.objects.get_or_create(code=code, defaults={"name": name})
        for position, (term_code, label) in enumerate(terms, start=1):
            Term.objects.get_or_create(
                vocabulary=vocabulary,
                code=term_code,
                defaults={"label": label, "position": position},
            )
