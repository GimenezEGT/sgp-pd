"""Textos padrão, envio, resultado e aditamento (FR-008, FR-011, FR-012, SC-002)."""

import datetime

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from sgp.dossier import services
from sgp.dossier.models import StandardText, TextStatus

from .test_generation import _final


@pytest.mark.req("011:FR-008")
def test_textos_padrao_versionados_e_aprovados_por_outra_pessoa(
    quality, manager, member, signing, events
):
    first = services.save_text(
        by=quality, key="unidade-fabril", title="Unidade fabril", text="Versão 1"
    )
    with pytest.raises(ValidationError, match="Quem escreveu"):
        services.approve_text(first, by=quality, password=signing.password)
    with pytest.raises(PermissionDenied):
        services.save_text(by=member, key="x", title="X", text="Y")
    signing.enable(manager)
    with pytest.raises(ValidationError, match="incorreta"):
        services.approve_text(first, by=manager, password="errada")
    services.approve_text(first, by=manager, password=signing.password)
    second = services.save_text(
        by=quality, key="unidade-fabril", title="Unidade fabril", text="Versão 2"
    )
    assert second.version == 2 and second.status == TextStatus.DRAFT
    services.approve_text(second, by=manager, password=signing.password)
    statuses = dict(
        StandardText.objects.filter(key="unidade-fabril").values_list("version", "status")
    )
    assert statuses == {1: TextStatus.SUPERSEDED, 2: TextStatus.APPROVED}
    assert len(events("dossier.text_approved")) == 2


@pytest.mark.req("011:FR-011")
def test_envio_e_resultado(
    signed_project,
    approved_entry_with_class,
    quality,
    company,
    minimal_definition,
    approved_text,
    events,
):
    draft = services.generate(signed_project, by=quality)
    with pytest.raises(ValidationError, match="Só o dossiê final"):
        services.submit(
            draft,
            by=quality,
            protocol="25351.000000/2026-00",
            submitted_on=datetime.date(2026, 11, 12),
        )
    version = _final(signed_project, approved_entry_with_class, quality, approved_text)
    submission = services.submit(
        version,
        by=quality,
        protocol="25351.000000/2026-00",
        submitted_on=datetime.date(2026, 11, 12),
    )
    with pytest.raises(ValidationError, match="deferido"):
        services.record_result(
            submission, by=quality, result="pending", result_on=datetime.date(2026, 12, 1)
        )
    services.record_result(
        submission,
        by=quality,
        result="granted",
        result_on=datetime.date(2026, 12, 1),
        notes="Publicado no DOU",
    )
    submission.refresh_from_db()
    assert submission.get_result_display() == "Deferido"
    assert len(events("dossier.submitted")) == 1 and len(events("dossier.result_recorded")) == 1


@pytest.mark.req("011:FR-011")
def test_classe_i_fica_arquivada_sem_envio(
    signed_project, approved_entry_with_class, quality, company, minimal_definition, approved_text
):
    approved_entry_with_class("I")
    approved_text()
    services.save_supplement(
        signed_project,
        by=quality,
        item_key="I.B",
        text="Analito.",
        not_applicable=False,
        justification="",
    )
    version = services.generate(signed_project, by=quality)
    assert version.final and version.risk_class == "I"
    with pytest.raises(ValidationError, match="Classe I"):
        services.submit(version, by=quality, protocol="X", submitted_on=datetime.date(2026, 11, 12))


@pytest.mark.req("011:FR-012")
@pytest.mark.req("011:SC-002")
def test_aditamento_destaca_so_o_que_mudou(
    client,
    signed_project,
    approved_entry_with_class,
    quality,
    company,
    minimal_definition,
    approved_text,
    events,
):
    sent = _final(signed_project, approved_entry_with_class, quality, approved_text)
    services.submit(
        sent, by=quality, protocol="25351.000001/2026-00", submitted_on=datetime.date(2026, 11, 12)
    )
    services.save_supplement(
        signed_project,
        by=quality,
        item_key="I.B",
        text="Analito revisado do KIT DE TESTE.",
        not_applicable=False,
        justification="",
    )
    current = services.generate(signed_project, by=quality)
    previous, changes, _ = services.addendum(current, by=quality)
    assert previous == sent
    assert [change["key"] for change in changes] == ["I.B"]
    assert "Analito revisado do KIT DE TESTE." in changes[0]["after"]
    client.force_login(quality)
    page = client.get(reverse("dossier:addendum", args=[current.pk])).content.decode()
    assert "1 item(ns) alterado(s)" in page
    response = client.get(reverse("dossier:addendum", args=[current.pk]), {"pdf": "1"})
    assert response["Content-Type"] == "application/pdf" and response.content.startswith(b"%PDF")
    assert events("dossier.addendum_generated")[-1].new_value["itens_alterados"] == ["I.B"]
