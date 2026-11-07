"""Arquivo guardado: metadados somente de inclusão; o conteúdo fica endereçado pelo SHA-256."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from sgp.core.models import AppendOnlyModel


class StoredFile(AppendOnlyModel):
    sha256 = models.CharField("resumo SHA-256", max_length=64, db_index=True)
    original_name = models.CharField("nome original", max_length=255)
    content_type = models.CharField("tipo", max_length=100)
    size = models.PositiveBigIntegerField("tamanho (bytes)")
    storage_name = models.CharField("caminho no armazenamento", max_length=80)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="enviado por",
    )
    uploaded_at = models.DateTimeField("enviado em", default=timezone.now)

    class Meta:
        verbose_name = "arquivo guardado"
        verbose_name_plural = "arquivos guardados"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.original_name

    @property
    def size_display(self) -> str:
        if self.size >= 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB".replace(".", ",")
        if self.size >= 1024:
            return f"{self.size / 1024:.0f} KB"
        return f"{self.size} bytes"
