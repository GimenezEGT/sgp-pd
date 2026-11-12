"""Perfis de cálculo por tipo de estudo (contrato perfis-calculo.md da feature 007).

O código do tipo (lista controlada `tipo-estudo`) escolhe o perfil: colunas usadas, métricas
calculadas e métricas aceitas no critério. Sem Django: recebe linhas e configuração, devolve dados.
"""

from collections import OrderedDict
from dataclasses import dataclass

from . import stats

FINE = {"r2", "correlacao", "inclinacao", "intercepto"}
INTEGER = {"n", "deteccoes"}
LABELS = {
    "n": "Medidas",
    "media": "Média",
    "dp": "Desvio-padrão",
    "cv": "CV%",
    "diferenca_media": "Diferença média",
    "dp_diferencas": "DP das diferenças",
    "inclinacao": "Inclinação",
    "intercepto": "Intercepto",
    "r2": "R²",
    "correlacao": "Correlação (r)",
    "sensibilidade": "Sensibilidade (%)",
    "especificidade": "Especificidade (%)",
    "concordancia": "Concordância (%)",
    "deteccao": "Detecção (%)",
    "deteccoes": "Detecções",
    "menor_nivel_detectado": "Menor nível detectado",
    "desvio_max": "Maior desvio absoluto (%)",
    "variacao_max": "Maior variação absoluta (%)",
}
COLUMN_LABELS = {
    "amostra": "Amostra",
    "lote": "Lote",
    "kit": "Kit de referência",
    "dia": "Dia",
    "corrida": "Corrida",
    "replicata": "Replicata",
    "grupo": "Nível/grupo",
    "x": "Referência/nível (x)",
    "y": "Medido (y)",
    "esperado": "Esperado",
    "obtido": "Obtido",
}
COMPARISONS = {"lt": "<", "le": "≤", "gt": ">", "ge": "≥"}
QUALITATIVE = ("pos", "neg")


@dataclass(frozen=True)
class Profile:
    code: str
    kind: str
    columns: tuple
    criteria: tuple
    required: tuple
    group_by: str = ""


def _profile(code, kind, columns, criteria, required, group_by=""):
    return code, Profile(code, kind, columns, criteria, required, group_by)


DESCRIPTIVE = ("media", "dp", "cv")
REGRESSION = ("inclinacao", "intercepto", "r2")
PROPORTIONS = ("sensibilidade", "especificidade", "concordancia")
PROFILES = dict(
    [
        _profile(
            "repetibilidade",
            "descriptive",
            ("amostra", "lote", "corrida", "replicata", "y"),
            DESCRIPTIVE,
            ("y",),
        ),
        _profile(
            "reprodutibilidade",
            "descriptive",
            ("amostra", "lote", "dia", "corrida", "replicata", "y"),
            DESCRIPTIVE,
            ("dia", "y"),
            "dia",
        ),
        _profile(
            "entre-lotes",
            "descriptive",
            ("amostra", "lote", "dia", "replicata", "y"),
            DESCRIPTIVE,
            ("lote", "y"),
            "lote",
        ),
        _profile(
            "comparacao-metodos",
            "comparison",
            ("amostra", "lote", "kit", "x", "y"),
            ("diferenca_media", "dp_diferencas", *REGRESSION, "correlacao"),
            ("x", "y"),
        ),
        _profile(
            "linearidade", "regression", ("amostra", "grupo", "x", "y"), REGRESSION, ("x", "y")
        ),
        _profile(
            "estabilidade-longa", "regression", ("lote", "x", "y"), REGRESSION, ("x", "y"), "lote"
        ),
        _profile(
            "sensibilidade-especificidade",
            "proportions",
            ("amostra", "kit", "esperado", "obtido"),
            PROPORTIONS,
            ("esperado", "obtido"),
        ),
        _profile("cut-off", "cutoff", ("amostra", "y", "esperado"), PROPORTIONS, ("y", "esperado")),
        _profile(
            "sensibilidade-analitica",
            "detection",
            ("amostra", "grupo", "x", "replicata", "obtido"),
            ("menor_nivel_detectado",),
            ("grupo", "obtido"),
        ),
        _profile(
            "reatividade-cruzada",
            "detection",
            ("amostra", "grupo", "obtido"),
            ("deteccoes",),
            ("grupo", "obtido"),
        ),
        _profile(
            "efeito-prozona",
            "detection",
            ("amostra", "grupo", "x", "obtido"),
            ("deteccao",),
            ("grupo", "obtido"),
        ),
        _profile(
            "interferentes",
            "interference",
            ("amostra", "grupo", "x", "y"),
            ("desvio_max",),
            ("grupo", "x", "y"),
        ),
        _profile(
            "estabilidade-aberto", "change", ("lote", "x", "y"), ("variacao_max",), ("x", "y")
        ),
        _profile(
            "estabilidade-transporte", "change", ("lote", "x", "y"), ("variacao_max",), ("x", "y")
        ),
    ]
)


