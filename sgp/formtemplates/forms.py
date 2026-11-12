import json

from django import forms
from django.core.exceptions import ValidationError


class DraftForm(forms.Form):
    reference = forms.CharField(label="Referência", max_length=200)
    valid_from = forms.DateField(
        label="Início de vigência",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        help_text="Documentos criados a partir desta data usam esta versão.",
    )
    definition = forms.CharField(
        label="Definição (capa e tópicos, em JSON)",
        widget=forms.Textarea(attrs={"rows": 30, "spellcheck": "false", "class": "codigo"}),
        help_text="Formato em specs/004-modelos-subdocumentos/contracts/definicao-modelo.md.",
    )
    row_version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean_definition(self):
        try:
            return json.loads(self.cleaned_data["definition"])
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"JSON inválido na linha {exc.lineno}, coluna {exc.colno}: {exc.msg}."
            ) from exc
