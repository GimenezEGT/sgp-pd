"""Entrega de arquivo com o SHA-256 conferido (FR-020, SC-005 da feature 003)."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET

from sgp.accounts.profiles import deny_access

from . import access, storage
from .models import StoredFile


@require_GET
def download(request, file_id):
    stored = get_object_or_404(StoredFile, pk=file_id)
    if not access.can_read(request.user, stored):
        return deny_access(request, "sem acesso ao registro dono do arquivo")
    try:
        data = storage.read_verified(stored)
    except storage.IntegrityFailure as failure:
        # A resposta é normal (sem exceção) para o evento não ser desfeito com a transação.
        storage.record_integrity_failure(failure, request=request)
        return render(request, "files/integrity_failed.html", {"stored": stored}, status=409)
    response = HttpResponse(data, content_type=stored.content_type)
    response["Content-Disposition"] = content_disposition_header(
        as_attachment=True, filename=stored.original_name
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response
