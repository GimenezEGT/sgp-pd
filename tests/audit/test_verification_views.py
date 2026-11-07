"""Tela de integridade, verificação sob demanda, alerta e comando (FR-021, FR-022)."""

import pytest
from django.core.management import call_command
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.audit.models import ChainVerification
from sgp.audit.services import record_event, verify_chain
from tests.db_helpers import tamper

pytestmark = pytest.mark.django_db


@pytest.mark.req("001:FR-021")
@pytest.mark.parametrize("profile", [Profile.QUALITY, Profile.ADMIN])
def test_qualidade_e_administrador_abrem_e_verificam(client, login_as, profile):
    login_as(profile)
    assert client.get(reverse("audit:integrity")).status_code == 200
    response = client.post(reverse("audit:verify_now"), follow=True)
    assert response.status_code == 200
    verification = ChainVerification.objects.get()
    assert verification.trigger == ChainVerification.Trigger.MANUAL
    assert verification.triggered_by is not None
    assert "Íntegra" in response.content.decode()


@pytest.mark.req("001:FR-021")
@pytest.mark.parametrize("profile", [Profile.RD_MANAGER, Profile.ANALYST, Profile.READER])
def test_demais_perfis_nao_verificam(client, login_as, profile):
    login_as(profile)
    assert client.get(reverse("audit:integrity")).status_code == 403
    assert client.post(reverse("audit:verify_now")).status_code == 403
    assert not ChainVerification.objects.exists()


@pytest.mark.req("001:FR-022")
def test_alerta_aparece_para_qualidade_enquanto_houver_quebra(client, login_as):
    record_event("audit.exported", actor=None)
    record_event("audit.exported", actor=None)
    tamper("UPDATE audit_auditevent SET reason = 'x' WHERE seq = 1")
    verify_chain()
    login_as(Profile.QUALITY)
    content = client.get(reverse("core:home")).content.decode()
    assert "Quebra de integridade na trilha de auditoria" in content


@pytest.mark.req("001:FR-022")
def test_alerta_nao_aparece_para_quem_nao_verifica(client, login_as):
    record_event("audit.exported", actor=None)
    tamper("UPDATE audit_auditevent SET reason = 'x' WHERE seq = 1")
    verify_chain()
    login_as(Profile.READER)
    content = client.get(reverse("core:home")).content.decode()
    assert "Quebra de integridade" not in content


@pytest.mark.req("001:FR-021")
def test_comando_retorna_1_quando_ha_quebra(capsys):
    record_event("audit.exported", actor=None)
    call_command("verify_audit_chain")
    assert "Íntegra" in capsys.readouterr().out
    tamper("UPDATE audit_auditevent SET reason = 'x' WHERE seq = 1")
    with pytest.raises(SystemExit) as exit_info:
        call_command("verify_audit_chain", "--agendada")
    assert exit_info.value.code == 1
    output = capsys.readouterr().out
    assert "evento 1: Conteúdo alterado" in output and "content_altered" not in output
    assert ChainVerification.objects.first().trigger == ChainVerification.Trigger.SCHEDULED


@pytest.mark.req("001:FR-021")
def test_tela_mostra_tipo_de_quebra_em_portugues(client, login_as):
    record_event("audit.exported", actor=None)
    record_event("audit.exported", actor=None)
    tamper("DELETE FROM audit_auditevent WHERE seq = 1")
    verify_chain()
    login_as(Profile.QUALITY)
    content = client.get(reverse("audit:integrity")).content.decode()
    assert "Lacuna na sequência" in content and "Encadeamento rompido" in content
    assert "sequence_gap" not in content and "chain_broken" not in content
