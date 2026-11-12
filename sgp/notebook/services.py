"""Regras do caderno de laboratório (feature 008).

Toda alteração passa por aqui e registra o evento na mesma transação. A reautenticação da 005 é
chamada fora da transação, para que as tentativas de senha fiquem gravadas mesmo quando a
assinatura é recusada.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.catalog.kinds import get_kind
from sgp.files.storage import store_upload
from sgp.projects.models import Project
from sgp.signatures.reauth import reauthenticate

from . import permissions, richtext
from .content import addendum_hash, entry_hash
from .models import (
    TEXT_FIELDS,
    TEXT_LABELS,
    Addendum,
    EntryAttachment,
    EntryMaterial,
    EntryStatus,
    EntryTemplate,
    LinkKind,
    LinkTarget,
    MaterialKind,
    NotebookEntry,
    NotebookLink,
    NotebookSignature,
    SignatureRole,
)

ATTACHMENT_KINDS = ("pdf", "png", "jpeg", "csv", "xlsx")
IMAGE_KINDS = ("png", "jpeg")
MATERIAL_LOOKUP = {
    MaterialKind.LOT: ("lotes", "code", "lot"),
    MaterialKind.MATERIAL: ("insumos", "code", "material"),
    MaterialKind.SAMPLE: ("amostras", "identifier", "sample"),
}
CONCURRENT_EDIT = (
    "A entrada foi alterada por outra gravação enquanto você editava; abra de novo e refaça."
)


def _event(event_type: str, entry, by, **kwargs):
    return record_event(event_type, actor=by, obj=entry, project_id=entry.project_id, **kwargs)


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:] + "." if text else ""


def _require(allowed: bool, message: str) -> None:
    if not allowed:
        raise PermissionDenied(message)


def _locked_entry(entry) -> NotebookEntry:
    return NotebookEntry.objects.select_for_update().select_related("project", "author").get(
        pk=entry.pk
    )


def image_file_ids(entry) -> set[int]:
    """Arquivos de imagem ativos da entrada: as únicas imagens aceitas no texto."""
    return set(
        entry.attachments.filter(
            removed_at__isnull=True, file__content_type__in=("image/png", "image/jpeg")
        ).values_list("file_id", flat=True)
    )


def build_search_text(entry) -> str:
    codes = entry.materials.filter(removed_at__isnull=True).values_list("code", flat=True)
    parts = [entry.title, *(richtext.plain_text(getattr(entry, f)) for f in TEXT_FIELDS), *codes]
    return richtext.fold(" ".join(part for part in parts if part))


def _refresh_search(entry) -> None:
    entry.search_text = build_search_text(entry)
    NotebookEntry.objects.filter(pk=entry.pk).update(search_text=entry.search_text)


# ------------------------------------------------------------------ entradas


def create_entry(project: Project, *, by, data: dict) -> NotebookEntry:
    _require(
        permissions.can_create(by, project),
        "Só membros do projeto aberto com perfil Analista/Pesquisador ou Líder e o Gestor de P&D "
        "criam entradas no caderno.",
    )
    title = (data.get("title") or "").strip()
    if not title:
        raise ValidationError("Informe o título da entrada.")
    template = data.get("template")
    if template is not None and not (template.is_current and template.active):
        raise ValidationError("O modelo escolhido não está vigente e ativo.")
    relevant = bool(data.get("relevant"))
    now = timezone.now()
    with transaction.atomic():
        Project.objects.select_for_update().get(pk=project.pk)
        number = (
            NotebookEntry.objects.filter(project=project).aggregate(top=Max("number"))["top"] or 0
        ) + 1
        texts = {
            field: richtext.sanitize(getattr(template, field)) if template else ""
            for field in TEXT_FIELDS
        }
        entry = NotebookEntry(
            project=project,
            number=number,
            author=by,
            created_at=now,
            title=title[:300],
            template=template,
            relevant=relevant,
            relevant_by=by if relevant else None,
            relevant_at=now if relevant else None,
            updated_by=by,
            updated_at=now,
            **texts,
        )
        entry.search_text = richtext.fold(
            " ".join([title, *(richtext.plain_text(value) for value in texts.values())])
        )
        entry.save()
        _event(
            "notebook.created",
            entry,
            by,
            new_value={
                "numero": number,
                "titulo": entry.title,
                "modelo": template.name if template else None,
                "versao_modelo": template.version if template else None,
                "relevante": relevant,
            },
        )
    return entry


def update_entry(entry: NotebookEntry, *, by, data: dict, row_version=None) -> NotebookEntry:
    _require(
        permissions.can_edit_entry(by, entry),
        "Só o autor altera a entrada, e só enquanto ela está aberta.",
    )
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(
            permissions.can_edit_entry(by, entry),
            "Só o autor altera a entrada, e só enquanto ela está aberta.",
        )
        if row_version is not None and str(row_version) != str(entry.row_version):
            raise ValidationError(CONCURRENT_EDIT)
        images = image_file_ids(entry)
        changes_old, changes_new = {}, {}
        title = (data.get("title", entry.title) or "").strip()
        if not title:
            raise ValidationError("Informe o título da entrada.")
        if title[:300] != entry.title:
            changes_old["titulo"], changes_new["titulo"] = entry.title, title[:300]
            entry.title = title[:300]
        for field in TEXT_FIELDS:
            if field not in data:
                continue
            clean = richtext.sanitize(data[field], image_ids=images)
            if clean != getattr(entry, field):
                label = TEXT_LABELS[field].lower()
                changes_old[label], changes_new[label] = getattr(entry, field), clean
                setattr(entry, field, clean)
        if not changes_new:
            return entry
        entry.search_text = build_search_text(entry)
        entry.updated_by = by
        entry.updated_at = timezone.now()
        entry.row_version += 1
        entry.save()
        _event("notebook.updated", entry, by, old_value=changes_old, new_value=changes_new)
    return entry


def add_material(entry: NotebookEntry, *, by, kind: str, code: str) -> EntryMaterial:
    _require(
        permissions.can_edit_entry(by, entry),
        "Materiais só entram pelo autor, com a entrada aberta.",
    )
    if kind not in MATERIAL_LOOKUP:
        raise ValidationError("Escolha lote, insumo ou amostra.")
    code = (code or "").strip()
    if not code:
        raise ValidationError("Informe o código do material.")
    slug, field, attribute = MATERIAL_LOOKUP[kind]
    catalog = get_kind(slug)
    queryset = catalog.model.objects.available().filter(**{f"{field}__iexact": code})
    if catalog.project_scoped:
        queryset = queryset.filter(project=entry.project)
    record = queryset.order_by("-version").first()
    label = MaterialKind(kind).label
    if record is None:
        raise ValidationError(
            f"{label} {code} não existe no cadastro (vigente e ativo"
            + (" deste projeto)." if catalog.project_scoped else ").")
        )
    real_code = getattr(record, field)
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_edit_entry(by, entry), "A entrada não está mais aberta.")
        if entry.materials.filter(
            kind=kind, code__iexact=real_code, removed_at__isnull=True
        ).exists():
            raise ValidationError(f"{label} {real_code} já está ligado a esta entrada.")
        material = EntryMaterial.objects.create(
            entry=entry,
            kind=kind,
            code=real_code,
            version=record.version,
            added_by=by,
            **{attribute: record},
        )
        _refresh_search(entry)
        _event(
            "notebook.material_added",
            entry,
            by,
            new_value={
                "tipo": label,
                "codigo": real_code,
                "id_cadastro": record.pk,
                "versao": record.version,
            },
        )
    return material


def remove_material(material: EntryMaterial, *, by) -> EntryMaterial:
    entry = material.entry
    _require(
        permissions.can_edit_entry(by, entry),
        "Materiais só saem pelo autor, com a entrada aberta.",
    )
    if material.removed_at:
        return material
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_edit_entry(by, entry), "A entrada não está mais aberta.")
        material.removed_by = by
        material.removed_at = timezone.now()
        material.save(update_fields=["removed_by", "removed_at"])
        _refresh_search(entry)
        _event(
            "notebook.material_removed",
            entry,
            by,
            old_value={"tipo": material.get_kind_display(), "codigo": material.code},
        )
    return material


def add_attachment(entry: NotebookEntry, *, by, uploaded, inline: bool = False):
    _require(
        permissions.can_edit_entry(by, entry),
        "Anexos só entram pelo autor, com a entrada aberta.",
    )
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_edit_entry(by, entry), "A entrada não está mais aberta.")
        stored = store_upload(uploaded, by=by, allowed=IMAGE_KINDS if inline else ATTACHMENT_KINDS)
        attachment = EntryAttachment.objects.create(
            entry=entry, file=stored, inline=inline, added_by=by
        )
        _event(
            "notebook.attachment_added",
            entry,
            by,
            new_value={
                "arquivo": stored.pk,
                "nome": stored.original_name,
                "sha256": stored.sha256,
                "no_texto": inline,
            },
        )
    return attachment


def remove_attachment(attachment: EntryAttachment, *, by) -> EntryAttachment:
    entry = attachment.entry
    _require(
        permissions.can_edit_entry(by, entry),
        "Anexos só saem pelo autor, com a entrada aberta.",
    )
    if attachment.removed_at:
        return attachment
    if attachment.promotions.exists():
        raise ValidationError("O anexo foi promovido para um estudo e registra a origem dos dados.")
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_edit_entry(by, entry), "A entrada não está mais aberta.")
        attachment.removed_by = by
        attachment.removed_at = timezone.now()
        attachment.save(update_fields=["removed_by", "removed_at"])
        _event(
            "notebook.attachment_removed",
            entry,
            by,
            old_value={"arquivo": attachment.file_id, "nome": attachment.file.original_name},
        )
    return attachment


def set_relevance(entry: NotebookEntry, *, by, relevant: bool) -> NotebookEntry:
    _require(
        permissions.can_mark_relevant(by, entry),
        "A relevância é marcada pelo autor ou pelo Gestor de P&D, antes da testemunha.",
    )
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_mark_relevant(by, entry), "A entrada já foi testemunhada.")
        if entry.relevant == bool(relevant):
            return entry
        old = entry.relevant
        entry.relevant = bool(relevant)
        entry.relevant_by = by
        entry.relevant_at = timezone.now()
        entry.save(update_fields=["relevant", "relevant_by", "relevant_at"])
        _event(
            "notebook.relevance_changed",
            entry,
            by,
            old_value={"relevante": old},
            new_value={"relevante": entry.relevant},
        )
    return entry


# ------------------------------------------------------------------ assinaturas


def sign_entry(entry: NotebookEntry, *, by, password: str, request=None) -> NotebookSignature:
    _require(
        permissions.can_sign(by, entry), "Só o autor assina a entrada, e só enquanto está aberta."
    )
    reauthenticate(request, by, password)
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_sign(by, entry), "A entrada não está mais aberta.")
        digest = entry_hash(entry)
        now = timezone.now()
        signature = NotebookSignature.objects.create(
            entry=entry, role=SignatureRole.AUTHOR, signer=by, signed_at=now, content_hash=digest
        )
        entry.status = EntryStatus.SIGNED
        entry.signed_at = now
        entry.save(update_fields=["status", "signed_at"])
        _event(
            "notebook.signed",
            entry,
            by,
            new_value={"numero": entry.number, "resumo": digest, "relevante": entry.relevant},
            request=request,
        )
    return signature


def author_signature(entry) -> NotebookSignature | None:
    return entry.signatures.filter(role=SignatureRole.AUTHOR, addendum__isnull=True).first()


def witness_entry(entry: NotebookEntry, *, by, password: str, request=None) -> NotebookSignature:
    refusal = permissions.witness_refusal(by, entry)
    _require(not refusal, _sentence(refusal))
    reauthenticate(request, by, password)
    mismatch = None
    with transaction.atomic():
        entry = _locked_entry(entry)
        refusal = permissions.witness_refusal(by, entry)
        _require(not refusal, _sentence(refusal))
        digest = entry_hash(entry)
        signed = author_signature(entry)
        if signed is None or signed.content_hash != digest:
            mismatch = (signed.content_hash if signed else "", digest)
        else:
            now = timezone.now()
            signature = NotebookSignature.objects.create(
                entry=entry,
                role=SignatureRole.WITNESS,
                signer=by,
                signed_at=now,
                content_hash=digest,
            )
            entry.status = EntryStatus.WITNESSED
            entry.witnessed_at = now
            entry.save(update_fields=["status", "witnessed_at"])
            _event(
                "notebook.witnessed",
                entry,
                by,
                new_value={"numero": entry.number, "resumo": digest},
                request=request,
            )
    if mismatch:
        _event(
            "notebook.integrity_failed",
            entry,
            by,
            old_value={"resumo_assinado": mismatch[0]},
            new_value={"resumo_atual": mismatch[1]},
            request=request,
        )
        raise ValidationError(
            "O conteúdo da entrada não confere com a assinatura do autor; a testemunha não foi "
            "registrada. Avise a Qualidade."
        )
    return signature


def add_addendum(entry: NotebookEntry, *, by, text: str, password: str, request=None) -> Addendum:
    _require(
        permissions.can_add_addendum(by, entry),
        "Adendos são feitos pelos editores do projeto em entradas já assinadas.",
    )
    clean = richtext.sanitize(text, image_ids=image_file_ids(entry))
    if not richtext.plain_text(clean) and "<img" not in clean:
        raise ValidationError("Escreva o texto do adendo.")
    reauthenticate(request, by, password)
    with transaction.atomic():
        entry = _locked_entry(entry)
        _require(permissions.can_add_addendum(by, entry), "A entrada ainda está aberta.")
        number = (entry.addenda.aggregate(top=Max("number"))["top"] or 0) + 1
        addendum = Addendum(
            entry=entry,
            number=number,
            text=clean,
            author=by,
            created_at=timezone.now(),
            search_text=richtext.fold(richtext.plain_text(clean)),
        )
        addendum.content_hash = addendum_hash(addendum)
        addendum.save()
        NotebookSignature.objects.create(
            entry=entry,
            addendum=addendum,
            role=SignatureRole.AUTHOR,
            signer=by,
            signed_at=addendum.created_at,
            content_hash=addendum.content_hash,
        )
        _event(
            "notebook.addendum_added",
            entry,
            by,
            new_value={"adendo": number, "texto": clean, "resumo": addendum.content_hash},
            request=request,
        )
    return addendum


def verify(entry: NotebookEntry) -> dict:
    """Confere os resumos assinados com o conteúdo atual (entrada e adendos)."""
    digest = entry_hash(entry)
    result = {"entry_ok": True, "addenda_ok": True, "digest": digest}
    for signature in entry.signatures.filter(addendum__isnull=True):
        if signature.content_hash != digest:
            result["entry_ok"] = False
    for addendum in entry.addenda.all():
        if addendum_hash(addendum) != addendum.content_hash:
            result["addenda_ok"] = False
    return result


# ------------------------------------------------------------------ vínculos


def _target_fields(target) -> tuple[str, dict, int]:
    from sgp.catalog.models import Lot
    from sgp.studies.models import Study
    from sgp.subdocuments.models import Subdocument

    if isinstance(target, Subdocument):
        return LinkTarget.SUBDOCUMENT, {"subdocument": target}, target.project_id
    if isinstance(target, Lot):
        return LinkTarget.LOT, {"lot": target}, target.project_id
    if isinstance(target, Study):
        return LinkTarget.STUDY, {"study": target}, target.project_id
    raise ValidationError("Escolha um subdocumento, um lote ou um estudo.")


def link(entry: NotebookEntry, *, by, target) -> NotebookLink:
    _require(permissions.can_link(by, entry), "Só os editores do projeto ligam entradas.")
    target_type, fields, project_id = _target_fields(target)
    if project_id != entry.project_id:
        raise ValidationError("Só é possível ligar registros do mesmo projeto.")
    with transaction.atomic():
        entry = _locked_entry(entry)
        if NotebookLink.objects.filter(
            entry=entry, kind=LinkKind.RELATED, removed_at__isnull=True, **fields
        ).exists():
            raise ValidationError("Esse vínculo já existe.")
        created = NotebookLink.objects.create(
            entry=entry, target_type=target_type, kind=LinkKind.RELATED, created_by=by, **fields
        )
        _event(
            "notebook.linked",
            entry,
            by,
            new_value={"alvo": created.get_target_type_display(), "id": target.pk, "registro": str(target)},
        )
    return created


def unlink(item: NotebookLink, *, by, reason: str) -> NotebookLink:
    _require(permissions.can_link(by, item.entry), "Só os editores do projeto retiram vínculos.")
    if item.kind == LinkKind.PROMOTED:
        raise ValidationError(
            "O vínculo de promoção registra a origem dos dados do estudo e não é retirado."
        )
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da retirada do vínculo.")
    if item.removed_at:
        return item
    with transaction.atomic():
        item.removed_by = by
        item.removed_at = timezone.now()
        item.removal_reason = reason[:500]
        item.save(update_fields=["removed_by", "removed_at", "removal_reason"])
        _event(
            "notebook.unlinked",
            item.entry,
            by,
            old_value={"alvo": item.get_target_type_display(), "registro": str(item.target)},
            reason=reason[:500],
        )
    return item


def linked_entries(obj, user=None):
    """Vínculos ativos e usos como material que apontam o registro (para mostrar o outro lado)."""
    from sgp.catalog.models import Lot, Material, Sample
    from sgp.studies.models import Study
    from sgp.subdocuments.models import Subdocument

    links = NotebookLink.objects.filter(removed_at__isnull=True).select_related(
        "entry__project", "entry__author", "attachment__file"
    )
    uses = EntryMaterial.objects.filter(removed_at__isnull=True).select_related(
        "entry__project", "entry__author"
    )
    if isinstance(obj, Subdocument):
        links, uses = links.filter(subdocument=obj), uses.none()
    elif isinstance(obj, Study):
        links, uses = links.filter(study__lineage=obj.lineage), uses.none()
    elif isinstance(obj, Lot):
        links, uses = links.filter(lot__lineage=obj.lineage), uses.filter(lot__lineage=obj.lineage)
    elif isinstance(obj, Material):
        links, uses = links.none(), uses.filter(material__lineage=obj.lineage)
    elif isinstance(obj, Sample):
        links, uses = links.none(), uses.filter(sample__lineage=obj.lineage)
    else:
        links, uses = links.none(), uses.none()
    items = [{"entry": item.entry, "kind": item.get_kind_display(), "link": item} for item in links]
    items += [{"entry": item.entry, "kind": "Material usado", "link": None} for item in uses]
    if user is not None:
        items = [item for item in items if permissions.can_view(user, item["entry"].project)]
    return sorted(items, key=lambda item: (-item["entry"].created_at.timestamp(), item["kind"]))


# ------------------------------------------------------------------ modelos de entrada


def _template_texts(data: dict) -> dict:
    return {field: richtext.sanitize(data.get(field, "")) for field in TEXT_FIELDS}


def _template_snapshot(template: EntryTemplate) -> dict:
    return {
        "nome": template.name,
        "versao": template.version,
        **{TEXT_LABELS[f].lower(): getattr(template, f) for f in TEXT_FIELDS},
    }


def _check_template_name(name: str, lineage=None) -> str:
    name = (name or "").strip()
    if not name:
        raise ValidationError("Informe o tipo de experimento do modelo.")
    clash = EntryTemplate.objects.filter(is_current=True, name__iexact=name)
    if lineage is not None:
        clash = clash.exclude(lineage=lineage)
    if clash.exists():
        raise ValidationError("Já existe um modelo vigente com esse nome.")
    return name[:200]


def create_template(*, by, data: dict) -> EntryTemplate:
    _require(
        permissions.can_manage_templates(by),
        "Só a Qualidade/AR e o Gestor de P&D mantêm os modelos de entrada.",
    )
    name = _check_template_name(data.get("name"))
    with transaction.atomic():
        template = EntryTemplate.objects.create(
            name=name, created_by=by, change_reason="Criação", **_template_texts(data)
        )
        record_event(
            "notebook.template_created", actor=by, obj=template, new_value=_template_snapshot(template)
        )
    return template


def update_template(template: EntryTemplate, *, by, data: dict, reason: str) -> EntryTemplate:
    _require(
        permissions.can_manage_templates(by),
        "Só a Qualidade/AR e o Gestor de P&D mantêm os modelos de entrada.",
    )
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da alteração do modelo.")
    with transaction.atomic():
        current = EntryTemplate.objects.select_for_update().get(pk=template.pk)
        if not current.is_current:
            raise ValidationError("Só a versão vigente do modelo pode ser alterada.")
        name = _check_template_name(data.get("name", current.name), lineage=current.lineage)
        texts = _template_texts(data)
        if name == current.name and all(texts[f] == getattr(current, f) for f in TEXT_FIELDS):
            raise ValidationError("Nada mudou no modelo.")
        EntryTemplate.objects.filter(pk=current.pk).update(is_current=False)
        new = EntryTemplate.objects.create(
            lineage=current.lineage,
            version=current.version + 1,
            is_current=True,
            active=current.active,
            name=name,
            created_by=by,
            change_reason=reason[:500],
            **texts,
        )
        record_event(
            "notebook.template_updated",
            actor=by,
            obj=new,
            old_value=_template_snapshot(current),
            new_value=_template_snapshot(new),
            reason=reason[:500],
        )
    return new


def deactivate_template(template: EntryTemplate, *, by, reason: str) -> EntryTemplate:
    _require(
        permissions.can_manage_templates(by),
        "Só a Qualidade/AR e o Gestor de P&D mantêm os modelos de entrada.",
    )
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Informe o motivo da desativação do modelo.")
    with transaction.atomic():
        current = EntryTemplate.objects.select_for_update().get(pk=template.pk)
        if not current.is_current or not current.active:
            raise ValidationError("O modelo já está fora de uso.")
        current.active = False
        current.save(update_fields=["active"])
        record_event(
            "notebook.template_deactivated",
            actor=by,
            obj=current,
            old_value={"ativo": True},
            new_value={"ativo": False},
            reason=reason[:500],
        )
    return current


def active_templates():
    return EntryTemplate.objects.filter(is_current=True, active=True).order_by("name")
