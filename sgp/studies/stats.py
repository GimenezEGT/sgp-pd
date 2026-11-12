"""Cálculos dos estudos (feature 007): módulo puro, sem Django (research R1 e R2).

Os dados entram como texto ou Decimal e as contas usam aritmética decimal exata; o arredondamento
é só de exibição, aplicado sobre o valor completo. Valor que não pode ser calculado é None.
"""

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, localcontext

RULES = {
    "half_even": (ROUND_HALF_EVEN, "meio para o par"),
    "half_up": (ROUND_HALF_UP, "meio para cima"),
    "truncate": (ROUND_DOWN, "truncar"),
}
WILSON_Z = Decimal("1.959963984540054")  # quantil 0,975 da normal padrão
HUNDRED = Decimal(100)


def to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(repr(value))
    return Decimal(str(value).strip().replace(",", "."))


def round_value(value, places: int, rule: str = "half_even") -> Decimal | None:
    if value is None:
        return None
    return to_decimal(value).quantize(Decimal(1).scaleb(-places), rounding=RULES[rule][0])


def rule_label(rule: str, places: int) -> str:
    return f"{RULES[rule][1]}, {places} casa{'s' if places != 1 else ''}"


def _mean(data: list[Decimal]) -> Decimal:
    return sum(data, Decimal(0)) / len(data)


def describe(values) -> dict:
    """Média, desvio-padrão amostral (n − 1) e populacional e CV%."""
    data = [to_decimal(v) for v in values]
    n = len(data)
    if not n:
        return {"n": 0, "media": None, "dp": None, "dp_populacional": None, "cv": None}
    with localcontext() as ctx:
        ctx.prec = 40
        mean = _mean(data)
        squares = sum(((v - mean) ** 2 for v in data), Decimal(0))
        sd = (squares / (n - 1)).sqrt() if n >= 2 else None
        sd_pop = (squares / n).sqrt()
        cv = sd / mean * HUNDRED if sd is not None and mean != 0 else None
    return {"n": n, "media": +mean, "dp": sd, "dp_populacional": sd_pop, "cv": cv}


def differences(reference, measured) -> dict:
    """Diferença média (medido − referência) e desvio-padrão das diferenças."""
    diffs = [to_decimal(y) - to_decimal(x) for x, y in zip(reference, measured, strict=True)]
    summary = describe(diffs)
    return {"n": summary["n"], "diferenca_media": summary["media"], "dp_diferencas": summary["dp"]}


def regression(x_values, y_values) -> dict:
    """Regressão linear de mínimos quadrados de y em x, com R² e correlação."""
    xs = [to_decimal(v) for v in x_values]
    ys = [to_decimal(v) for v in y_values]
    empty = {"n": len(xs), "inclinacao": None, "intercepto": None, "r2": None, "correlacao": None}
    if len(xs) < 2 or len(set(xs)) < 2:
        return empty
    with localcontext() as ctx:
        ctx.prec = 40
        mx, my = _mean(xs), _mean(ys)
        sxx = sum(((x - mx) ** 2 for x in xs), Decimal(0))
        sxy = sum(((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)), Decimal(0))
        syy = sum(((y - my) ** 2 for y in ys), Decimal(0))
        slope = sxy / sxx
        intercept = my - slope * mx
        r2 = sxy * sxy / (sxx * syy) if syy != 0 else None
        r = sxy / (sxx * syy).sqrt() if syy != 0 else None
    return {"n": len(xs), "inclinacao": slope, "intercepto": intercept, "r2": r2, "correlacao": r}


def proportion(successes: int, total: int, method: str = "clopper_pearson") -> dict:
    """Proporção em % com IC 95% exato de Clopper-Pearson (padrão) ou de Wilson."""
    if total <= 0:
        return {
            "k": successes,
            "n": total,
            "proporcao": None,
            "ic_inferior": None,
            "ic_superior": None,
        }
    k, n = successes, total
    if method == "wilson":
        with localcontext() as ctx:
            ctx.prec = 40
            p = Decimal(k) / n
            z2 = WILSON_Z * WILSON_Z
            denominator = 1 + z2 / n
            center = (p + z2 / (2 * n)) / denominator
            half = WILSON_Z * (p * (1 - p) / n + z2 / (4 * n * n)).sqrt() / denominator
            low, high = max(Decimal(0), center - half), min(Decimal(1), center + half)
    else:
        from scipy.stats import beta

        low = Decimal(0) if k == 0 else to_decimal(float(beta.ppf(0.025, k, n - k + 1)))
        high = Decimal(1) if k == n else to_decimal(float(beta.ppf(0.975, k + 1, n - k)))
        p = Decimal(k) / n
    return {
        "k": k,
        "n": n,
        "proporcao": p * HUNDRED,
        "ic_inferior": low * HUNDRED,
        "ic_superior": high * HUNDRED,
    }


def percent_deviation(expected, found) -> Decimal | None:
    expected, found = to_decimal(expected), to_decimal(found)
    if expected == 0:
        return None
    return (found - expected) / expected * HUNDRED


def classify(value, cutoff, direction: str) -> str:
    """Interpretação pelo corte: positivo quando ≥ corte (`ge`) ou ≤ corte (`le`)."""
    value, cutoff = to_decimal(value), to_decimal(cutoff)
    positive = value >= cutoff if direction == "ge" else value <= cutoff
    return "pos" if positive else "neg"


def contingency(pairs) -> dict:
    """Verdadeiros e falsos positivos e negativos de pares (esperado, obtido)."""
    table = {"vp": 0, "fn": 0, "vn": 0, "fp": 0}
    for expected, obtained in pairs:
        if expected == "pos":
            table["vp" if obtained == "pos" else "fn"] += 1
        elif expected == "neg":
            table["vn" if obtained == "neg" else "fp"] += 1
    return table
