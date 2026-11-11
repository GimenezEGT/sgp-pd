"""Regressão visual: páginas geradas dos dados de teste comparadas com as referências aprovadas
pela Qualidade (SC-008; research R12).

Atualizar as referências (só com aprovação registrada da Qualidade):
    docker compose run --rm web sh scripts/atualizar_referencias_visuais.sh
"""

import os
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import Image, ImageChops, ImageStat

from sgp.documents import layouts, render_pdf
from sgp.documents.preview import sample_content

pytestmark = [pytest.mark.django_db]
REFERENCES = Path(__file__).parent / "referencias"
UPDATE = os.environ.get("SGP_ATUALIZAR_REFERENCIAS") == "1"
DPI = 50
TOLERANCE = 0.5  # diferença média de pixel, em níveis de cinza (0 a 255)


def _pages(target: str, *, draft: bool, rows: int | None = None) -> list[Image.Image]:
    data = sample_content(target)
    if rows:
        table = data["sections"][0]["blocks"][2]
        table["rows"] = [
            [f"{i:03d}", f"Item fictício {i:03d}", f"{i},50"] for i in range(1, rows + 1)
        ]
    pdf = render_pdf.render(
        data,
        layouts.current_layout(target),
        draft=draft,
        created="2026-11-08T10:00:00-03:00",
        identifier=b"0" * 32,
        verification_code="" if draft else "ABCD-EFGH-JKMN-PQRS",
    )
    document = pdfium.PdfDocument(pdf)
    return [page.render(scale=DPI / 72).to_pil().convert("L") for page in document]


CASES = {
    "subdocumento-capa-oficial": lambda: _pages("subdocument", draft=False)[0],
    "subdocumento-tabela-rascunho": lambda: _pages("subdocument", draft=True, rows=120)[1],
    "tap-capa-oficial": lambda: _pages("charter", draft=False)[0],
}


@pytest.mark.req("006:SC-008")
@pytest.mark.req("006:FR-004")
@pytest.mark.parametrize("name", sorted(CASES))
def test_paginas_iguais_as_referencias_aprovadas(vocab_seed, name):
    image = CASES[name]()
    path = REFERENCES / f"{name}.png"
    if UPDATE:
        REFERENCES.mkdir(exist_ok=True)
        image.save(path, optimize=True)
        pytest.skip(f"referência atualizada: {path.name}")
    assert path.exists(), (
        f"Falta a referência {path.name}; gere com scripts/atualizar_referencias_visuais.sh"
    )
    reference = Image.open(path).convert("L")
    assert image.size == reference.size
    difference = ImageStat.Stat(ImageChops.difference(image, reference)).mean[0]
    assert difference <= TOLERANCE, f"{name}: diferença média {difference:.3f}"
