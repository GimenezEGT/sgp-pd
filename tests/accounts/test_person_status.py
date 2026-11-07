"""Desativação e reativação de pessoas pelo Administrador, sem exclusão (FR-026, FR-012)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.accounts.services import grant_profile, set_person_active
from sgp.audit.models import AuditEvent

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-026")]


def test_administrador_desativa_e_reativa_com_motivo(client, login_as, make_user):
    admin = login_as(Profile.ADMIN)
    person = make_user("ana", Profile.ANALYST)
    url = reverse("accounts:deactivate_person", args=[person.pk])
    client.post(url, {"reason": "Desligamento da empresa"})
    person.refresh_from_db()
    assert not person.is_active
    event = AuditEvent.objects.get(event_type="accounts.user_updated", object_id=str(person.pk))
    assert event.actor == admin and event.reason == "Desligamento da empresa"
    assert event.old_value == {"is_active": True} and event.new_value == {"is_active": False}
    client.post(reverse("accounts:reactivate_person", args=[person.pk]), {"reason": "Readmissão"})
    person.refresh_from_db()
    assert person.is_active


def test_pessoa_desativada_nao_entra_nem_recebe_perfil(client, directory, make_user):
    admin = make_user("admin", Profile.ADMIN)
    person = make_user("ana", Profile.ANALYST)
    set_person_active(person, by=admin, active=False, reason="Afastamento")
    directory.add_person("ana")
    response = client.post(
        reverse("accounts:login"), {"username": "ana", "password": "Senha#Teste1"}
    )
    assert response.status_code == 200
    with pytest.raises(ValidationError):
        grant_profile(person, Profile.READER, by=admin, reason="x", approval_reference="y")


@pytest.mark.req("001:FR-012")
def test_ultimo_administrador_nao_e_desativado(make_user):
    admin = make_user("admin", Profile.ADMIN)
    with pytest.raises(ValidationError, match="último Administrador"):
        set_person_active(admin, by=admin, active=False, reason="Teste")
    make_user("admin2", Profile.ADMIN)
    set_person_active(admin, by=admin, active=False, reason="Troca de função")


def test_motivo_obrigatorio_e_situacao_repetida(make_user):
    admin = make_user("admin", Profile.ADMIN)
    person = make_user("ana")
    with pytest.raises(ValidationError):
        set_person_active(person, by=admin, active=False, reason="")
    with pytest.raises(ValidationError, match="já está ativa"):
        set_person_active(person, by=admin, active=True, reason="x")


def test_somente_administrador_desativa(client, login_as, make_user):
    login_as(Profile.RD_MANAGER)
    person = make_user("ana")
    url = reverse("accounts:deactivate_person", args=[person.pk])
    assert client.post(url, {"reason": "x"}).status_code == 403
    person.refresh_from_db()
    assert person.is_active
