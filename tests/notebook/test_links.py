"""Vínculos nos dois sentidos e promoção de dados para estudo (FR-010, FR-011, SC-003)."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from sgp.notebook import promotion, services
from sgp.notebook.models import LinkKind
from sgp.studies.models import Study, StudyStatus

from .conftest import csv_file


@pytest.mark.req("008:FR-010")
def test_vinculos_do_mesmo_projeto_com_retirada_logica(
    make_entry,
    analyst,
    outsider,
    project,
    make_subdocument,
    make_study,
    make_lot,
    open_project,
    events,
):
    entry = make_entry()
    sub = make_subdocument(project, "entrada")
    study = make_study("repetibilidade")
    lot = make_lot(project, analyst, code="L-VINC")
    for target in (sub, study, lot):
        services.link(entry, by=analyst, target=target)
    assert entry.links.filter(removed_at__isnull=True).count() == 3
    with pytest.raises(ValidationError, match="já existe"):
        services.link(entry, by=analyst, target=sub)
    other = open_project()
    foreign = make_lot(other, other.leader, code="L-ALHEIO")
    with pytest.raises(ValidationError, match="mesmo projeto"):
        services.link(entry, by=analyst, target=foreign)
    with pytest.raises(PermissionDenied):
        services.link(entry, by=outsider, target=sub)
    item = entry.links.get(subdocument=sub)
    with pytest.raises(ValidationError, match="motivo"):
        services.unlink(item, by=analyst, reason=" ")
    services.unlink(item, by=analyst, reason="Ligado por engano")
    item.refresh_from_db()
    assert item.removed_at and item.removal_reason == "Ligado por engano"
    services.link(entry, by=analyst, target=sub)
    assert len(events("notebook.linked")) == 4 and len(events("notebook.unlinked")) == 1


@pytest.mark.req("008:FR-010")
def test_vinculo_aparece_no_outro_registro(
    client, signed_entry, analyst, project, make_subdocument, make_study, make_lot
):
    entry = signed_entry(relevant=False)
    sub = make_subdocument(project, "entrada")
    study = make_study("repetibilidade")
    lot = make_lot(project, analyst, code="L-OUTROLADO")
    for target in (sub, study, lot):
        services.link(entry, by=analyst, target=target)
    client.force_login(analyst)
    pages = (
        reverse("subdocuments:detail", args=[sub.pk]),
        reverse("studies:detail", args=[study.pk]),
        reverse("catalog:detail", args=["lotes", lot.pk]),
    )
    for url in pages:
        content = client.get(url).content.decode()
        assert entry.title in content and "Caderno de laboratório" in content


def _promotable(make_entry, analyst):
    entry = make_entry()
    attachment = services.add_attachment(entry, by=analyst, uploaded=csv_file())
    return entry, attachment


@pytest.mark.req("008:FR-011")
@pytest.mark.req("008:SC-003")
def test_promocao_para_estudo_mantem_o_vinculo_nos_dois_sentidos(
    make_entry, analyst, make_study, events
):
    entry, attachment = _promotable(make_entry, analyst)
    study = make_study("repetibilidade")
    preview = promotion.preview(
        entry, by=analyst, attachment=attachment, study=study, mapping={"y": "Valor"}
    )
    assert preview["accepted"] == 3
    created = promotion.confirm(
        entry, by=analyst, token=preview["token"], equipment="", mapping={"y": "Valor"}
    )
    study.refresh_from_db()
    assert len(study.rows) == 3
    assert created.kind == LinkKind.PROMOTED and created.attachment == attachment
    assert [item["entry"] for item in services.linked_entries(study)] == [entry]
    imported = events("studies.imported")[-1]
    assert imported.new_value["origem_caderno"]["sha256"] == attachment.file.sha256
    assert events("notebook.promoted")[-1].new_value["linhas"] == 3
    with pytest.raises(ValidationError, match="origem"):
        services.unlink(created, by=analyst, reason="Tentativa")
    with pytest.raises(ValidationError, match="promovido"):
        services.remove_attachment(attachment, by=analyst)


@pytest.mark.req("008:FR-011")
def test_promocao_recusada_para_estudo_bloqueado_ou_token_adulterado(
    make_entry, analyst, make_study
):
    entry, attachment = _promotable(make_entry, analyst)
    study = make_study("repetibilidade")
    preview = promotion.preview(
        entry, by=analyst, attachment=attachment, study=study, mapping={"y": "Valor"}
    )
    with pytest.raises(ValidationError, match="expirou"):
        promotion.confirm(entry, by=analyst, token=preview["token"] + "x", equipment="", mapping={})
    Study.objects.filter(pk=study.pk).update(status=StudyStatus.LOCKED)
    with pytest.raises(ValidationError, match="elaboração"):
        promotion.confirm(entry, by=analyst, token=preview["token"], equipment="", mapping={})
    assert promotion.target_studies(entry) == []


@pytest.mark.req("008:FR-011")
def test_tela_de_promocao(client, make_entry, analyst, make_study):
    entry, attachment = _promotable(make_entry, analyst)
    study = make_study("repetibilidade")
    client.force_login(analyst)
    url = reverse("notebook:promote", args=[entry.pk])
    page = client.get(url, {"anexo": attachment.pk, "estudo": study.pk})
    assert page.status_code == 200 and "col__y" in page.content.decode()
    preview = client.post(url, {"anexo": attachment.pk, "estudo": study.pk, "col__y": "Valor"})
    token = preview.context["preview"]["token"]
    done = client.post(
        url,
        {
            "acao": "confirmar",
            "token": token,
            "anexo": attachment.pk,
            "estudo": study.pk,
            "col__y": "Valor",
        },
    )
    assert done.status_code == 302 and done["Location"] == reverse(
        "studies:detail", args=[study.pk]
    )
    study.refresh_from_db()
    assert len(study.rows) == 3
