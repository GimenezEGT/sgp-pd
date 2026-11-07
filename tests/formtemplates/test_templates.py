"""Cadastro, edição e publicação de modelos pela Qualidade (US1: FR-001, FR-003 a FR-005)."""

import json

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.formtemplates import services
from sgp.formtemplates.models import FormTemplate
from sgp.vocab.models import get_term

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("vocab_seed")]


@pytest.fixture
def quality(make_user):
    return make_user(None, Profile.QUALITY)


@pytest.fixture
def critical_type():
    return get_term("tipo-subdocumento", "analise-critica")


@pytest.mark.req("004:FR-004")
def test_rascunho_da_proxima_versao_copia_a_vigente(quality, critical_type, events):
    current = services.current_template(critical_type)
    draft = services.create_draft(critical_type, by=quality)
    assert (draft.form_version, draft.status) == (current.form_version + 1, "draft")
    assert draft.definition == current.definition and draft.reference == current.reference
    assert events("formtemplates.draft_created")[-1].new_value["a_partir_de"] == "05"
    with pytest.raises(ValidationError, match="Já existe um rascunho"):
        services.create_draft(critical_type, by=quality)


@pytest.mark.req("004:FR-001")
def test_editar_e_publicar_com_evento(quality, critical_type, events):
    draft = services.create_draft(critical_type, by=quality)
    definition = dict(draft.definition)
    definition["topics"] = draft.topics + [
        {
            "key": "estatistica",
            "label": "Avaliação das técnicas estatísticas utilizadas",
            "fields": [{"key": "texto", "type": "rich_text", "label": "Avaliação"}],
        }
    ]
    draft = services.update_draft(draft, by=quality, data={}, definition=definition, row_version=1)
    updated = events("formtemplates.draft_updated")[-1]
    assert "topico:estatistica" in updated.new_value
    services.publish(draft, by=quality)
    draft.refresh_from_db()
    assert draft.is_published and draft.published_by == quality
    assert services.current_template(critical_type) == draft
    assert events("formtemplates.published")[-1].new_value["versao"] == "06"


@pytest.mark.req("004:FR-003")
def test_publicacao_recusada_com_definicao_invalida(quality, critical_type):
    draft = services.create_draft(critical_type, by=quality)
    definition = dict(draft.definition)
    duplicated = dict(draft.topics[0], key="outro")
    definition["topics"] = draft.topics + [duplicated]
    draft = services.update_draft(draft, by=quality, data={}, definition=definition)
    with pytest.raises(ValidationError) as error:
        services.publish(draft, by=quality)
    assert any("rótulo repetido" in message for message in error.value.messages)


@pytest.mark.req("004:FR-004")
def test_publicado_nao_muda_nem_pelo_servico_nem_pelo_banco(quality, critical_type):
    current = services.current_template(critical_type)
    with pytest.raises(ValidationError, match="publicado não muda"):
        services.update_draft(current, by=quality, data={}, definition=current.definition)
    with pytest.raises(DatabaseError, match="publicado não pode ser alterado"):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE formtemplates_formtemplate SET reference = 'x' WHERE id = %s", [current.pk]
            )


@pytest.mark.req("004:FR-005")
def test_so_a_qualidade_cadastra_e_publica(client, login_as, make_user, critical_type, events):
    with pytest.raises(ValidationError, match="Só a Qualidade"):
        services.create_draft(critical_type, by=make_user(None, Profile.RD_MANAGER))
    current = services.current_template(critical_type)
    login_as(Profile.ANALYST, Profile.RD_MANAGER)
    assert client.get(reverse("formtemplates:list")).status_code == 200
    assert client.get(reverse("formtemplates:detail", args=[current.pk])).status_code == 200
    response = client.post(reverse("formtemplates:new_version", args=[current.pk]))
    assert response.status_code == 403
    assert events("auth.permission_denied")


@pytest.mark.req("004:FR-001")
def test_telas_da_qualidade(client, quality, critical_type):
    client.force_login(quality)
    current = services.current_template(critical_type)
    detail = client.get(reverse("formtemplates:detail", args=[current.pk])).content.decode()
    assert "ESTE RELATÓRIO DEVE CONTER:" in detail and "1 - Análise sistemática" in detail
    response = client.post(reverse("formtemplates:new_version", args=[current.pk]))
    draft = FormTemplate.objects.get(subdocument_type=critical_type, status="draft")
    assert response["Location"] == reverse("formtemplates:edit", args=[draft.pk])
    payload = {
        "reference": draft.reference,
        "valid_from": draft.valid_from.isoformat(),
        "definition": "{ inválido",
        "row_version": draft.row_version,
    }
    page = client.post(reverse("formtemplates:edit", args=[draft.pk]), payload).content.decode()
    assert "JSON inválido na linha 1" in page
    payload["definition"] = json.dumps(draft.definition)
    client.post(reverse("formtemplates:edit", args=[draft.pk]), payload)
    client.post(reverse("formtemplates:publish", args=[draft.pk]))
    draft.refresh_from_db()
    assert draft.is_published
