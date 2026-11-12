"""Entradas do caderno ligadas a um subdocumento, estudo ou cadastro (o outro lado do vínculo)."""

from django import template

register = template.Library()


@register.inclusion_tag("notebook/_linked_entries.html", takes_context=True)
def notebook_links(context, obj):
    from sgp.notebook.services import linked_entries

    request = context.get("request")
    user = getattr(request, "user", None)
    return {"items": linked_entries(obj, user=user) if user is not None else []}
