"""Adaptadores dos dois tipos de modelo: formulário (004) e layout (006) (research R1, R4, R8)."""

from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from sgp.audit.services import record_event
from sgp.signatures.canonical import content_hash

from .models import TemplateKind


class FormAdapter:
    kind = TemplateKind.FORM
    label = "Modelo de subdocumento"

    @property
    def model(self):
        from sgp.formtemplates.models import FormTemplate

        return FormTemplate

    def get(self, pk):
        return self.model.objects.select_related("subdocument_type").get(pk=pk)

    def lock(self, obj):
        return (
            self.model.objects.select_for_update().select_related("subdocument_type").get(pk=obj.pk)
        )

    def family(self, obj) -> str:
        return obj.subdocument_type.code

    def family_label(self, obj) -> str:
        return obj.subdocument_type.label

    def version(self, obj) -> int:
        return obj.form_version

    def versions(self, obj):
        return self.model.objects.filter(subdocument_type=obj.subdocument_type).order_by(
            "-form_version"
        )

    def current(self, obj, on=None):
        from sgp.formtemplates.services import current_template

        return current_template(obj.subdocument_type, on)

    def comparable(self, obj) -> dict:
        return {"referência": obj.reference, "definição": obj.definition}

    def content(self, obj) -> dict:
        return {
            "tipo": self.kind.value,
            "familia": self.family(obj),
            "versao": self.version(obj),
            "referencia": obj.reference,
            "vigencia": obj.valid_from,
            "definicao": obj.definition,
        }

    def errors(self, obj) -> list[str]:
        from sgp.formtemplates.services import definition_errors

        errors = definition_errors(obj, obj.definition)
        if not obj.reference.strip():
            errors.insert(0, "Informe a referência do formulário.")
        return errors

    def publish(self, obj, *, by, valid_from):
        obj.status = "published"
        obj.valid_from = valid_from
        obj.published_by = by
        obj.published_at = timezone.now()
        obj.save(update_fields=["status", "valid_from", "published_by", "published_at"])
        record_event(
            "formtemplates.published",
            actor=by,
            obj=obj,
            new_value={
                "tipo": obj.subdocument_type.label,
                "versao": obj.version_display,
                "vigencia": obj.valid_from,
            },
        )

    def usage(self, obj) -> list[str]:
        from sgp.subdocuments.models import Subdocument

        return [
            f"{sub.project.code or sub.project.title} – {sub}"
            for sub in Subdocument.objects.filter(template=obj).select_related(
                "project", "subdocument_type"
            )
        ]

    def detail_url(self, obj) -> str:
        return reverse("formtemplates:detail", args=[obj.pk])

    def edit_url(self, obj) -> str:
        return reverse("formtemplates:edit", args=[obj.pk])


class LayoutAdapter:
    kind = TemplateKind.LAYOUT
    label = "Modelo de layout"

    @property
    def model(self):
        from sgp.documents.models import LayoutTemplate

        return LayoutTemplate

    def get(self, pk):
        return self.model.objects.select_related("logo").get(pk=pk)

    def lock(self, obj):
        return self.model.objects.select_for_update().get(pk=obj.pk)

    def family(self, obj) -> str:
        return obj.target

    def family_label(self, obj) -> str:
        return f"Layout de {obj.get_target_display()}"

    def version(self, obj) -> int:
        return obj.version

    def versions(self, obj):
        return self.model.objects.filter(target=obj.target).order_by("-version")

    def current(self, obj, on=None):
        from sgp.documents.layouts import current_layout

        return current_layout(obj.target, on)

    def _logo(self, obj) -> str:
        from sgp.documents.layouts import DEFAULT_LOGO_SHA256

        return obj.logo.sha256 if obj.logo_id else f"padrão {DEFAULT_LOGO_SHA256}"

    def comparable(self, obj) -> dict:
        return {"logotipo": self._logo(obj), "definição": obj.definition}

    def content(self, obj) -> dict:
        return {
            "tipo": self.kind.value,
            "familia": self.family(obj),
            "versao": self.version(obj),
            "vigencia": obj.valid_from,
            "logotipo": self._logo(obj),
            "definicao": obj.definition,
        }

    def errors(self, obj) -> list[str]:
        from sgp.documents.layouts import definition_errors

        return definition_errors(obj, obj.definition)

    def publish(self, obj, *, by, valid_from):
        from sgp.documents.layouts import logo_bytes

        logo_bytes(obj)  # logotipo legível e íntegro antes de publicar
        obj.status = "published"
        obj.valid_from = valid_from
        obj.published_by = by
        obj.published_at = timezone.now()
        obj.save(update_fields=["status", "valid_from", "published_by", "published_at"])
        record_event(
            "layouts.published",
            actor=by,
            obj=obj,
            new_value={
                "alvo": obj.get_target_display(),
                "versao": obj.version_display,
                "vigencia": obj.valid_from,
            },
        )

    def usage(self, obj) -> list[str]:
        from sgp.documents.models import LayoutBinding

        bindings = LayoutBinding.objects.filter(layout=obj).order_by("kind", "object_id", "version")
        return [f"{b.get_kind_display()} {b.object_id} – versão {b.version:02d}" for b in bindings]

    def detail_url(self, obj) -> str:
        return reverse("layouts:detail", args=[obj.pk])

    def edit_url(self, obj) -> str:
        return reverse("layouts:edit", args=[obj.pk])


ADAPTERS = {adapter.kind: adapter for adapter in (FormAdapter(), LayoutAdapter())}


def get_adapter(kind: str):
    try:
        return ADAPTERS[kind]
    except KeyError:
        raise Http404("Tipo de modelo inexistente.") from None


def load(kind: str, pk):
    adapter = get_adapter(kind)
    try:
        return adapter, adapter.get(pk)
    except adapter.model.DoesNotExist:
        raise Http404("Versão de modelo inexistente.") from None


def digest(adapter, obj) -> str:
    return content_hash(adapter.content(obj))
