"""Conteúdo canônico da entrada e do adendo (contrato conteudo-assinado.md da feature 008)."""

from datetime import UTC

from sgp.signatures.canonical import content_hash


def _iso(moment) -> str:
    return moment.astimezone(UTC).isoformat()


def entry_content(entry) -> dict:
    template = entry.template
    materials = entry.materials.filter(removed_at__isnull=True).order_by("pk")
    attachments = (
        entry.attachments.filter(removed_at__isnull=True).select_related("file").order_by("pk")
    )
    return {
        "projeto": entry.project.code or "",
        "numero": entry.number,
        "autor": entry.author.username,
        "criada_em": _iso(entry.created_at),
        "titulo": entry.title,
        "objetivo": entry.objective,
        "hipotese": entry.hypothesis,
        "procedimento": entry.procedure,
        "resultados": entry.results,
        "conclusao": entry.conclusion,
        "modelo": (
            {"id": template.pk, "nome": template.name, "versao": template.version}
            if template
            else None
        ),
        "materiais": [
            {"tipo": item.kind, "id": item.record_id, "codigo": item.code, "versao": item.version}
            for item in materials
        ],
        "anexos": [
            {
                "id": item.file_id,
                "nome": item.file.original_name,
                "sha256": item.file.sha256,
                "no_texto": item.inline,
            }
            for item in attachments
        ],
    }


def entry_hash(entry) -> str:
    return content_hash(entry_content(entry))


def addendum_content(addendum) -> dict:
    entry = addendum.entry
    return {
        "entrada": entry.pk,
        "projeto": entry.project.code or "",
        "numero_entrada": entry.number,
        "adendo": addendum.number,
        "autor": addendum.author.username,
        "criado_em": _iso(addendum.created_at),
        "texto": addendum.text,
    }


def addendum_hash(addendum) -> str:
    return content_hash(addendum_content(addendum))
