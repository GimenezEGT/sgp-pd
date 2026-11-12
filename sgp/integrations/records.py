"""Registros do modelo lógico do contexto (contrato registros.md da feature 012).

Cada função devolve (tipo, chave de idempotência, campos lógicos) a partir dos dados aprovados.
Datas em ISO 8601; textos como estão no sistema.
"""

from django.utils import timezone

from sgp.signatures.models import ApprovedVersion, Meaning, Signature


def _date(value) -> str:
    if not value:
        return ""
    if hasattr(value, "hour"):
        value = timezone.localtime(value).date()
    return value.isoformat()


def _name(user) -> str:
    return (user.get_full_name() or user.username) if user else ""


def project(project) -> tuple[str, str, dict]:
    payload = {
        "codigo_projeto": project.code or "",
        "nome": project.title,
        "produto": project.product_name,
        "tecnologia": project.technology.label if project.technology_id else "",
        "orgao": project.regulatory_body or "",
        "classe_risco": project.risk_class or "",
        "lider": _name(project.leader),
        "situacao": project.get_status_display(),
        "versao_projeto": project.version or 0,
        "data_abertura": _date(project.approved_at),
    }
    return "projeto", f"projeto:{project.pk}:{project.version or 0}", payload


def _signer(kind: str, object_id: int, version: int, meaning: str) -> str:
    signature = (
        Signature.objects.filter(kind=kind, object_id=object_id, version=version, meaning=meaning)
        .order_by("-signed_at", "-pk")
        .first()
    )
    return signature.signer_name if signature else ""


def document(sub, approval: ApprovedVersion) -> tuple[str, str, dict]:
    from sgp.documents.models import GeneratedDocument
    from sgp.formtemplates.models import FormTemplate

    template_id = ((approval.content or {}).get("modelo") or {}).get("id")
    template = FormTemplate.objects.filter(pk=template_id).first() or sub.template
    official = (
        GeneratedDocument.objects.filter(
            kind="subdocument",
            object_id=sub.pk,
            version=approval.version,
            official=True,
            format="pdf",
        )
        .order_by("-generated_at", "-pk")
        .first()
    )
    payload = {
        "codigo_projeto": sub.project.code or "",
        "tipo_subdocumento": sub.subdocument_type.label,
        "versao_documento": approval.version,
        "versao_formulario": getattr(template, "form_version", "") or "",
        "referencia_psg": getattr(template, "reference", "") or "",
        "data_aprovacao": _date(approval.approved_at),
        "elaborador": _signer("subdocument", sub.pk, approval.version, Meaning.ELABORATED),
        "aprovador": _signer("subdocument", sub.pk, approval.version, Meaning.APPROVED),
        "resumo_conteudo": approval.content_hash,
        "pdf_sha256": official.file_hash if official else "",
        "pdf_codigo_verificacao": official.verification_code if official else "",
    }
    return "documento", f"documento:{sub.pk}:{approval.version}", payload


def lot(record) -> tuple[str, str, dict]:
    payload = {
        "codigo_lote": record.code,
        "tipo": record.get_lot_type_display(),
        "codigo_projeto": (record.project.code or "") if record.project_id else "",
        "data_fabricacao": _date(record.manufacture_date),
        "data_validade": _date(record.expiry_date),
        "local": record.manufacturing_site,
        "responsavel": _name(record.production_responsible),
    }
    return "lote", f"lote:{record.pk}:{record.version}", payload


def new_material(material, project) -> tuple[str, str, dict]:
    certificate = material.certificate
    payload = {
        "descricao": material.description,
        "tipo": material.get_material_type_display(),
        "fabricante": material.manufacturer,
        "lote_fabricante": material.manufacturer_lot,
        "certificado_nome": certificate.original_name if certificate else "",
        "certificado_sha256": certificate.sha256 if certificate else "",
        "codigo_projeto": project.code or "",
        "situacao": "solicitado",
    }
    return "insumo_novo", f"insumo_novo:{material.pk}:{material.version}:{project.pk}", payload


def study_result(study) -> tuple[str, str, dict]:
    from sgp.studies import profiles

    results = study.results or {}
    criteria = results.get("criterios", [])
    criterion_text = "; ".join(
        f"{c['rotulo']} {profiles.COMPARISONS.get(c['comparacao'], c['comparacao'])} {c['limite']}"
        for c in criteria
    )
    result_text = "; ".join(
        f"{c['rotulo']} = {c['valor'] if c['valor'] is not None else 'não calculável'}"
        for c in criteria
    )
    if study.not_applicable:
        conclusion = f"Não aplicável: {study.justification}"
    elif criteria:
        conclusion = "atendido" if all(c.get("atendido") for c in criteria) else "não atendido"
    else:
        conclusion = "sem critério"
    payload = {
        "codigo_projeto": study.project.code or "",
        "tipo_estudo": study.study_type.label,
        "titulo": study.title,
        "versao": study.version,
        "criterio": criterion_text,
        "resultado": result_text,
        "conclusao": conclusion,
        "documento_origem": str(study.subdocument) if study.subdocument_id else "",
    }
    return "resultado_estudo", f"resultado_estudo:{study.pk}:{study.version}", payload


def references(sub, approval, kind: str, topic_keys=None) -> list[int]:
    """Ids citados em campos de referência do tipo `kind` no conteúdo aprovado."""
    from sgp.formtemplates.models import FormTemplate

    template_id = ((approval.content or {}).get("modelo") or {}).get("id")
    template = FormTemplate.objects.filter(pk=template_id).first() or sub.template
    topics = (approval.content or {}).get("topicos") or {}
    ids = []
    for topic in template.topics:
        if topic_keys and topic["key"] not in topic_keys:
            continue
        values = (topics.get(topic["key"]) or {}).get("values") or {}
        for field in topic.get("fields", []):
            if field.get("type") != "reference" or field.get("kind") != kind:
                continue
            value = values.get(field["key"]) or []
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, dict):
                    item = item.get("id")
                if str(item).isdigit() and int(item) not in ids:
                    ids.append(int(item))
    return ids
