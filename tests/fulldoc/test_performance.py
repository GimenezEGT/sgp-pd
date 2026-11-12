"""Desempenho: 300 páginas em menos de 3 minutos (SC-003). Rodar com `pytest -m slow`."""

import time

import pytest

from sgp.notebook import richtext
from sgp.notebook.models import EntryStatus, NotebookEntry

PARAGRAPH = (
    "Preparo da solução tampão de fosfato, ajuste do pH, leitura em triplicata no equipamento de "
    "bancada e registro das condições ambientais do laboratório durante o ensaio. "
)


@pytest.mark.slow
@pytest.mark.req("009:SC-003")
def test_trezentas_paginas_em_menos_de_tres_minutos(
    complete_project, member, run_fulldoc, seal_cert
):
    project = complete_project()
    procedure = "".join(f"<p>{PARAGRAPH * 6}</p>" for _ in range(6))
    NotebookEntry.objects.bulk_create(
        NotebookEntry(
            project=project,
            number=number,
            author=member,
            title=f"Ensaio {number} de estabilidade",
            procedure=procedure,
            conclusion="<p>Resultado dentro do esperado.</p>",
            status=EntryStatus.SIGNED,
            search_text=richtext.fold(f"Ensaio {number}"),
            updated_by=member,
        )
        for number in range(1, 281)
    )
    start = time.perf_counter()
    done = run_fulldoc(project, project.leader, caderno="completo")
    elapsed = time.perf_counter() - start
    print(f"SC-003: {done.result.pages} páginas em {elapsed:.1f} s")
    assert done.result.pages >= 300, done.result.pages
    assert elapsed < 180, elapsed