def metric(name: str, value, config: dict, interval=None) -> dict:
    if name in INTEGER:
        places = 0
    else:
        places = config["fine_places"] if name in FINE else config["places"]
    item = {
        "metrica": name,
        "rotulo": LABELS[name],
        "valor": None,
        "arredondado": None,
        "regra": "",
    }
    if value is None:
        return item
    item["valor"] = str(value)
    item["arredondado"] = str(stats.round_value(value, places, config["rounding"]))
    item["regra"] = stats.rule_label(config["rounding"], places)
    if interval and interval[0] is not None:
        item["ic"] = [str(stats.round_value(v, places, config["rounding"])) for v in interval]
    return item


def _groups(rows, key):
    grouped = OrderedDict()
    for row in rows:
        grouped.setdefault(str(row.get(key) or ""), []).append(row)
    return grouped


def _describe(rows, config) -> list[dict]:
    summary = stats.describe([row["y"] for row in rows])
    return [metric("n", summary["n"], config)] + [
        metric(name, summary[name], config) for name in DESCRIPTIVE
    ]


def _regression(rows, config) -> list[dict]:
    result = stats.regression([r["x"] for r in rows], [r["y"] for r in rows])
    return [metric("n", result["n"], config)] + [
        metric(name, result[name], config) for name in (*REGRESSION, "correlacao")
    ]


def _proportions(pairs, config) -> list[dict]:
    table = stats.contingency(pairs)
    method = config.get("ci_method", "clopper_pearson")
    sens = stats.proportion(table["vp"], table["vp"] + table["fn"], method)
    spec = stats.proportion(table["vn"], table["vn"] + table["fp"], method)
    total = sum(table.values())
    conc = stats.proportion(table["vp"] + table["vn"], total, method)
    out = [metric("n", total, config)]
    for name, result in (("sensibilidade", sens), ("especificidade", spec), ("concordancia", conc)):
        out.append(
            metric(
                name,
                result["proporcao"],
                config,
                (result["ic_inferior"], result["ic_superior"]),
            )
        )
    return out


def _detection(rows, config) -> tuple[list[dict], list[dict]]:
    groups = []
    lowest = None
    positives = 0
    for label, items in _groups(rows, "grupo").items():
        hits = sum(1 for r in items if r.get("obtido") == "pos")
        positives += hits
        rate = stats.proportion(hits, len(items))["proporcao"]
        groups.append(
            {
                "rotulo": label,
                "metricas": [metric("n", len(items), config), metric("deteccao", rate, config)],
            }
        )
        level = next((r.get("x") for r in items if r.get("x") not in (None, "")), None)
        if hits == len(items) and level is not None:
            level = stats.to_decimal(level)
            lowest = level if lowest is None or level < lowest else lowest
    overall = stats.proportion(positives, len(rows))["proporcao"]
    totals = [
        metric("n", len(rows), config),
        metric("deteccoes", positives, config),
        metric("deteccao", overall, config),
        metric("menor_nivel_detectado", lowest, config),
    ]
    return groups, totals


def _interference(rows, config) -> tuple[list[dict], list[dict]]:
    groups, overall = [], None
    for label, items in _groups(rows, "grupo").items():
        deviations = [stats.percent_deviation(r["x"], r["y"]) for r in items]
        valid = [abs(d) for d in deviations if d is not None]
        worst = max(valid) if valid else None
        if worst is not None:
            overall = worst if overall is None or worst > overall else overall
        groups.append(
            {
                "rotulo": label,
                "metricas": [metric("n", len(items), config), metric("desvio_max", worst, config)],
            }
        )
    return groups, [metric("n", len(rows), config), metric("desvio_max", overall, config)]


