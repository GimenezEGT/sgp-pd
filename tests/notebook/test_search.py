"""Linha do tempo, busca e pendências (FR-012, FR-013, SC-002, SC-004)."""

import time
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from sgp.notebook import richtext, search, services
from sgp.notebook.models import MaterialKind, NotebookEntry
from sgp.notebook.search import Filters


def _found(user, **filters):
    return set(search.search(user, Filters(**filters)).values_list("pk", flat=True))


@pytest.mark.req("008:FR-013")
@pytest.mark.req("008:SC-002")
def test_busca_por_lote_traz_todas_as_entradas_que_o_usam(
    make_entry, analyst, manager, project, make_lot
):
    make_lot(project, analyst, code="L-BUSCA-1")
    lot = make_lot(project, analyst, code="L-BUSCA-2")
    first, second, third, other = (make_entry(f"Ensaio {n}") for n in range(4))
    services.add_material(first, by=analyst, kind=MaterialKind.LOT, code="L-BUSCA-1")
    services.add_material(second, by=analyst, kind=MaterialKind.LOT, code="L-BUSCA-1")
    services.add_material(other, by=analyst, kind=MaterialKind.LOT, code="L-BUSCA-2")
    services.link(third, by=analyst, target=lot.__class__.objects.get(code="L-BUSCA-1"))
    assert _found(manager, lot="l-busca-1") == {first.pk, second.pk, third.pk}
    assert _found(manager, lot="L-BUSCA-2") == {other.pk}


@pytest.mark.req("008:FR-013")
def test_busca_textual_em_portugues_com_e_sem_acento(make_entry, analyst, manager, signing):
    entry = make_entry("Preparo do tampão")
    services.update_entry(entry, by=analyst, data={"procedure": "<p>Solução tampão de fosfato</p>"})
    make_entry("Outro assunto")
    for words in ("solução", "solucao", "SOLUCAO tampao", "fosfato"):
        assert _found(manager, q=words) == {entry.pk}, words
    assert _found(manager, q="inexistente") == set()
    signing.enable(analyst)
    services.sign_entry(entry, by=analyst, password=signing.password)
    services.add_addendum(
        entry, by=analyst, text="Equipamento recalibrado", password=signing.password
    )
    assert _found(manager, q="recalibrado") == {entry.pk}


@pytest.mark.req("008:FR-013")
def test_filtros_por_amostra_pesquisador_periodo_e_situacao(
    make_entry, analyst, colleague, manager, make_sample, signed_entry
):
    sample = make_sample(analyst)
    with_sample = make_entry("Com amostra")
    services.add_material(with_sample, by=analyst, kind=MaterialKind.SAMPLE, code=sample.identifier)
    by_colleague = make_entry("Do colega", by=colleague)
    old = make_entry("Antiga")
    NotebookEntry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=12))
    awaiting = signed_entry(relevant=True)
    plain = signed_entry(relevant=False)
    assert _found(manager, sample=sample.identifier) == {with_sample.pk}
    assert _found(manager, author=colleague.username) == {by_colleague.pk}
    assert by_colleague.pk in _found(manager, author=colleague.full_name[-5:])
    today = timezone.localdate()
    assert old.pk not in _found(manager, date_from=today - timedelta(days=1))
    assert _found(manager, date_to=today - timedelta(days=5)) == {old.pk}
    assert _found(manager, situation="overdue") == {old.pk}
    assert _found(manager, situation="awaiting_witness") == {awaiting.pk}
    assert _found(manager, situation="signed") == {plain.pk}
    assert old.pk in _found(manager, situation="")
    assert _found(manager, older_than=10) == {old.pk}
    assert _found(manager, older_than=0) >= {old.pk, with_sample.pk}


@pytest.mark.req("008:FR-013")
def test_so_projetos_acessiveis(client, make_entry, outsider, manager, quality):
    entry = make_entry("Confidencial")
    assert _found(outsider) == set()
    assert entry.pk in _found(manager) and entry.pk in _found(quality)
    client.force_login(outsider)
    page = client.get(reverse("notebook:search"), {"q": "Confidencial"}).content.decode()
    assert reverse("notebook:detail", args=[entry.pk]) not in page and "0 entrada(s)" in page


@pytest.mark.req("008:FR-012")
def test_linha_do_tempo_paginada_com_carregar_mais(client, make_entry, analyst, project):
    for number in range(25):
        make_entry(f"Ensaio {number:02d}")
    client.force_login(analyst)
    url = reverse("notebook:project", args=[project.pk])
    page = client.get(url).content.decode()
    assert page.count('class="entrada-caderno"') == 20 and "Carregar mais" in page
    assert page.index("Ensaio 24") < page.index("Ensaio 05")
    more = client.get(url, {"pagina": 2}, HTTP_HX_REQUEST="true").content.decode()
    assert more.count('class="entrada-caderno"') == 5 and "<html" not in more
    assert "Carregar mais" not in more and "Nova entrada" in page


@pytest.mark.req("008:SC-004")
def test_busca_em_1000_entradas_em_menos_de_2_segundos(project, analyst, manager):
    entries = []
    for number in range(1, 1001):
        title = f"Ensaio {number} de estabilidade"
        procedure = f"<p>Solução tampão lote {number % 37}</p>"
        entries.append(
            NotebookEntry(
                project=project,
                number=number,
                author=analyst,
                title=title,
                procedure=procedure,
                search_text=richtext.fold(f"{title} {richtext.plain_text(procedure)}"),
                updated_by=analyst,
            )
        )
    NotebookEntry.objects.bulk_create(entries)
    start = time.perf_counter()
    queryset = search.search(manager, Filters(q="solucao tampao estabilidade"))
    total = queryset.count()
    first_page = list(queryset[:20])
    elapsed = time.perf_counter() - start
    assert total == 1000 and len(first_page) == 20
    assert elapsed < 2, elapsed
