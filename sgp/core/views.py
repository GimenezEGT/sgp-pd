from django.contrib.auth.decorators import login_not_required
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from sgp.accounts.profiles import active_profiles
from sgp.core.navigation import nav_for


@require_GET
def home(request):
    profiles = active_profiles(request.user)
    sections: dict[str, list] = {}
    for item in nav_for(profiles):
        sections.setdefault(item["section"], []).append(item)
    return render(request, "core/home.html", {"sections": sections})


@login_not_required
@require_GET
def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")
