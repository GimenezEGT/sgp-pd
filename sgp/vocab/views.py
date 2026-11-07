"""Telas das listas controladas, só para Qualidade/AR (FR-019 da feature 003)."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from sgp.accounts.profiles import Profile, profile_required

from . import services
from .forms import TermChangeForm, TermForm
from .models import Term, Vocabulary


def _errors(request, exc: ValidationError) -> None:
    for message in exc.messages:
        messages.error(request, message)


@require_GET
@profile_required(Profile.QUALITY)
def vocabulary_list(request):
    vocabularies = Vocabulary.objects.order_by("name")
    return render(request, "vocab/lists.html", {"vocabularies": vocabularies})


@require_http_methods(["GET", "POST"])
@profile_required(Profile.QUALITY)
def vocabulary_detail(request, code):
    vocabulary = get_object_or_404(Vocabulary, code=code)
    form = TermForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.add_term(
                vocabulary,
                by=request.user,
                label=form.cleaned_data["label"],
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as exc:
            _errors(request, exc)
        else:
            messages.success(request, "Termo incluído; a versão da lista subiu.")
            return redirect("vocab:detail", code=vocabulary.code)
    context = {
        "vocabulary": vocabulary,
        "terms": vocabulary.terms.order_by("position", "label"),
        "form": form,
    }
    return render(request, "vocab/detail.html", context)


@require_POST
@profile_required(Profile.QUALITY)
def term_change(request, term_id):
    term = get_object_or_404(Term.objects.select_related("vocabulary"), pk=term_id)
    form = TermChangeForm(request.POST)
    if not form.is_valid():
        messages.error(request, services.REASON_REQUIRED)
        return redirect("vocab:detail", code=term.vocabulary.code)
    action = form.cleaned_data["action"]
    reason = form.cleaned_data["reason"]
    try:
        if action == "rotulo":
            services.relabel_term(
                term, by=request.user, label=form.cleaned_data["label"], reason=reason
            )
            messages.success(request, "Rótulo corrigido; a versão da lista subiu.")
        else:
            active = action == "reativar"
            services.set_term_active(term, by=request.user, active=active, reason=reason)
            messages.success(request, "Termo reativado." if active else "Termo desativado.")
    except ValidationError as exc:
        _errors(request, exc)
    return redirect("vocab:detail", code=term.vocabulary.code)
