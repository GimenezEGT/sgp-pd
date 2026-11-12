"""Minhas pendências (FR-004, FR-005)."""

from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from sgp.notebook.models import EntryStatus, NotebookEntry
from sgp.projects.models import ProjectStatus
from sgp.projects.permissions import accessible_projects
from sgp.signatures.models import Meaning, Signature
from sgp.subdocuments.models import Subdocument, SubdocumentStatus


def my_pending(user) -> dict:
    from sgp.signatures.services import is_approver, review_queue

    projects = accessible_projects(user).values("pk")
    elaborated = Signature.objects.filter(
        kind="subdocument", signer=user, meaning=Meaning.ELABORATED
    ).values("object_id")
    returned = (
        Subdocument.objects.filter(project__in=projects, status=SubdocumentStatus.RETURNED)
        .filter(Q(created_by=user) | Q(pk__in=elaborated))
        .select_related("project", "subdocument_type")
        .order_by("project__code", "pk")
    )
    returned_projects = (
        accessible_projects(user)
        .filter(leader=user, status=ProjectStatus.RETURNED)
        .order_by("code", "pk")
    )
    limit = timezone.now() - timedelta(days=int(getattr(settings, "NOTEBOOK_SIGN_DAYS", 7)))
    my_entries = [
        {"entry": entry, "overdue": entry.created_at < limit}
        for entry in NotebookEntry.objects.filter(author=user, status=EntryStatus.OPEN)
        .select_related("project")
        .order_by("created_at")
    ]
    witness = (
        NotebookEntry.objects.filter(project__in=projects, status=EntryStatus.SIGNED, relevant=True)
        .exclude(author=user)
        .select_related("project", "author")
        .order_by("signed_at")
    )
    approvals = review_queue(user) if is_approver(user) else []
    return {
        "approvals": approvals,
        "returned": list(returned),
        "returned_projects": list(returned_projects),
        "entries": my_entries,
        "witness": list(witness),
        "total": len(approvals)
        + len(returned)
        + len(returned_projects)
        + len(my_entries)
        + len(witness),
    }
