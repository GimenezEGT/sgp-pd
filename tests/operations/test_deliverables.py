"""Cópias fora do alcance da interface e roteiros versionados com o sistema (FR-010, FR-015 da
feature 014)."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from sgp.operations import installation, operation, urls
from sgp.operations.models import BackupRun, BackupStatus

ROOT = Path(settings.BASE_DIR)


@pytest.mark.req("014:FR-010")
def test_nenhuma_rota_baixa_ou_restaura_copias():
    names = {pattern.name for pattern in urls.urlpatterns}
    assert names == {
        "panel",
        "backup_now",
        "restore_now",
        "qualify_installation",
        "qualify_operation",
        "report",
        "access_review",
    }
    backup_dir = Path(settings.BACKUP_DIR).resolve()
    for served in (Path(settings.STATIC_ROOT).resolve(), Path(settings.MEDIA_ROOT).resolve()):
        assert served != backup_dir and served not in backup_dir.parents


@pytest.mark.django_db
@pytest.mark.req("014:FR-010")
def test_painel_nao_oferece_o_conteudo_das_copias(client, it_admin, backup_dir):
    BackupRun.objects.create(
        status=BackupStatus.SUCCESS, label="20261112-010000", finished_at=timezone.now()
    )
    client.force_login(it_admin)
    page = client.get(reverse("operations:panel")).content.decode()
    assert "20261112-010000" in page
    assert "banco.dump" not in page and "manifesto.json" not in page
    assert client.get("/operacao/copias/20261112-010000/banco.dump").status_code == 404


def _codes(text: str, prefix: str) -> set[str]:
    return set(re.findall(rf"\b{prefix}-\d{{2}}\b", text))


@pytest.mark.req("014:FR-015")
def test_roteiros_versionados_e_coerentes_com_as_qualificacoes():
    iq = (ROOT / "docs" / "validacao" / "iq-roteiro.md").read_text("utf-8")
    oq = (ROOT / "docs" / "validacao" / "oq-roteiro.md").read_text("utf-8")
    recovery = (ROOT / "docs" / "operacao" / "recuperacao.md").read_text("utf-8")
    index = (ROOT / "docs" / "validacao" / "README.md").read_text("utf-8")
    assert "qualificacao_instalacao" in iq and "copia_seguranca" in iq
    assert _codes(iq, "IQ") == {code for code, _, _ in installation.ITEMS}
    assert "qualificacao_operacao" in oq and "scripts/verificar.sh" in oq
    expected_oq = {code for code, _, _ in operation.ITEMS} | {"OQ-11"}
    assert _codes(oq, "OQ") == expected_oq
    for section in ("Assinatura eletrônica", "Trilha de auditoria", "Geração de documentos"):
        assert section in oq
    assert "pg_restore" in recovery and "sgp_anterior" in recovery
    for deliverable in ("iq-roteiro.md", "oq-roteiro.md", "matriz-rastreabilidade.md"):
        assert deliverable in index
