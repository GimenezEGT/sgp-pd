"""E-mails imediatos, resumo diário, preferências e falhas (FR-007 a FR-009, SC-002)."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from sgp.notifications import services
from sgp.notifications.models import Notification, NotificationKind, NotificationStatus


@pytest.mark.req("010:FR-007")
def test_devolucao_gera_email_imediato_ao_elaborador(
    emails, submitted_entry, manager, django_capture_on_commit_callbacks, events
):
    from sgp.signatures import services as signatures

    with django_capture_on_commit_callbacks(execute=True):
        signatures.return_document(
            "subdocument", submitted_entry, by=manager, comment="Corrigir o tópico 3"
        )
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    analyst = submitted_entry.created_by
    analyst.refresh_from_db()
    assert message.to == [analyst.email]
    assert "Documento devolvido" in message.subject and "Corrigir o tópico 3" in message.body
    assert (
        Notification.objects.get(kind=NotificationKind.RETURNED).status == NotificationStatus.SENT
    )
    assert len(events("notifications.sent")) == 1


@pytest.mark.req("010:FR-007")
@pytest.mark.req("010:FR-008")
def test_aprovacao_avisa_elaborador_e_lider_e_respeita_preferencia(
    emails,
    submitted_entry,
    analyst,
    manager,
    project,
    signing,
    django_capture_on_commit_callbacks,
    events,
):
    from sgp.signatures import services as signatures

    services.set_preferences(analyst, [NotificationKind.RETURNED, NotificationKind.STALLED])
    assert services.is_enabled(analyst, NotificationKind.PENDING_SIGNATURE)
    signing.enable(manager)
    with django_capture_on_commit_callbacks(execute=True):
        signatures.approve("subdocument", submitted_entry, by=manager, password=signing.password)
    assert [m.to for m in mail.outbox] == [["lider@exemplo.test"]]
    skipped = Notification.objects.get(user=analyst)
    assert skipped.status == NotificationStatus.SKIPPED and "desligado" in skipped.error
    assert (
        Notification.objects.filter(
            user=analyst, status=NotificationStatus.SKIPPED, kind=NotificationKind.APPROVED
        ).count()
        == 1
    )
    assert events("notifications.skipped")
    assert len(events("notifications.preference_changed")) == 1


@pytest.mark.req("010:FR-008")
def test_assinatura_pendente_nao_pode_ser_desligada(client, analyst):
    client.force_login(analyst)
    client.post(reverse("notifications:preferences"), {"ligadas": []})
    rows = {row["kind"]: row for row in services.preferences(analyst)}
    assert rows[NotificationKind.PENDING_SIGNATURE]["enabled"] is True
    assert rows[NotificationKind.PENDING_SIGNATURE]["locked"] is True
    assert rows[NotificationKind.APPROVED]["enabled"] is False
    page = client.get(reverse("notifications:preferences")).content.decode()
    assert "sempre ligada" in page


@pytest.mark.req("010:FR-007")
@pytest.mark.req("010:SC-002")
def test_resumo_diario_no_dia_seguinte_ao_prazo(
    emails, submitted_entry, analyst, manager, django_capture_on_commit_callbacks
):
    days = settings.REVIEW_ALERT_DAYS
    on_deadline = timezone.now() + timedelta(days=days)
    assert services.daily_digest(on_deadline) == []
    next_day = timezone.now() + timedelta(days=days + 1)
    with django_capture_on_commit_callbacks(execute=True):
        created = services.daily_digest(next_day)
    kinds = {n.user_id: n.kind for n in created if n.status != NotificationStatus.SKIPPED}
    assert kinds == {
        manager.pk: NotificationKind.PENDING_SIGNATURE,
        analyst.pk: NotificationKind.STALLED,
    }
    analyst.refresh_from_db()
    assert {tuple(m.to) for m in mail.outbox} == {("gestor@exemplo.test",), (analyst.email,)}
    assert "Resumo diário de pendências" in mail.outbox[0].subject
    assert services.daily_digest(next_day) == []


@pytest.mark.req("010:FR-007")
def test_resumo_inclui_caderno_atrasado_e_testemunha(emails, project, analyst, signing):
    from sgp.notebook import services as notebook

    open_entry = notebook.create_entry(project, by=analyst, data={"title": "Esquecida"})
    relevant = notebook.create_entry(
        project, by=analyst, data={"title": "Precisa de testemunha", "relevant": True}
    )
    signing.enable(analyst)
    notebook.sign_entry(relevant, by=analyst, password=signing.password)
    later = timezone.now() + timedelta(days=settings.NOTEBOOK_SIGN_DAYS + 1)
    items = services.digest_items(later)
    texts = {user.pk: [text for _, text, _ in rows] for user, rows in items.items()}
    assert any("Esquecida" in text for text in texts[analyst.pk])
    assert any("Precisa de testemunha" in text for text in texts[project.leader.pk])
    assert open_entry.pk


@pytest.mark.req("010:FR-009")
def test_sem_email_e_falha_ficam_registrados(
    project, analyst, monkeypatch, django_capture_on_commit_callbacks, events
):
    analyst.email = ""
    analyst.save(update_fields=["email"])
    services.create(analyst, NotificationKind.RETURNED, subject="s", body="b", dedup_key="t:1")
    assert Notification.objects.get(dedup_key="t:1").status == NotificationStatus.SKIPPED
    analyst.email = "analista@exemplo.test"
    analyst.save(update_fields=["email"])

    def broken(*args, **kwargs):
        raise OSError("SMTP fora do ar")

    monkeypatch.setattr("sgp.notifications.services.send_mail", broken)
    with django_capture_on_commit_callbacks(execute=True):
        services.create(analyst, NotificationKind.RETURNED, subject="s", body="b", dedup_key="t:2")
    failed = Notification.objects.get(dedup_key="t:2")
    assert failed.status == NotificationStatus.FAILED and failed.attempts == 3
    assert "SMTP fora do ar" in failed.error
    assert len(events("notifications.failed")) == 1
    assert (
        services.create(analyst, NotificationKind.RETURNED, subject="s", body="b", dedup_key="t:2")
        is None
    )
