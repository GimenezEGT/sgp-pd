from datetime import timedelta

from django import forms
from django.utils import timezone

from sgp.accounts.models import User


class DelegationForm(forms.Form):
    delegate = forms.ModelChoiceField(label="Delegado", queryset=User.objects.none())
    starts_on = forms.DateField(label="Início", widget=forms.DateInput(attrs={"type": "date"}))
    ends_on = forms.DateField(
        label="Fim (até 30 dias)", widget=forms.DateInput(attrs={"type": "date"})
    )
    reason = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = User.objects.filter(is_active=True).order_by("full_name", "username")
        if user is not None:
            queryset = queryset.exclude(pk=user.pk)
        self.fields["delegate"].queryset = queryset
        self.fields["delegate"].label_from_instance = lambda person: (
            person.get_full_name() or person.username
        )
        today = timezone.localdate()
        self.fields["starts_on"].initial = today
        self.fields["ends_on"].initial = today + timedelta(days=6)


class EndDelegationForm(forms.Form):
    reason = forms.CharField(
        label="Motivo do encerramento", widget=forms.Textarea(attrs={"rows": 2})
    )
