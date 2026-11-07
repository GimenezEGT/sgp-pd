from django import template

from sgp.core.formatting import compact_json, local_date, local_datetime

register = template.Library()


@register.filter
def datahora(value):
    return local_datetime(value)


@register.filter
def data(value):
    return local_date(value)


@register.filter
def json_compacto(value):
    return compact_json(value)


@register.filter
def rotulo_evento(code):
    from sgp.audit.event_types import label_for

    return label_for(code)


@register.filter
def rotulo_quebra(kind):
    from sgp.audit.services import break_label

    return break_label(kind)


@register.filter
def rotulo_perfil(code):
    from sgp.accounts.profiles import Profile

    try:
        return Profile(code).label
    except ValueError:
        return code
