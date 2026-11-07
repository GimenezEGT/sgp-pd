from django import forms

from .models import AccessRequest
from .profiles import Profile


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuário de rede",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha de rede",
        max_length=256,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class AccessRequestForm(forms.Form):
    justification = forms.CharField(
        label="Justificativa",
        min_length=10,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Informe o projeto, a sua função e quem aprova o acesso.",
    )


class GrantProfileForm(forms.Form):
    profile = forms.ChoiceField(label="Perfil", choices=Profile.choices)
    reason = forms.CharField(
        label="Motivo", max_length=2000, widget=forms.Textarea(attrs={"rows": 3})
    )
    approval_reference = forms.CharField(
        label="Referência da aprovação",
        max_length=500,
        help_text="Quem aprovou e onde (ex.: e-mail do Gestor de P&D de 07/11/2026, chamado TI-1234).",
    )

    def __init__(self, *args, unavailable=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile"].choices = [
            (code, label) for code, label in Profile.choices if code not in set(unavailable)
        ]


class ReasonForm(forms.Form):
    reason = forms.CharField(
        label="Motivo", max_length=2000, widget=forms.Textarea(attrs={"rows": 2})
    )


class RevokeProfileForm(forms.Form):
    reason = forms.CharField(
        label="Motivo da revogação", max_length=2000, widget=forms.Textarea(attrs={"rows": 2})
    )
    approval_reference = forms.CharField(
        label="Referência da aprovação",
        max_length=500,
        help_text="Quem aprovou a revogação e onde.",
    )


class DecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Decisão",
        choices=[
            (AccessRequest.Status.GRANTED, "Atendida"),
            (AccessRequest.Status.REJECTED, "Recusada"),
        ],
    )
    reason = forms.CharField(
        label="Motivo", max_length=2000, widget=forms.Textarea(attrs={"rows": 2})
    )


class PeopleSearchForm(forms.Form):
    q = forms.CharField(label="Buscar por login ou nome", required=False, max_length=150)
