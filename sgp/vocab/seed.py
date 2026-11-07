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

ALL_SEEDS = {**SEED, **SAMPLE_SEED}


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
