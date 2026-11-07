"""Confere a cobertura mínima por pacote (plano da feature 001: ≥ 90% em core e auditoria).

Uso, depois do pytest (que grava var/coverage.json):
    python scripts/cobertura_minima.py
"""

import json
import sys
from pathlib import Path

THRESHOLDS = {"sgp/core": 90.0, "sgp/audit": 90.0}


def main(path: str = "var/coverage.json") -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    totals = {prefix: [0, 0] for prefix in THRESHOLDS}
    for filename, info in data["files"].items():
        normalized = filename.replace("\\", "/")
        for prefix in THRESHOLDS:
            if normalized.startswith(prefix + "/"):
                summary = info["summary"]
                totals[prefix][0] += summary["covered_lines"] + summary.get("covered_branches", 0)
                totals[prefix][1] += summary["num_statements"] + summary.get("num_branches", 0)
    failed = False
    for prefix, (covered, total) in totals.items():
        percent = 100.0 * covered / total if total else 100.0
        ok = percent >= THRESHOLDS[prefix]
        failed = failed or not ok
        print(
            f"{prefix}: {percent:.1f}% (mínimo {THRESHOLDS[prefix]:.0f}%) {'OK' if ok else 'ABAIXO DO MÍNIMO'}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
