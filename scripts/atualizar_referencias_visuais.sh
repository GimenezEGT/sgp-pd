#!/bin/sh
# Regera as referências da regressão visual (feature 006, SC-008) a partir dos dados de teste.
# Só use com aprovação registrada da Garantia da Qualidade; confira as imagens antes do commit.
# Uso: docker compose run --rm web sh scripts/atualizar_referencias_visuais.sh
set -eu
SGP_ATUALIZAR_REFERENCIAS=1 pytest -q -p no:cacheprovider --no-cov tests/documents/test_visual.py -rs
ls -l tests/documents/referencias
