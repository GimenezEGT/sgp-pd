"""Preferências de notificação (contrato rotas-ui.md da feature 010)."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from . import services
from .models import Notification


@require_http_methods(["GET", "POST"])
def preferences(request):
    if request.method == "POST":
        services.set_preferences(request.user, request.POST.getlist("ligadas"))
        messages.success(request, "Preferências de notificação gravadas.")
        return redirect("notifications:preferences")
    context = {
        "rows": services.preferences(request.user),
        "recent": Notification.objects.filter(user=request.user)[:20],
        "email": request.user.email,
    }
    return render(request, "notifications/preferences.html", context)
