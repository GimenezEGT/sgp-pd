"""Carga inicial das listas controladas (docs/contexto/05-vocabularios.md e 02-dicionario)."""

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
