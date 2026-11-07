"""Listas controladas (vocabulários) mantidas como dados, não como código (princípio IV)."""

from django.db import models

from sgp.core.models import ProtectedModel, ProtectedQuerySet

TECHNOLOGY = "tecnologia"
SUBDOCUMENT_TYPE = "tipo-subdocumento"


class Vocabulary(ProtectedModel):
    code = models.SlugField("código", max_length=60, unique=True)
    name = models.CharField("nome", max_length=200)
    description = models.TextField("descrição", blank=True)
    version = models.PositiveIntegerField("versão", default=1)

    class Meta:
        verbose_name = "lista controlada"
        verbose_name_plural = "listas controladas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TermQuerySet(ProtectedQuerySet):
    def of(self, vocabulary_code: str):
        return self.filter(vocabulary__code=vocabulary_code)

    def active(self):
        return self.filter(is_active=True)


class Term(ProtectedModel):
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.PROTECT, related_name="terms")
    code = models.SlugField("código", max_length=60)
    label = models.CharField("rótulo", max_length=200)
    position = models.PositiveIntegerField("ordem", default=0)
    is_active = models.BooleanField("ativo", default=True)

    objects = TermQuerySet.as_manager()

    class Meta:
        verbose_name = "termo"
        verbose_name_plural = "termos"
        ordering = ["vocabulary", "position", "label"]
        constraints = [
            models.UniqueConstraint(fields=["vocabulary", "code"], name="vocab_term_unique_code")
        ]

    def __str__(self) -> str:
        return self.label


def active_terms(vocabulary_code: str):
    return Term.objects.of(vocabulary_code).active()


def get_term(vocabulary_code: str, code: str) -> Term:
    return Term.objects.get(vocabulary__code=vocabulary_code, code=code)
