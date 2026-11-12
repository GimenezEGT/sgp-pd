"""Outbox na transação da aprovação, envio único, falha, reprocessamento e fila (FR-004, FR-005,
FR-007, FR-009, SC-001, SC-004)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone

from sgp.integrations import services
from sgp.integrations.models import IntegrationMessage, MessageStatus


def _approve(entry, manager, signing, capture):
    from sgp.signatures import services as signatures

    signing.enable(manager)
    with capture(execute=True):
        signatures.approve("subdocument", entry, by=manager, password=signing.password)


@pytest.mark.req("012:FR-004")
def test_aprovacao_gera_mensagem_do_documento_na_mesma_transacao(
    submitted_entry, manager, signing, django_capture_on_commit_callbacks
):
    _approve(submitted_entry, manager, signing, django_capture_on_commit_callbacks)
    message = IntegrationMessage.objects.get(record_type="documento")
    assert message.idempotency_key == f"documento:{submitted_entry.pk}:1"
    payload = message.payload
    assert payload["tipo_subdocumento"] == "Entrada de Projeto" and payload["versao_documento"] == 1
    assert payload["elaborador"] and payload["aprovador"] and len(payload["resumo_conteudo"]) == 64
    assert message.status == MessageStatus.WAITING_CONFIG and message.attempts == 0


@pytest.mark.req("012:FR-005")
@pytest.mark.req("012:FR-009")
@pytest.mark.req("012:SC-001")
def test_envio_unico_mesmo_com_reenvio(
    gateway,
    configured,
    submitted_entry,
    manager,
    signing,
    django_capture_on_commit_callbacks,
    events,
):
    _approve(submitted_entry, manager, signing, django_capture_on_commit_callbacks)
    message = IntegrationMessage.objects.get(record_type="documento")
    assert message.status == MessageStatus.SENT and message.mapping_version == configured.version
    IntegrationMessage.objects.filter(pk=message.pk).update(status=MessageStatus.PENDING)
    services.dispatch(message.pk)
    stored = gateway.records["TESTE_DOCUMENTO"]
    assert list(stored) == [message.idempotency_key]
    assert stored[message.idempotency_key]["TIPO"] == "Entrada de Projeto"
    assert services.enqueue("documento", message.idempotency_key, {}) is None
    assert len(events("integration.sent")) == 2


@pytest.mark.req("012:FR-005")
@pytest.mark.req("012:FR-009")
@pytest.mark.req("012:SC-004")
def test_falha_com_espera_crescente_e_reprocessamento(
    gateway,
    configured,
    submitted_entry,
    manager,
    signing,
    it_admin,
    django_capture_on_commit_callbacks,
    events,
    settings,
):
    from sgp.subdocuments.models import SubdocumentStatus

    settings.INTEGRATION_MAX_ATTEMPTS = 3
    gateway.fail = 10
    _approve(submitted_entry, manager, signing, django_capture_on_commit_callbacks)
    submitted_entry.refresh_from_db()
    assert submitted_entry.status == SubdocumentStatus.APPROVED
    message = IntegrationMessage.objects.get(record_type="documento")
    assert message.status == MessageStatus.ERROR and message.attempts == 1
    assert timedelta(seconds=50) < message.next_attempt_at - timezone.now() <= timedelta(minutes=1)
    services.process_due(timezone.now())
    message.refresh_from_db()
    assert message.attempts == 1
    services.process_due(timezone.now() + timedelta(minutes=2))
    message.refresh_from_db()
    assert message.attempts == 2 and message.next_attempt_at - timezone.now() > timedelta(minutes=1)
    services.process_due(timezone.now() + timedelta(minutes=10))
    message.refresh_from_db()
    assert message.attempts == 3 and message.next_attempt_at is None
    services.process_due(timezone.now() + timedelta(hours=1))
    message.refresh_from_db()
    assert message.attempts == 3
    gateway.fail = 0
    with pytest.raises(PermissionDenied):
        services.reprocess(message, by=manager)
    sent = services.reprocess(message, by=it_admin)
    assert sent.status == MessageStatus.SENT and sent.attempts == 4
    failed = [e for e in events("integration.failed") if e.object_id == str(message.pk)]
    assert len(failed) == 3 and len(events("integration.reprocessed")) == 1


@pytest.mark.req("012:FR-004")
def test_projeto_aprovado_e_estudo_bloqueado_geram_registros(signed_project, member, manager):
    from sgp.audit.services import record_event
    from sgp.studies import services as studies
    from sgp.vocab.models import get_term

    project_message = IntegrationMessage.objects.get(record_type="projeto")
    assert project_message.payload["codigo_projeto"] == signed_project.code
    study = studies.create_study(
        signed_project,
        by=member,
        data={"study_type": get_term("tipo-estudo", "repetibilidade"), "title": "Estudo fictício"},
    )
    record_event("studies.locked", actor=manager, obj=study, project_id=signed_project.pk)
    result = IntegrationMessage.objects.get(record_type="resultado_estudo")
    assert (
        result.payload["titulo"] == "Estudo fictício"
        and result.payload["conclusao"] == "sem critério"
    )


@pytest.mark.req("012:FR-007")
def test_fila_so_para_a_ti(
    client, it_admin, member, submitted_entry, manager, signing, django_capture_on_commit_callbacks
):
    _approve(submitted_entry, manager, signing, django_capture_on_commit_callbacks)
    client.force_login(it_admin)
    page = client.get(reverse("integrations:queue")).content.decode()
    assert "Aguardando configuração" in page and f"documento:{submitted_entry.pk}:1" in page
    client.force_login(member)
    assert client.get(reverse("integrations:queue")).status_code == 403
