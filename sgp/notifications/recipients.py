"""Quem recebe cada notificação (research R7 da feature 010)."""

from sgp.signatures.models import DocumentKind, Meaning, Signature


def _unique(users) -> list:
    seen, out = set(), []
    for user in users:
        if user is not None and user.pk not in seen:
            seen.add(user.pk)
            out.append(user)
    return out


def document(kind: str, object_id):
    """(registro, projeto, rótulo) do documento da trilha, ou (None, None, "")."""
    from sgp.projects.models import BusinessPlan, ProjectCharter
    from sgp.subdocuments.models import Subdocument

    model = {
        DocumentKind.SUBDOCUMENT: Subdocument,
        DocumentKind.CHARTER: ProjectCharter,
        DocumentKind.BUSINESS_PLAN: BusinessPlan,
    }.get(kind)
    if model is None:
        return None, None, ""
    obj = model.objects.select_related("project").filter(pk=object_id).first()
    if obj is None:
        return None, None, ""
    return obj, obj.project, str(obj)


def elaborator(kind: str, obj):
    """Quem assinou como elaborador (a assinatura mais recente); senão, o criador ou o líder."""
    signature = (
        Signature.objects.filter(kind=kind, object_id=obj.pk, meaning=Meaning.ELABORATED)
        .select_related("signer")
        .order_by("-signed_at", "-pk")
        .first()
    )
    if signature:
        return signature.signer
    if kind == DocumentKind.SUBDOCUMENT:
        return obj.created_by
    return obj.project.leader


def for_returned(kind: str, obj) -> list:
    return _unique([elaborator(kind, obj)])


def for_approved(kind: str, obj) -> list:
    return _unique([elaborator(kind, obj), obj.project.leader])
