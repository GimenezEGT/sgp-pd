"""Exportação para a revisão periódica de acessos (FR-014 da feature 014)."""

import csv
import io

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from openpyxl import load_workbook

from sgp.operations import access_review


@pytest.mark.django_db
@pytest.mark.req("014:FR-014")
def test_revisao_de_acessos_csv_e_xlsx(client, it_admin, quality, analyst, make_project, events):
    project = make_project()
    name, content_type, data = access_review.export("csv", by=quality)
    assert name.endswith(".csv") and content_type.startswith("text/csv")
    rows = list(csv.reader(io.StringIO(data.decode("utf-8")), delimiter=";"))
    assert rows[0] == access_review.COLUMNS
    by_person = {row[0]: row for row in rows[1:]}
    admin_row = by_person["ti.admin"]
    assert admin_row[3] == "sim" and "Administrador do sistema (desde" in admin_row[4]
    assert admin_row[6] == "nunca"
    leader_row = by_person[project.leader.username]
    assert (project.code or project.title) in leader_row[5]
    _, _, xlsx = access_review.export("xlsx", by=it_admin)
    sheet = load_workbook(io.BytesIO(xlsx)).active
    assert sheet.title == "Revisão de acessos" and sheet.cell(1, 1).value == "pessoa"
    assert len(events("operations.access_review_exported")) == 2
    with pytest.raises(PermissionDenied):
        access_review.export("csv", by=analyst)
    with pytest.raises(ValidationError):
        access_review.export("pdf", by=it_admin)
    client.force_login(analyst)
    assert client.get(reverse("operations:access_review") + "?formato=csv").status_code == 403
    client.force_login(quality)
    response = client.get(reverse("operations:access_review") + "?formato=xlsx")
    assert response.status_code == 200 and "attachment" in response["Content-Disposition"]
