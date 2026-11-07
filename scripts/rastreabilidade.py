"""Gera a matriz de rastreabilidade requisito → teste (evidência para a validação do sistema,
RDC 665/2022, art. 104).

Lê os requisitos (FR-xxx e SC-xxx) de specs/*/spec.md, o mapa teste → requisitos gravado pelo
pytest (--req-report) e as verificações manuais de docs/validacao/verificacoes-manuais.json.

Uso:
    pytest --collect-only -q --req-report=var/req-report.json
    python scripts/rastreabilidade.py

Sai com código 1 se algum requisito não tiver teste nem verificação manual registrada, ou se algum
teste citar requisito inexistente.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
MANUAL = ROOT / "docs" / "validacao" / "verificacoes-manuais.json"
OUTPUT = ROOT / "docs" / "validacao" / "matriz-rastreabilidade.md"
REQ_LINE = re.compile(r"^\s*-\s+\*\*(?P<id>(?:FR|SC)-\d{3})\*\*:\s*(?P<text>.+)$")


def load_requirements() -> dict[str, tuple[str, str]]:
    requirements = {}
    for spec in sorted(SPECS.glob("*/spec.md")):
        feature = spec.parent.name[:3]
        for line in spec.read_text(encoding="utf-8").splitlines():
            match = REQ_LINE.match(line)
            if match:
                requirements[f"{feature}:{match['id']}"] = (spec.parent.name, match["text"].strip())
    return requirements


def summarize(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", text).replace("|", "/")
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def main(report_path: str = "var/req-report.json") -> int:
    report = json.loads((ROOT / report_path).read_text(encoding="utf-8"))
    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else {}
    tests_by_req: dict[str, list[str]] = defaultdict(list)
    for test, ids in report.items():
        for identifier in ids:
            tests_by_req[identifier].append(test)

    requirements = load_requirements()
    unknown = sorted(set(tests_by_req) - set(requirements))
    missing = [req for req in requirements if req not in tests_by_req and req not in manual]

    lines = [
        "# Matriz de rastreabilidade requisito → teste",
        "",
        f"Gerada por `scripts/rastreabilidade.py` em {date.today():%d/%m/%Y}. Não edite à mão.",
        "",
        f"Requisitos: {len(requirements)} · com teste automatizado: "
        f"{sum(1 for req in requirements if req in tests_by_req)} · só verificação manual: "
        f"{sum(1 for req in requirements if req not in tests_by_req and req in manual)} · sem cobertura: {len(missing)}",
        "",
    ]
    current_feature = None
    for req, (feature_dir, text) in requirements.items():
        if feature_dir != current_feature:
            current_feature = feature_dir
            lines += [
                f"## {feature_dir}",
                "",
                "| Requisito | Descrição | Evidência |",
                "| --- | --- | --- |",
            ]
        tests = sorted(tests_by_req.get(req, []))
        evidence = "<br>".join(f"`{test}`" for test in tests)
        if req in manual:
            evidence = (evidence + "<br>" if evidence else "") + f"Manual: {manual[req]}"
        lines.append(
            f"| {req.split(':')[1]} | {summarize(text)} | {evidence or '**SEM COBERTURA**'} |"
        )
        next_index = list(requirements).index(req) + 1
        if (
            next_index == len(requirements)
            or requirements[list(requirements)[next_index]][0] != feature_dir
        ):
            lines.append("")
    if unknown:
        lines += (
            ["## Testes que citam requisitos inexistentes", ""]
            + [f"- {req}" for req in unknown]
            + [""]
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Matriz gravada em {OUTPUT.relative_to(ROOT)}: {len(requirements)} requisitos, {len(missing)} sem cobertura."
    )
    for req in missing:
        print(f"  SEM COBERTURA: {req}")
    for req in unknown:
        print(f"  REQUISITO INEXISTENTE CITADO EM TESTE: {req}")
    return 1 if missing or unknown else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
