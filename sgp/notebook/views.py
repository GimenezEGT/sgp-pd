"""Telas do caderno de laboratório (contrato rotas-ui.md da feature 008)."""

from functools import wraps

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import deny_access
from sgp.catalog.models import Lot
from sgp.files.storage import IntegrityFailure, record_integrity_failure
from sgp.projects.models import Project
from sgp.projects.permissions import accessible_projects
from sgp.studies import profiles as study_profiles
from sgp.studies import services as study_services
from sgp.studies.models import ImportMapping, Study
from sgp.subdocuments.models import Subdocument

from . import permissions, promotion, richtext, search, services
from .models import (
    TEXT_FIELDS,
    TEXT_LABELS,
    EntryAttachment,
    EntryMaterial,
    EntryTemplate,
    MaterialKind,
    NotebookEntry,
    NotebookLink,
    SignatureRole,
)


class EntryForm(forms.Form):
    title = forms.CharField(label="Título", max_length=300)
    template = forms.ModelChoiceField(
        label="Modelo de entrada",
        queryset=EntryTemplate.objects.none(),
        required=False,
        empty_label="— sem modelo —",
    )
    relevant = forms.BooleanField(
        label="Relevante para propriedade intelectual ou decisão do projeto (exige testemunha)",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = services.active_templates()


class FilterForm(forms.Form):
    q = forms.CharField(label="Palavras", required=False, max_length=200)
    projeto = forms.TypedChoiceField(label="Projeto", required=False, coerce=int, empty_value=None)
    lote = forms.CharField(label="Lote", required=False, max_length=100)
    amostra = forms.CharField(label="Amostra", required=False, max_length=100)
    pesquisador = forms.CharField(label="Pesquisador", required=False, max_length=150)
    de = forms.DateField(label="De", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    ate = forms.DateField(
        label="Até", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    situacao = forms.ChoiceField(
        label="Situação", required=False, choices=[("", "Todas"), *search.SITUATIONS]
    )
    abertas_ha = forms.IntegerField(
        label="Abertas há mais de (dias)", required=False, min_value=0, max_value=3650
    )

    def __init__(self, *args, projects=None, **kwargs):
        super().__init__(*args, **kwargs)
        if projects is None:
            del self.fields["projeto"]
        else:
            self.fields["projeto"].choices = [("", "Todos")] + [(p.pk, str(p)) for p in projects]

    def filters(self, project=None) -> search.Filters:
        data = self.cleaned_data if self.is_valid() else {}
        return search.Filters(
            q=data.get("q") or "",
            project=project.pk if project else data.get("projeto"),
            lot=data.get("lote") or "",
            sample=data.get("amostra") or "",
            author=data.get("pesquisador") or "",
            date_from=data.get("de"),
            date_to=data.get("ate"),
            situation=data.get("situacao") or "",
            older_than=data.get("abertas_ha"),
        )


def _guarded(view):
    """Converte recusa de permissão do serviço em negação registrada (403)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except PermissionDenied as exc:
            return deny_access(request, str(exc) or "sem permissão no caderno")

    return wrapper


def _entry_or_deny(request, pk):
    entry = get_object_or_404(
        NotebookEntry.objects.select_related("project", "author", "template"), pk=pk
    )
    if not permissions.can_view(request.user, entry.project):
        return None, deny_access(request, "sem acesso ao projeto do caderno")
    return entry, None


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


def _detail(entry, anchor=""):
    url = reverse("notebook:detail", args=[entry.pk])
    return redirect(f"{url}#{anchor}" if anchor else url)


# ------------------------------------------------------------------ linha do tempo e busca


def _timeline(request, *, project=None):
    projects = None if project else list(accessible_projects(request.user).order_by("code"))
    form = FilterForm(request.GET or None, projects=projects)
    queryset = search.search(request.user, form.filters(project))
    page = Paginator(queryset, search.PAGE_SIZE).get_page(request.GET.get("pagina"))
    context = {
        "form": form,
        "project": project,
        "page": page,
        "rows": search.annotate(page.object_list),
        "sign_days": search.sign_days(),
        "can_create": bool(project and permissions.can_create(request.user, project)),
    }
    if request.headers.get("HX-Request"):
        return render(request, "notebook/_entries.html", context)
    return render(request, "notebook/timeline.html", context)


@require_GET
def search_view(request):
    return _timeline(request)


@require_GET
def project_notebook(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not permissions.can_view(request.user, project):
        return deny_access(request, "sem acesso ao projeto do caderno")
    return _timeline(request, project=project)


# ------------------------------------------------------------------ entrada


@require_http_methods(["GET", "POST"])
@_guarded
def entry_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if not permissions.can_create(request.user, project):
        return deny_access(request, "só os editores do projeto aberto criam entradas no caderno")
    form = EntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            entry = services.create_entry(project, by=request.user, data=form.cleaned_data)
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(
                request,
                f"Entrada {entry.number} criada com data e hora do servidor; preencha o registro.",
            )
            return redirect("notebook:edit", pk=entry.pk)
    return render(request, "notebook/create.html", {"project": project, "form": form})


def _texts(entry) -> list[dict]:
    images = services.image_file_ids(entry)
    return [
        {
            "field": field,
            "label": TEXT_LABELS[field],
            "html": mark_safe(richtext.sanitize(getattr(entry, field), image_ids=images)),  # noqa: S308
            "value": getattr(entry, field),
        }
        for field in TEXT_FIELDS
    ]


def _latest_studies(project) -> list[Study]:
    latest = {}
    for study in Study.objects.filter(project=project).order_by("lineage", "-version"):
        latest.setdefault(study.lineage, study)
    return sorted(latest.values(), key=lambda study: study.title)


@require_GET
def entry_detail(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    user = request.user
    images = services.image_file_ids(entry)
    addenda = []
    for addendum in entry.addenda.select_related("author").order_by("number"):
        addenda.append(
            {
                "obj": addendum,
                "html": mark_safe(richtext.sanitize(addendum.text, image_ids=images)),  # noqa: S308
            }
        )
    signatures = entry.signatures.filter(addendum__isnull=True).select_related("signer")
    can_link = permissions.can_link(user, entry)
    context = {
        "entry": entry,
        "situation": search.SITUATION_LABELS[search.situation(entry)],
        "situation_code": search.situation(entry),
        "texts": _texts(entry),
        "materials": entry.materials.filter(removed_at__isnull=True),
        "removed_materials": entry.materials.filter(removed_at__isnull=False),
        "attachments": entry.attachments.filter(removed_at__isnull=True).select_related("file"),
        "removed_attachments": entry.attachments.filter(removed_at__isnull=False).select_related(
            "file"
        ),
        "author_signature": signatures.filter(role=SignatureRole.AUTHOR).first(),
        "witness_signature": signatures.filter(role=SignatureRole.WITNESS).first(),
        "addenda": addenda,
        "links": entry.links.filter(removed_at__isnull=True).select_related(
            "subdocument", "lot", "study", "attachment__file"
        ),
        "removed_links": entry.links.filter(removed_at__isnull=False),
        "verification": services.verify(entry) if not entry.is_open else None,
        "material_kinds": MaterialKind.choices,
        "can_edit": permissions.can_edit_entry(user, entry),
        "can_sign": permissions.can_sign(user, entry),
        "can_witness": permissions.can_witness(user, entry),
        "can_mark_relevant": permissions.can_mark_relevant(user, entry),
        "can_add_addendum": permissions.can_add_addendum(user, entry),
        "can_link": can_link,
        "can_promote": can_link and bool(promotion.spreadsheets(entry)),
        "subdocuments": (
            Subdocument.objects.filter(project=entry.project).select_related("subdocument_type")
            if can_link
            else []
        ),
        "studies": _latest_studies(entry.project) if can_link else [],
    }
    return render(request, "notebook/detail.html", context)


@require_http_methods(["GET", "POST"])
@_guarded
def entry_edit(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    if not permissions.can_edit_entry(request.user, entry):
        return deny_access(request, "só o autor altera a entrada aberta")
    if request.method == "POST":
        data = {"title": request.POST.get("title", "")}
        data.update({field: request.POST.get(field, "") for field in TEXT_FIELDS})
        try:
            services.update_entry(
                entry, by=request.user, data=data, row_version=request.POST.get("row_version")
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Entrada gravada.")
            if request.POST.get("continuar"):
                return redirect("notebook:edit", pk=entry.pk)
            return _detail(entry)
        entry.title = data["title"]
        for field in TEXT_FIELDS:
            setattr(entry, field, data[field])
    context = {
        "entry": entry,
        "texts": _texts(entry),
        "attachments": entry.attachments.filter(removed_at__isnull=True).select_related("file"),
    }
    return render(request, "notebook/edit.html", context)


@require_POST
@_guarded
def material_add(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    try:
        material = services.add_material(
            entry,
            by=request.user,
            kind=request.POST.get("tipo", ""),
            code=request.POST.get("codigo", ""),
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(
            request, f"Material ligado à entrada: {material.get_kind_display()} {material.code}."
        )
    return _detail(entry, "materiais")


@require_POST
@_guarded
def material_remove(request, pk):
    material = get_object_or_404(EntryMaterial.objects.select_related("entry__project"), pk=pk)
    entry, denied = _entry_or_deny(request, material.entry_id)
    if denied:
        return denied
    services.remove_material(material, by=request.user)
    messages.success(request, f"Material retirado da entrada: {material.get_kind_display()} {material.code}.")
    return _detail(entry, "materiais")


def _wants_json(request) -> bool:
    return "application/json" in request.headers.get("Accept", "")


@require_POST
@_guarded
def attachment_add(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    inline = request.POST.get("no_texto") == "1"
    uploaded = request.FILES.get("arquivo")
    try:
        if uploaded is None:
            raise ValidationError("Escolha o arquivo.")
        attachment = services.add_attachment(
            entry, by=request.user, uploaded=uploaded, inline=inline
        )
    except ValidationError as exc:
        if _wants_json(request):
            return JsonResponse({"erro": " ".join(exc.messages)}, status=400)
        _errors(request, exc)
        return _detail(entry, "anexos")
    if _wants_json(request):
        return JsonResponse(
            {
                "url": reverse("files:download", args=[attachment.file_id]),
                "name": attachment.file.original_name,
            }
        )
    messages.success(
        request, f"Anexo {attachment.file.original_name} incluído com o resumo SHA-256."
    )
    return _detail(entry, "anexos")


@require_POST
@_guarded
def attachment_remove(request, pk):
    attachment = get_object_or_404(
        EntryAttachment.objects.select_related("entry__project", "file"), pk=pk
    )
    entry, denied = _entry_or_deny(request, attachment.entry_id)
    if denied:
        return denied
    try:
        services.remove_attachment(attachment, by=request.user)
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Anexo {attachment.file.original_name} retirado da entrada.")
    return _detail(entry, "anexos")


@require_POST
@_guarded
def relevance(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    entry = services.set_relevance(
        entry, by=request.user, relevant=request.POST.get("relevante") == "1"
    )
    messages.success(
        request,
        "Entrada marcada como relevante: precisa de testemunha."
        if entry.relevant
        else "Entrada desmarcada como relevante.",
    )
    return _detail(entry)


@require_POST
@_guarded
def sign(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    try:
        services.sign_entry(
            entry, by=request.user, password=request.POST.get("senha", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Entrada assinada e bloqueada; correções só por adendo.")
    return _detail(entry, "assinaturas")


@require_POST
@_guarded
def witness(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    try:
        services.witness_entry(
            entry, by=request.user, password=request.POST.get("senha", ""), request=request
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Testemunho assinado.")
    return _detail(entry, "assinaturas")


@require_POST
@_guarded
def addendum_add(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    try:
        addendum = services.add_addendum(
            entry,
            by=request.user,
            text=request.POST.get("texto", ""),
            password=request.POST.get("senha", ""),
            request=request,
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Adendo {addendum.number} assinado; o original não mudou.")
    return _detail(entry, "adendos")


def _link_target(entry, post):
    target_type = post.get("alvo", "")
    if target_type == "subdocument":
        return get_object_or_404(
            Subdocument, pk=post.get("subdocumento") or 0, project=entry.project
        )
    if target_type == "study":
        return get_object_or_404(Study, pk=post.get("estudo") or 0, project=entry.project)
    if target_type == "lot":
        code = (post.get("lote") or "").strip()
        lot = (
            Lot.objects.available()
            .filter(project=entry.project, code__iexact=code)
            .order_by("-version")
            .first()
        )
        if lot is None:
            raise ValidationError(f"Lote {code} não existe no cadastro deste projeto.")
        return lot
    raise ValidationError("Escolha um subdocumento, um lote ou um estudo.")


@require_POST
@_guarded
def link_add(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    if not permissions.can_link(request.user, entry):
        return deny_access(request, "só os editores do projeto ligam entradas")
    try:
        created = services.link(entry, by=request.user, target=_link_target(entry, request.POST))
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, f"Entrada ligada a {created.target}.")
    return _detail(entry, "vinculos")


@require_POST
@_guarded
def link_remove(request, pk):
    item = get_object_or_404(NotebookLink.objects.select_related("entry__project"), pk=pk)
    entry, denied = _entry_or_deny(request, item.entry_id)
    if denied:
        return denied
    try:
        services.unlink(item, by=request.user, reason=request.POST.get("motivo", ""))
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Vínculo retirado; fica no histórico da entrada.")
    return _detail(entry, "vinculos")


@require_http_methods(["GET", "POST"])
@_guarded
def promote(request, pk):
    entry, denied = _entry_or_deny(request, pk)
    if denied:
        return denied
    if not permissions.can_link(request.user, entry):
        return deny_access(request, "só os editores do projeto promovem dados para estudos")
    params = request.POST if request.method == "POST" else request.GET
    sheets = promotion.spreadsheets(entry)
    studies = promotion.target_studies(entry)
    attachment = next((a for a in sheets if str(a.pk) == params.get("anexo", "")), None)
    study = next((s for s in studies if str(s.pk) == params.get("estudo", "")), None)
    equipment = (params.get("equipamento") or "").strip()
    context = {
        "entry": entry,
        "sheets": sheets,
        "studies": studies,
        "attachment": attachment,
        "study": study,
        "equipment": equipment,
        "mappings": ImportMapping.objects.all(),
        "columns": [],
        "preview": None,
    }
    if attachment and study:
        profile = study_services.profile_of(study.study_type)
        saved = ImportMapping.objects.filter(equipment=equipment).first() if equipment else None
        mapping = {
            column: (
                params.get(f"col__{column}")
                if f"col__{column}" in params
                else (saved.mapping.get(column, "") if saved else "")
            ).strip()
            for column in profile.columns
        }
        context["columns"] = [
            (c, study_profiles.COLUMN_LABELS[c], mapping.get(c, "")) for c in profile.columns
        ]
        if request.method == "POST":
            try:
                if request.POST.get("acao") == "confirmar":
                    created = promotion.confirm(
                        entry,
                        by=request.user,
                        token=request.POST.get("token", ""),
                        equipment=equipment,
                        mapping=mapping,
                    )
                    messages.success(
                        request,
                        f"Dados promovidos para o estudo {created.study}; o vínculo aparece na "
                        "entrada e no estudo.",
                    )
                    return redirect("studies:detail", pk=created.study_id)
                context["preview"] = promotion.preview(
                    entry,
                    by=request.user,
                    attachment=attachment,
                    study=study,
                    mapping={k: v for k, v in mapping.items() if v},
                )
            except IntegrityFailure as failure:
                record_integrity_failure(failure, request=request)
                messages.error(request, "O arquivo anexado não confere com o resumo guardado.")
            except ValidationError as exc:
                _errors(request, exc)
    return render(request, "notebook/promote.html", context)


# ------------------------------------------------------------------ modelos de entrada


class TemplateForm(forms.Form):
    name = forms.CharField(label="Tipo de experimento", max_length=200)
    objective = forms.CharField(label="Objetivo", required=False, widget=forms.Textarea)
    hypothesis = forms.CharField(label="Hipótese", required=False, widget=forms.Textarea)
    procedure = forms.CharField(label="Procedimento", required=False, widget=forms.Textarea)
    results = forms.CharField(label="Resultados", required=False, widget=forms.Textarea)
    conclusion = forms.CharField(label="Conclusão", required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in TEXT_FIELDS:
            self.fields[field].widget.attrs.update({"rows": 4, "data-rich": "1"})


@require_http_methods(["GET", "POST"])
@_guarded
def template_list(request):
    can_manage = permissions.can_manage_templates(request.user)
    form = TemplateForm(request.POST or None)
    if request.method == "POST":
        if not can_manage:
            return deny_access(request, "só a Qualidade/AR e o Gestor de P&D mantêm os modelos")
        if form.is_valid():
            try:
                template = services.create_template(by=request.user, data=form.cleaned_data)
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, f"Modelo {template.name} criado (versão 1).")
                return redirect("notebook:template_detail", pk=template.pk)
    templates = EntryTemplate.objects.filter(is_current=True).order_by("-active", "name")
    return render(
        request,
        "notebook/templates.html",
        {"templates": templates, "form": form, "can_manage": can_manage},
    )


@require_http_methods(["GET", "POST"])
@_guarded
def template_detail(request, pk):
    template = get_object_or_404(EntryTemplate, pk=pk)
    can_manage = permissions.can_manage_templates(request.user) and template.is_current
    initial = {"name": template.name, **{f: getattr(template, f) for f in TEXT_FIELDS}}
    form = TemplateForm(request.POST or None, initial=initial)
    if request.method == "POST":
        if not can_manage:
            return deny_access(request, "só a Qualidade/AR e o Gestor de P&D mantêm os modelos")
        if form.is_valid():
            try:
                new = services.update_template(
                    template,
                    by=request.user,
                    data=form.cleaned_data,
                    reason=request.POST.get("motivo", ""),
                )
            except ValidationError as exc:
                _errors(request, exc)
            else:
                messages.success(request, f"Modelo alterado: versão {new.version} vigente.")
                return redirect("notebook:template_detail", pk=new.pk)
    context = {
        "template": template,
        "texts": [
            {"label": TEXT_LABELS[f], "html": mark_safe(richtext.sanitize(getattr(template, f)))}  # noqa: S308
            for f in TEXT_FIELDS
        ],
        "versions": EntryTemplate.objects.filter(lineage=template.lineage).order_by("-version"),
        "form": form,
        "can_manage": can_manage,
    }
    return render(request, "notebook/template_detail.html", context)


@require_POST
@_guarded
def template_deactivate(request, pk):
    if not permissions.can_manage_templates(request.user):
        return deny_access(request, "só a Qualidade/AR e o Gestor de P&D mantêm os modelos")
    template = get_object_or_404(EntryTemplate, pk=pk)
    try:
        services.deactivate_template(
            template, by=request.user, reason=request.POST.get("motivo", "")
        )
    except ValidationError as exc:
        _errors(request, exc)
    else:
        messages.success(request, "Modelo desativado; entradas antigas continuam como nasceram.")
    return redirect("notebook:template_detail", pk=template.pk)
