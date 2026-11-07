"""Designação do primeiro Administrador na implantação."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from sgp.accounts.models import ProfileAssignment, User
from sgp.accounts.profiles import Profile
from sgp.audit.models import AuditEvent

pytestmark = pytest.mark.django_db


@pytest.mark.req("001:FR-010")
def test_designa_primeiro_administrador_com_motivo_e_aprovacao():
    call_command("grant_initial_admin", "Admin.TI", motivo="Implantação", aprovacao="Gestão da TI")
    user = User.objects.get(username="admin.ti")
    assignment = ProfileAssignment.objects.get(user=user)
    assert assignment.profile == Profile.ADMIN and assignment.granted_by is None
    assert assignment.approval_reference == "Gestão da TI"
    types = list(AuditEvent.objects.values_list("event_type", flat=True))
    assert types == ["accounts.user_created", "accounts.profile_granted"]
    assert AuditEvent.objects.get(event_type="accounts.profile_granted").actor_username == "sistema"


def test_recusa_quando_ja_existe_administrador(make_user):
    make_user("chefe", Profile.ADMIN)
    with pytest.raises(CommandError, match="Já existe Administrador ativo"):
        call_command("grant_initial_admin", "outro", motivo="x", aprovacao="y")
    assert not User.objects.filter(username="outro").exists()


def test_recusa_login_vazio():
    with pytest.raises(CommandError):
        call_command("grant_initial_admin", "  ", motivo="x", aprovacao="y")
