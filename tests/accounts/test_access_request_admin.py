"""Decisão das solicitações de acesso pelo Administrador (FR-016)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.models import AccessRequest
from sgp.accounts.profiles import Profile
from sgp.accounts.services import create_access_request, decide_access_request
from sgp.audit.models import AuditEvent

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-016")]


def test_administrador_ve_pendentes_e_decide(client, login_as, make_user):
    admin = login_as(Profile.ADMIN)
    person = make_user("sem.perfil")
    request = create_access_request(person, "Preciso consultar o projeto X")
    page = client.get(reverse("accounts:access_requests")).content.decode()
    assert "Preciso consultar o projeto X" in page
    response = client.post(
        reverse("accounts:decide_access_request", args=[request.pk]),
        {"decision": "granted", "reason": "Perfil Leitor concedido"},
    )
    assert response.status_code == 302
    request.refresh_from_db()
    assert request.status == AccessRequest.Status.GRANTED and request.decided_by == admin
    event = AuditEvent.objects.get(event_type="accounts.access_request_decided")
    assert event.old_value == {"situacao": "pending"} and event.new_value == {"situacao": "granted"}


def test_decisao_exige_motivo_e_e_unica(make_user):
    admin = make_user("admin", Profile.ADMIN)
    request = create_access_request(make_user("x"), "Justificativa suficiente")
    with pytest.raises(ValidationError):
        decide_access_request(request, by=admin, decision="rejected", reason="")
    decide_access_request(request, by=admin, decision="rejected", reason="Fora do escopo")
    with pytest.raises(ValidationError, match="já foi decidida"):
        decide_access_request(request, by=admin, decision="granted", reason="Mudou de ideia")


def test_decisao_invalida_e_recusada(make_user):
    admin = make_user("admin", Profile.ADMIN)
    request = create_access_request(make_user("x"), "Justificativa suficiente")
    with pytest.raises(ValidationError):
        decide_access_request(request, by=admin, decision="talvez", reason="?")


def test_somente_administrador_ve_solicitacoes(client, login_as):
    login_as(Profile.QUALITY)
    assert client.get(reverse("accounts:access_requests")).status_code == 403
