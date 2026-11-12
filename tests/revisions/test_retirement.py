"""Descarte de revisão e retirada de uso de modelo (FR-011, FR-015)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.formtemplates import services as forms
from sgp.revisions import services
from sgp.revisions.models import TemplateRetirement

pytestmark = [pytest.mark.django_db]


@pytest.mark.req("013:FR-011")
def test_descarte_com_motivo_fica_no_historico_e_libera_nova_revisao(
    form_draft, quality, rapd_type, events
):
    with pytest.raises(ValidationError, match="motivo"):
        services.discard("form", form_draft, by=quality, reason="")
    discarded = services.discard("form", form_draft, by=quality, reason="Não vai adiante")
    assert discarded.status == "discarded" and discarded.discard_reason == "Não vai adiante"
    assert services.history("form", discarded)[0]["situation"] == "discarded"
    assert events("templates.discarded")[-1].reason == "Não vai adiante"
    again = forms.create_draft(rapd_type, by=quality)
    assert again.form_version == 7


@pytest.mark.req("013:FR-015")
def test_retirada_pedida_aprovada_com_assinatura_e_tipo_sem_vigente(
    quality, approver, signing, project, approved_entry, make_subdocument, events, vocab_seed
):
    from sgp.vocab.models import get_term

    change = get_term("tipo-subdocumento", "alteracao")
    existing = make_subdocument(project, "alteracao")
    current = forms.current_template(change)
    with pytest.raises(ValidationError, match="motivo"):
        services.request_retirement(current, by=quality, reason="")
    retirement = services.request_retirement(current, by=quality, reason="Processo mudou")
    with pytest.raises(ValidationError, match="em andamento"):
        services.request_retirement(current, by=quality, reason="De novo")
    services.approve_retirement(retirement, by=approver, password=signing.password)
    retirement.refresh_from_db()
    assert retirement.status == "approved" and retirement.signature.purpose == "retirement"
    assert forms.current_template(change) is None
    with pytest.raises(ValidationError, match="Não há modelo vigente"):
        make_subdocument(project, "alteracao")
    existing.refresh_from_db()
    assert existing.template_id == current.pk  # o documento existente continua consultável
    with pytest.raises(ValidationError, match="retirado de uso"):
        forms.create_draft(change, by=quality)
    assert events("templates.retirement_requested") and events("templates.retirement_approved")


@pytest.mark.req("013:FR-015")
def test_retirada_devolvida_com_comentario_pela_tela(quality, approver, client, rapd_type):
    current = forms.current_template(rapd_type)
    client.force_login(quality)
    client.post(reverse("revisions:retirement_request", args=[current.pk]), {"motivo": "Obsoleto"})
    retirement = TemplateRetirement.objects.get()
    client.force_login(approver)
    client.post(reverse("revisions:retirement_return", args=[retirement.pk]), {"comentario": ""})
    retirement.refresh_from_db()
    assert retirement.status == "requested"
    client.post(
        reverse("revisions:retirement_return", args=[retirement.pk]), {"comentario": "Ainda em uso"}
    )
    retirement.refresh_from_db()
    assert retirement.status == "returned" and forms.current_template(rapd_type) == current


@pytest.mark.req("013:FR-015")
def test_layout_nao_tem_retirada_de_uso(client, quality, vocab_seed):
    from sgp.documents import layouts

    current = layouts.current_layout("subdocument")
    client.force_login(quality)
    page = client.get(reverse("layouts:detail", args=[current.pk])).content.decode()
    assert "Pedir retirada de uso" not in page
    form_page = client.get(
        reverse(
            "formtemplates:detail",
            args=[forms.FormTemplate.objects.filter(status="published").first().pk],
        )
    ).content.decode()
    assert "Histórico e revisões" in form_page
