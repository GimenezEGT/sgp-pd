from datetime import datetime, time, timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .event_types import choices as event_choices


class AuditFilterForm(forms.Form):
    usuario = forms.ModelChoiceField(
        label="Usuário", queryset=None, required=False, empty_label="Todos"
    )
    projeto = forms.IntegerField(label="Projeto (código interno)", required=False, min_value=1)
    de = forms.DateField(
        label="De",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    ate = forms.DateField(
        label="Até",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    tipo = forms.ChoiceField(label="Tipo de evento", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].queryset = get_user_model().objects.order_by("username")
        self.fields["usuario"].label_from_instance = lambda user: (
            f"{user.username} — {user.get_full_name()}"
        )
        self.fields["tipo"].choices = [("", "Todos"), *event_choices()]

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("de"), cleaned.get("ate")
        if start and end and start > end:
            raise forms.ValidationError("A data inicial não pode ser posterior à final.")
        return cleaned

    def apply(self, queryset):
        data = self.cleaned_data
        if data.get("usuario"):
            queryset = queryset.filter(actor=data["usuario"])
        if data.get("projeto"):
            queryset = queryset.filter(project_id=data["projeto"])
        tz = timezone.get_current_timezone()
        if data.get("de"):
            queryset = queryset.filter(
                occurred_at__gte=datetime.combine(data["de"], time.min, tzinfo=tz)
            )
        if data.get("ate"):
            next_day = datetime.combine(data["ate"] + timedelta(days=1), time.min, tzinfo=tz)
            queryset = queryset.filter(occurred_at__lt=next_day)
        if data.get("tipo"):
            queryset = queryset.filter(event_type=data["tipo"])
        return queryset

    def describe(self) -> str:
        data = self.cleaned_data
        user = data.get("usuario")
        parts = [
            f"Usuário: {user.username if user else 'todos'}",
            f"Projeto: {data.get('projeto') or 'todos'}",
            f"De: {data['de'].strftime('%d/%m/%Y') if data.get('de') else 'todos'}",
            f"Até: {data['ate'].strftime('%d/%m/%Y') if data.get('ate') else 'todos'}",
            f"Tipo: {data.get('tipo') or 'todos'}",
        ]
        return "; ".join(parts)

    def as_event_value(self) -> dict:
        data = self.cleaned_data
        return {
            "usuario": data["usuario"].username if data.get("usuario") else None,
            "projeto": data.get("projeto"),
            "de": data.get("de"),
            "ate": data.get("ate"),
            "tipo": data.get("tipo") or None,
        }
