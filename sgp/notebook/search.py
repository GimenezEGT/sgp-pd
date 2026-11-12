"""Linha do tempo e busca do caderno (FR-012, FR-013; research R10)."""

from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db.models import Q
from django.utils import timezone

from sgp.projects.permissions import accessible_projects

from . import richtext
from .models import Addendum, EntryMaterial, EntryStatus, MaterialKind, NotebookEntry, NotebookLink

PAGE_SIZE = 20
SITUATIONS = (
    ("open", "Aberta"),
    ("overdue", "Atrasada"),
    ("signed", "Assinada"),
    ("awaiting_witness", "Aguardando testemunha"),
    ("witnessed", "Testemunhada"),
)
SITUATION_LABELS = dict(SITUATIONS)


def sign_days() -> int:
    return int(getattr(settings, "NOTEBOOK_SIGN_DAYS", 7))


def situation(entry, now=None) -> str:
    now = now or timezone.now()
    if entry.status == EntryStatus.OPEN:
        overdue = entry.created_at < now - timedelta(days=sign_days())
        return "overdue" if overdue else "open"
    if entry.status == EntryStatus.SIGNED:
        return "awaiting_witness" if entry.relevant else "signed"
    return "witnessed"


@dataclass
class Filters:
    q: str = ""
    project: int | None = None
    lot: str = ""
    sample: str = ""
    author: str = ""
    date_from: date | None = None
    date_to: date | None = None
    situation: str = ""
    older_than: int | None = None


def _situation_filter(code: str, now) -> Q:
    limit = now - timedelta(days=sign_days())
    return {
        "open": Q(status=EntryStatus.OPEN, created_at__gte=limit),
        "overdue": Q(status=EntryStatus.OPEN, created_at__lt=limit),
        "signed": Q(status=EntryStatus.SIGNED, relevant=False),
        "awaiting_witness": Q(status=EntryStatus.SIGNED, relevant=True),
        "witnessed": Q(status=EntryStatus.WITNESSED),
    }.get(code, Q())


def search(user, filters: Filters, now=None):
    """Entradas dos projetos acessíveis que atendem os filtros, da mais recente para a mais antiga."""
    now = now or timezone.now()
    queryset = NotebookEntry.objects.filter(
        project__in=accessible_projects(user).values("pk")
    ).select_related("project", "author")
    if filters.project:
        queryset = queryset.filter(project_id=filters.project)
    text = richtext.fold(filters.q).strip()
    if text:
        query = SearchQuery(text, config="portuguese", search_type="websearch")
        queryset = queryset.filter(
            Q(search_vector=query)
            | Q(pk__in=Addendum.objects.filter(search_vector=query).values("entry_id"))
        )
    if filters.lot.strip():
        code = filters.lot.strip()
        queryset = queryset.filter(
            Q(
                pk__in=EntryMaterial.objects.filter(
                    kind=MaterialKind.LOT, code__iexact=code, removed_at__isnull=True
                ).values("entry_id")
            )
            | Q(
                pk__in=NotebookLink.objects.filter(
                    lot__code__iexact=code, removed_at__isnull=True
                ).values("entry_id")
            )
        )
    if filters.sample.strip():
        queryset = queryset.filter(
            pk__in=EntryMaterial.objects.filter(
                kind=MaterialKind.SAMPLE,
                code__iexact=filters.sample.strip(),
                removed_at__isnull=True,
            ).values("entry_id")
        )
    if filters.author.strip():
        name = filters.author.strip()
        queryset = queryset.filter(
            Q(author__username__iexact=name) | Q(author__full_name__icontains=name)
        )
    if filters.date_from:
        queryset = queryset.filter(created_at__date__gte=filters.date_from)
    if filters.date_to:
        queryset = queryset.filter(created_at__date__lte=filters.date_to)
    if filters.situation in SITUATION_LABELS:
        queryset = queryset.filter(_situation_filter(filters.situation, now))
    if filters.older_than is not None:
        queryset = queryset.filter(
            status=EntryStatus.OPEN, created_at__lt=now - timedelta(days=filters.older_than)
        )
    return queryset.order_by("-created_at", "-pk")


def annotate(entries, now=None) -> list[dict]:
    now = now or timezone.now()
    rows = []
    for entry in entries:
        code = situation(entry, now)
        rows.append(
            {
                "entry": entry,
                "situation": code,
                "situation_label": SITUATION_LABELS[code],
                "excerpt": richtext.excerpt(entry.conclusion or entry.objective or entry.results),
                "days_open": (now - entry.created_at).days if entry.is_open else None,
            }
        )
    return rows