def _change(rows, config) -> tuple[list[dict], list[dict]]:
    by_time = OrderedDict()
    for row in sorted(rows, key=lambda r: stats.to_decimal(r["x"])):
        by_time.setdefault(stats.to_decimal(row["x"]), []).append(row["y"])
    if not by_time:
        return [], [metric("n", 0, config), metric("variacao_max", None, config)]
    baseline = stats.describe(next(iter(by_time.values())))["media"]
    groups, worst = [], None
    for time, values in by_time.items():
        mean = stats.describe(values)["media"]
        change = stats.percent_deviation(baseline, mean)
        if change is not None and time != next(iter(by_time)):
            worst = abs(change) if worst is None or abs(change) > worst else worst
        groups.append(
            {
                "rotulo": f"Tempo {stats.round_value(time, 2, config['rounding'])}".replace(
                    ".", ","
                ),
                "metricas": [metric("media", mean, config), metric("variacao_max", change, config)],
            }
        )
    return groups, [metric("n", len(rows), config), metric("variacao_max", worst, config)]


def compute(code: str, rows: list[dict], config: dict) -> dict:
    """Resultados por grupo e globais do tipo de estudo, com a regra de arredondamento aplicada."""
    profile = PROFILES[code]
    groups: list[dict] = []
    if profile.kind == "descriptive":
        if profile.group_by:
            groups = [
                {
                    "rotulo": f"{COLUMN_LABELS[profile.group_by]} {label}",
                    "metricas": _describe(items, config),
                }
                for label, items in _groups(rows, profile.group_by).items()
            ]
        totals = _describe(rows, config)
    elif profile.kind == "comparison":
        diffs = stats.differences([r["x"] for r in rows], [r["y"] for r in rows])
        totals = [
            metric("n", diffs["n"], config),
            metric("diferenca_media", diffs["diferenca_media"], config),
            metric("dp_diferencas", diffs["dp_diferencas"], config),
            *_regression(rows, config)[1:],
        ]
    elif profile.kind == "regression":
        if profile.group_by:
            groups = [
                {
                    "rotulo": f"{COLUMN_LABELS[profile.group_by]} {label}",
                    "metricas": _regression(items, config),
                }
                for label, items in _groups(rows, profile.group_by).items()
                if label
            ]
        totals = _regression(rows, config)
    elif profile.kind == "proportions":
        totals = _proportions([(r.get("esperado"), r.get("obtido")) for r in rows], config)
    elif profile.kind == "cutoff":
        cutoff = config.get("cutoff")
        if cutoff in (None, ""):
            totals = [metric("n", len(rows), config)] + [
                metric(n, None, config) for n in PROPORTIONS
            ]
        else:
            pairs = [
                (
                    r.get("esperado"),
                    stats.classify(r["y"], cutoff, config.get("cutoff_direction", "ge")),
                )
                for r in rows
            ]
            totals = _proportions(pairs, config)
    elif profile.kind == "detection":
        groups, totals = _detection(rows, config)
    elif profile.kind == "interference":
        groups, totals = _interference(rows, config)
    else:
        groups, totals = _change(rows, config)
    return {"grupos": groups, "global": totals}


def evaluate(criteria: list[dict], results: dict) -> list[dict]:
    """Critério atendido comparando o valor arredondado exibido com o limite; não calculável não atende."""
    by_name = {item["metrica"]: item for item in results.get("global", [])}
    out = []
    for criterion in criteria:
        item = by_name.get(criterion["metrica"])
        value = item["arredondado"] if item else None
        met = None
        if value is not None:
            value_d, limit = stats.to_decimal(value), stats.to_decimal(criterion["limite"])
            met = {
                "lt": value_d < limit,
                "le": value_d <= limit,
                "gt": value_d > limit,
                "ge": value_d >= limit,
            }[criterion["comparacao"]]
        out.append(
            {
                **criterion,
                "rotulo": LABELS.get(criterion["metrica"], criterion["metrica"]),
                "valor": value,
                "atendido": bool(met) if met is not None else False,
                "calculavel": value is not None,
            }
        )
    return out
