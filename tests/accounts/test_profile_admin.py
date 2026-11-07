"""Concessão e revogação de perfis pelo Administrador (história 2): FR-010 a FR-012, SC-004."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import Profile
from sgp.accounts.services import grant_profile, revoke_profile
from sgp.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def grant_url(person):
    return reverse("accounts:grant_profile", args=[person.pk])


def revoke_url(assignment):
    return reverse("accounts:revoke_profile", args=[assignment.user_id, assignment.pk])


@pytest.mark.req("001:FR-010")
@pytest.mark.req("001:SC-004")
def test_concessao_com_motivo_e_aprovacao(client, login_as, make_user):
    admin = login_as(Profile.ADMIN)
    person = make_user("ana")
    response = client.post(
        grant_url(person),
        {
            "profile": Profile.ANALYST,
            "reason": "Entrada na equipe do projeto",
            "approval_reference": "E-mail do Gestor de P&D 07/11/2026",
        },
    )
    assert response.status_code == 302
    assignment = ProfileAssignment.objects.get(user=person)
    assert assignment.profile == Profile.ANALYST and assignment.granted_by == admin
    event = AuditEvent.objects.get(event_type="accounts.profile_granted")
    assert event.actor == admin and event.reason == "Entrada na equipe do projeto"
    assert event.old_value == {"perfis": []}
    assert event.new_value["perfis"] == ["ANALYST"]
    assert event.new_value["aprovacao"] == "E-mail do Gestor de P&D 07/11/2026"
    assert event.occurred_at is not None


@pytest.mark.req("001:FR-010")
@pytest.mark.parametrize("missing", ["reason", "approval_reference"])
def test_concessao_sem_motivo_ou_aprovacao_e_recusada(client, login_as, make_user, missing):
    login_as(Profile.ADMIN)
    person = make_user("ana")
    data = {"profile": Profile.ANALYST, "reason": "Motivo", "approval_reference": "Aprovação"}
    data[missing] = ""
    client.post(grant_url(person), data)
    assert not ProfileAssignment.objects.filter(user=person).exists()


@pytest.mark.req("001:FR-010")
def test_concessao_duplicada_e_recusada(make_user):
    admin = make_user("admin", Profile.ADMIN)
    person = make_user("ana", Profile.READER)
    with pytest.raises(ValidationError, match="já tem esse perfil"):
        grant_profile(person, Profile.READER, by=admin, reason="x", approval_reference="y")


def test_pessoa_desativada_nao_recebe_perfil(make_user):
    admin = make_user("admin", Profile.ADMIN)
    person = make_user("ana", is_active=False)
    with pytest.raises(ValidationError, match="desativada"):
        grant_profile(person, Profile.READER, by=admin, reason="x", approval_reference="y")


@pytest.mark.req("001:FR-011")
@pytest.mark.req("001:SC-004")
def test_revogacao_preserva_historico(client, login_as, make_user):
    admin = login_as(Profile.ADMIN)
    person = make_user("ana", Profile.READER)
    assignment = ProfileAssignment.objects.get(user=person)
    response = client.post(revoke_url(assignment), {"reason": "Saiu do projeto"})
    assert response.status_code == 302
    assignment.refresh_from_db()
    assert assignment.revoked_at is not None and assignment.revoked_by == admin
    assert assignment.revoke_reason == "Saiu do projeto"
    assert ProfileAssignment.objects.filter(user=person).count() == 1
    event = AuditEvent.objects.get(event_type="accounts.profile_revoked")
    assert event.old_value == {"perfis": ["READER"]} and event.new_value["perfis"] == []
    detail = client.get(reverse("accounts:person_detail", args=[person.pk])).content.decode()
    assert "Saiu do projeto" in detail


@pytest.mark.req("001:FR-011")
def test_revogacao_sem_motivo_ou_repetida_e_recusada(make_user):
    admin = make_user("admin", Profile.ADMIN)
    person = make_user("ana", Profile.READER)
    assignment = ProfileAssignment.objects.get(user=person)
    with pytest.raises(ValidationError):
        revoke_profile(assignment, by=admin, reason=" ")
    revoke_profile(assignment, by=admin, reason="ok")
    with pytest.raises(ValidationError, match="já foi revogada"):
        revoke_profile(assignment, by=admin, reason="de novo")


@pytest.mark.req("001:FR-012")
def test_ultimo_administrador_nao_e_revogado(client, login_as):
    admin = login_as(Profile.ADMIN)
    assignment = ProfileAssignment.objects.get(user=admin)
    response = client.post(revoke_url(assignment), {"reason": "Teste"}, follow=True)
    assert "último Administrador" in response.content.decode()
    assignment.refresh_from_db()
    assert assignment.revoked_at is None


@pytest.mark.req("001:FR-012")
def test_com_dois_administradores_um_pode_ser_revogado(make_user):
    first = make_user("admin1", Profile.ADMIN)
    make_user("admin2", Profile.ADMIN)
    revoke_profile(ProfileAssignment.objects.get(user=first), by=first, reason="Troca de função")
    assert not ProfileAssignment.objects.filter(user=first, revoked_at__isnull=True).exists()


@pytest.mark.req("001:FR-012")
def test_administrador_desativado_nao_conta_como_ativo(make_user):
    first = make_user("admin1", Profile.ADMIN)
    second = make_user("admin2", Profile.ADMIN)
    second.is_active = False
    second.save()
    with pytest.raises(ValidationError):
        revoke_profile(ProfileAssignment.objects.get(user=first), by=first, reason="x")


@pytest.mark.req("001:FR-010")
@pytest.mark.parametrize("profile", [Profile.RD_MANAGER, Profile.QUALITY, Profile.READER])
def test_somente_administrador_gerencia_perfis(client, login_as, make_user, profile):
    login_as(profile)
    person = make_user("alvo")
    assert client.get(reverse("accounts:people")).status_code == 403
    assert client.get(reverse("accounts:person_detail", args=[person.pk])).status_code == 403
    response = client.post(
        grant_url(person), {"profile": Profile.ADMIN, "reason": "x", "approval_reference": "y"}
    )
    assert response.status_code == 403
    assert not ProfileAssignment.objects.filter(user=person).exists()


def test_lista_com_busca(client, login_as, make_user):
    login_as(Profile.ADMIN)
    make_user("maria.souza", full_name="Maria Souza")
    make_user("joao.lima", full_name="João Lima")
    content = client.get(reverse("accounts:people"), {"q": "souza"}).content.decode()
    assert "maria.souza" in content and "joao.lima" not in content


def test_detalhe_oferece_so_perfis_ainda_nao_ativos(client, login_as, make_user):
    login_as(Profile.ADMIN)
    person = make_user("ana", Profile.READER)
    response = client.get(reverse("accounts:person_detail", args=[person.pk]))
    choices = [code for code, _ in response.context["grant_form"].fields["profile"].choices]
    assert Profile.READER not in choices and Profile.ANALYST in choices
