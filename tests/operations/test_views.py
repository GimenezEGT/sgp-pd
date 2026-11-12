"""Painel de operação: permissões, pedidos enfileirados e download do relatório (FR-007, FR-009,
FR-013 da feature 014)."""

import pytest
from django.urls import reverse
from django.utils import timezone

from sgp.operations import tasks
from sgp.operations.models import BackupRun, BackupStatus


@pytest.fixture
def delayed(monkeypatch):
    calls = []
    for name in ("backup", "restore_test", "qualification"):
        task = getattr(tasks, name)
        monkeypatch.setattr(task, "delay", lambda *a, _name=name, **kw: calls.append((_name, kw)))
    return calls


@pytest.mark.django_db
@pytest.mark.req("014:FR-007")
def test_painel_para_ti_e_qualidade(client, it_admin, quality, analyst, backup_dir):
    BackupRun.objects.create(
        status=BackupStatus.FAILED, label="20261112-010000", error="Destino indisponível"
    )
    client.force_login(it_admin)
    page = client.get(reverse("operations:panel")).content.decode()
    assert "Fazer cópia agora" in page and "Destino indisponível" in page
    assert "Sem cópia de segurança bem-sucedida" in page
    assert "Nenhum teste de restauração executado" in page
    client.force_login(quality)
    page = client.get(reverse("operations:panel")).content.decode()
    assert "Fazer cópia agora" not in page and "qualificação de operação" in page
    client.force_login(analyst)
    assert client.get(reverse("operations:panel")).status_code == 403


@pytest.mark.django_db
@pytest.mark.req("014:FR-009")
def test_pedidos_de_copia_e_teste_so_da_ti(
    client, it_admin, quality, backup_dir, delayed, events, django_capture_on_commit_callbacks
):
    client.force_login(quality)
    assert client.post(reverse("operations:backup_now")).status_code == 403
    assert client.post(reverse("operations:restore_now")).status_code == 403
    assert client.post(reverse("operations:qualify_installation")).status_code == 403
    client.force_login(it_admin)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(reverse("operations:backup_now"), follow=True)
    assert "Cópia de segurança pedida" in response.content.decode()
    assert delayed == [("backup", {"kind": "manual", "user_id": it_admin.pk})]
    response = client.post(reverse("operations:restore_now"), follow=True)
    assert "Não há cópia de segurança bem-sucedida" in response.content.decode()
    BackupRun.objects.create(
        status=BackupStatus.SUCCESS, label="20261112-020000", finished_at=timezone.now()
    )
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("operations:restore_now"))
    assert delayed[-1] == ("restore_test", {"kind": "manual", "user_id": it_admin.pk})
    assert events("operations.backup_requested") and events("operations.restore_requested")


@pytest.mark.django_db
@pytest.mark.req("014:FR-012")
@pytest.mark.req("014:FR-013")
def test_qualidade_pede_a_oq_e_baixa_o_relatorio(
    client, quality, analyst, delayed, events, django_capture_on_commit_callbacks, monkeypatch
):
    from sgp.operations import operation, qualification

    client.force_login(quality)
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("operations:qualify_operation"))
    assert delayed == [("qualification", {"kind": "operation", "user_id": quality.pk})]
    assert events("operations.qualification_requested")
    monkeypatch.setattr(operation, "run", lambda: [])
    run = qualification.execute("operation", by=quality)
    response = client.get(reverse("operations:report", args=[run.pk]))
    assert response.status_code == 200 and response["Content-Type"] == "application/pdf"
    assert b"".join(response.streaming_content).startswith(b"%PDF-")
    assert events("operations.report_downloaded")
    client.force_login(analyst)
    assert client.post(reverse("operations:qualify_operation")).status_code == 403
    assert client.get(reverse("operations:report", args=[run.pk])).status_code == 403
