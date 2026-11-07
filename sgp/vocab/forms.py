from django import forms


class TermForm(forms.Form):
    label = forms.CharField(label="Novo termo", max_length=200)
    reason = forms.CharField(
        label="Motivo (opcional)", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )


class TermChangeForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("rotulo", "Corrigir rótulo"),
            ("desativar", "Desativar"),
            ("reativar", "Reativar"),
        ]
    )
    label = forms.CharField(label="Rótulo", max_length=200, required=False)
    reason = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 2}))
