"""Histórico, comparação e uso por versão (FR-016 a FR-019, SC-004)."""

import pytest
from django.urls import reverse

from sgp.revisions import services

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("013:FR-019")
@pytest.mark.req("013:FR-016")
@pytest.mark.req("013:SC-004")
def test_historico_com_etapas_motivo_e_documentos_por_versao(
    submitted,
    approver,
    signing,
    client,
    quality,
    project,
    approved_entry,
    make_subdocument,
    approve_quick,
):
    for code in ("formulacao", "lote-piloto"):
        approve_quick(make_subdocument(project, code))
    make_subdocument(project, "rapd")
    services.return_revision("form", submitted, by=approver, comment="Detalhar o impacto")
    services.submit("form", submitted, by=quality, reason="Ajuste de rótulo", impact="Novos RAPD")
    services.approve("form", submitted, by=approver, password=signing.password)
    rows = services.history("form", submitted)
    newest, previous = rows[0], rows[1]
    assert (newest["situation"], previous["situation"]) == ("current", "superseded")
    assert [s.get_step_display() for s in newest["steps"]] == [
        "Revisão aberta",
        "Enviada para aprovação",
        "Devolvida",
        "Enviada para aprovação",
        "Aprovada com assinatura",
        "Entrou em vigência",
    ]
    assert previous["usage_count"] == 1 and newest["usage_count"] == 0
    client.force_login(quality)
    page = client.get(reverse("revisions:history", args=["form", submitted.pk])).content.decode()
    assert "Detalhar o impacto" in page and "Novos RAPD" in page and "Vigente" in page


@pytest.mark.req("013:FR-018")
def test_comparacao_entre_duas_versoes_pela_tela(submitted, approver, signing, client, rapd_type):
    from sgp.formtemplates.models import FormTemplate

    services.approve("form", submitted, by=approver, password=signing.password)
    old = FormTemplate.objects.get(subdocument_type=rapd_type, form_version=5)
    client.force_login(approver)
    page = client.get(
        reverse("revisions:compare", args=["form", submitted.pk]), {"com": old.pk}
    ).content.decode()
    assert "Alterado" in page and "Formulações propostas (revisado)" in page


@pytest.mark.req("013:FR-019")
def test_uso_por_versao_de_layout(quality, approver, signing, project):
    from sgp.documents import layouts

    current = layouts.current_layout("charter")
    usage = services.get_adapter("layout").usage(current)
    assert usage and all("versão 01" in item for item in usage)


@pytest.mark.req("013:FR-017")
def test_trilha_filtrada_pelo_modelo(submitted, approver, signing, client):
    services.approve("form", submitted, by=approver, password=signing.password)
    from sgp.audit.models import AuditEvent

    types = set(
        AuditEvent.objects.filter(object_id=str(submitted.pk)).values_list("event_type", flat=True)
    )
    assert {
        "formtemplates.draft_created",
        "formtemplates.draft_updated",
        "templates.submitted",
        "templates.approved",
        "formtemplates.published",
    } <= types
