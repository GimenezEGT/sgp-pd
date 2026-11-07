"""Campos de formulário em padrão brasileiro (FR-009 da feature 002)."""

from decimal import Decimal, InvalidOperation

from django import forms

from sgp.core.formatting import format_decimal_br

NBSP = chr(160)
MAX_MONEY = Decimal("999999999999.99")  # Decimal(14,2)


def parse_brl(text: str | None) -> Decimal | None:
    """Converte '1.234.567,89', '1234567,89', 'R$ 1.234,00' ou '1234.56' em Decimal."""
    raw = (text or "").strip().replace("R$", "").replace(NBSP, "").replace(" ", "")
    if not raw:
        return None
    if "," in raw:
        normalized = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1 or (raw.count(".") == 1 and len(raw.split(".")[1]) == 3):
        normalized = raw.replace(".", "")
    else:
        normalized = raw
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(raw) from exc


class BRLMoneyField(forms.Field):
    default_error_messages = {
        "invalid": "Informe um valor em reais, por exemplo 1.234,56.",
        "negative": "O valor não pode ser negativo.",
        "places": "Use no máximo 2 casas decimais.",
        "too_big": "Valor acima do limite permitido.",
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget", forms.TextInput(attrs={"inputmode": "decimal", "placeholder": "0,00"})
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, Decimal | int | float):
            return format_decimal_br(value, 2)
        return value

    def to_python(self, value):
        text = "" if value in self.empty_values else str(value).strip()
        try:
            number = parse_brl(text)
        except ValueError as exc:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid") from exc
        if number is None:
            return None
        if number < 0:
            raise forms.ValidationError(self.error_messages["negative"], code="negative")
        if -number.as_tuple().exponent > 2:
            raise forms.ValidationError(self.error_messages["places"], code="places")
        if number > MAX_MONEY:
            raise forms.ValidationError(self.error_messages["too_big"], code="too_big")
        return number.quantize(Decimal("0.01"))


class LinesField(forms.CharField):
    """Lista de textos digitada uma por linha; devolve lista sem linhas vazias."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.Textarea(attrs={"rows": 3}))
        kwargs.setdefault("required", False)
        kwargs.setdefault("help_text", "Um item por linha.")
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list | tuple):
            return "\n".join(value)
        return value

    def to_python(self, value):
        text = super().to_python(value) or ""
        return [line.strip() for line in text.splitlines() if line.strip()]
