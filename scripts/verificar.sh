#!/bin/sh
# Portão de qualidade do SGP-P&D: lint, testes, cobertura mínima e matriz de rastreabilidade.
# Uso: docker compose run --rm web sh scripts/verificar.sh
set -eu

echo "== ruff"
ruff check .

echo "== pytest"
pytest -q -p no:cacheprovider "$@"

echo "== cobertura mínima por pacote"
python scripts/cobertura_minima.py

echo "== matriz de rastreabilidade"
pytest --collect-only -q -p no:cacheprovider --no-cov --req-report=var/req-report.json >/dev/null
python scripts/rastreabilidade.py
