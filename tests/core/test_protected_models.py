import pytest

from sgp.accounts.models import LoginAttempt, ProfileAssignment, User
from sgp.accounts.profiles import Profile
from sgp.audit.services import record_event
from sgp.core.models import DeletionNotAllowedError, ImmutableRecordError

pytestmark = [pytest.mark.django_db, pytest.mark.req("001:FR-026")]


def test_pessoa_nao_e_apagada(make_user):
    user = make_user("nao.apaga")
    with pytest.raises(DeletionNotAllowedError):
        user.delete()
    with pytest.raises(DeletionNotAllowedError):
        User.objects.filter(pk=user.pk).delete()
    assert User.objects.filter(pk=user.pk).exists()


def test_concessao_de_perfil_nao_e_apagada(make_user):
    user = make_user("com.perfil", Profile.READER)
    assignment = ProfileAssignment.objects.get(user=user)
    with pytest.raises(DeletionNotAllowedError):
        assignment.delete()
    with pytest.raises(DeletionNotAllowedError):
        ProfileAssignment.objects.all().delete()


@pytest.mark.req("001:FR-019")
def test_registro_append_only_nao_e_alterado():
    attempt = LoginAttempt.objects.create(username="x", result=LoginAttempt.Result.FAILURE)
    attempt.ip_address = "10.0.0.1"
    with pytest.raises(ImmutableRecordError):
        attempt.save()
    with pytest.raises(ImmutableRecordError):
        LoginAttempt.objects.filter(pk=attempt.pk).update(ip_address="10.0.0.2")
    with pytest.raises(DeletionNotAllowedError):
        attempt.delete()


@pytest.mark.req("001:FR-019")
def test_evento_de_auditoria_nao_e_alterado_pela_aplicacao():
    event = record_event("audit.exported", actor=None, new_value={"formato": "csv"})
    event.reason = "alterado"
    with pytest.raises(ImmutableRecordError):
        event.save()
    with pytest.raises(ImmutableRecordError):
        type(event).objects.filter(pk=event.pk).update(reason="alterado")
    with pytest.raises(DeletionNotAllowedError):
        event.delete()


def test_senha_nunca_utilizavel(make_user):
    user = make_user("sem.senha")
    assert not user.has_usable_password()
    user.password = ""
    user.save()
    assert not user.has_usable_password()
