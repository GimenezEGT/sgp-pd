"""Exportação para a revisão periódica de acessos (FR-014 da feature 014)."""

import csv
import io

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from openpyxl import Workbook

from sgp.accounts.models import ProfileAssignment
from sgp.accounts.profiles import Profile, active_profiles
from sgp.audit.services import record_event
from sgp.projects.models import ProjectMember

COLUMNS = [
    "pessoa",
    "nome",
    "email",
    "conta_ativa",
    "perfis_ativos",
    "papeis_em_projetos",
    "ultimo_acesso",
]
FORMATS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
VIEWERS = {Profile.ADMIN, Profile.QUALITY}


def can_view(user) -> bool:
    return bool(VIEWERS & active_profiles(user))


def _name(user) -> str:
    return (user.get_full_name() or user.username) if user else "sistema"


def rows() -> list[dict]:
    assignments: dict[int, list[str]] = {}
    for item in (
        ProfileAssignment.objects.filter(revoked_at__isnull=True)
        .select_related("granted_by")
        .order_by("profile")
    ):
        assignments.setdefault(item.user_id, []).append(
            f"{item.get_profile_display()} (desde "
            f"{timezone.localtime(item.granted_at):%d/%m/%Y}, por {_name(item.granted_by)})"
        )
    memberships: dict[int, list[str]] = {}
    for member in (
        ProjectMember.objects.active().select_related("project").order_by("project__code")
    ):
        memberships.setdefault(member.user_id, []).append(
            f"{member.project.code or member.project.title} ({member.role})"
        )
    result = []
    for user in get_user_model().objects.order_by("username"):
        result.append(
            {
                "pessoa": user.username,
                "nome": user.get_full_name(),
                "email": user.email,
                "conta_ativa": "sim" if user.is_active else "não",
                "perfis_ativos": "; ".join(assignments.get(user.pk, [])),
                "papeis_em_projetos": "; ".join(memberships.get(user.pk, [])),
                "ultimo_acesso": f"{timezone.localtime(user.last_login):%d/%m/%Y %H:%M}"
                if user.last_login
                else "nunca",
            }
        )
    return result


def export(fmt: str, *, by, request=None) -> tuple[str, str, bytes]:
    if not can_view(by):
        raise PermissionDenied("Só a TI e a Garantia da Qualidade exportam a revisão de acessos.")
    if fmt not in FORMATS:
        raise ValidationError("Escolha o formato csv ou xlsx.")
    data_rows = rows()
    stamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
    name = f"sgp-pd-revisao-de-acessos-{stamp}.{fmt}"
    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(COLUMNS)
        for row in data_rows:
            writer.writerow([row[c] for c in COLUMNS])
        data = buffer.getvalue().encode("utf-8")
    else:
        book = Workbook()
        sheet = book.active
        sheet.title = "Revisão de acessos"
        sheet.append(COLUMNS)
        for row in data_rows:
            sheet.append([row[c] for c in COLUMNS])
        out = io.BytesIO()
        book.save(out)
        data = out.getvalue()
    record_event(
        "operations.access_review_exported",
        actor=by,
        object_type="operations.access_review",
        object_id=fmt,
        object_repr=name,
        new_value={"formato": fmt, "pessoas": len(data_rows)},
        request=request,
    )
    return name, FORMATS[fmt], data
