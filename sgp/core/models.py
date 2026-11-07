"""Modelos base que aplicam o "nada é apagado" (princípio I da constituição).

- ProtectedModel: nenhum registro é excluído fisicamente (nem por instância nem por queryset).
- AppendOnlyModel: além disso, registro gravado nunca é alterado.

Os privilégios do papel de banco da aplicação reforçam as mesmas regras (sgp.core.db_privileges).
"""

from django.db import models


class DeletionNotAllowedError(Exception):
    """Tentativa de excluir fisicamente um registro do SGP-P&D."""


class ImmutableRecordError(Exception):
    """Tentativa de alterar um registro somente de inclusão."""


DELETION_MESSAGE = (
    "Registros do SGP-P&D não são apagados; use desativação, encerramento ou nova versão."
)
IMMUTABLE_MESSAGE = "Este registro é somente de inclusão e não pode ser alterado."


class ProtectedQuerySet(models.QuerySet):
    def delete(self):
        raise DeletionNotAllowedError(DELETION_MESSAGE)

    delete.queryset_only = True


class AppendOnlyQuerySet(ProtectedQuerySet):
    def update(self, **kwargs):
        raise ImmutableRecordError(IMMUTABLE_MESSAGE)

    def bulk_update(self, objs, fields, batch_size=None):
        raise ImmutableRecordError(IMMUTABLE_MESSAGE)

    def update_or_create(self, *args, **kwargs):
        raise ImmutableRecordError(IMMUTABLE_MESSAGE)


class ProtectedModel(models.Model):
    objects = ProtectedQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise DeletionNotAllowedError(DELETION_MESSAGE)


class AppendOnlyModel(ProtectedModel):
    """Registro somente de inclusão; a tabela entra na lista append-only dos privilégios."""

    append_only = True

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableRecordError(IMMUTABLE_MESSAGE)
        kwargs["force_insert"] = True
        kwargs.pop("force_update", None)
        kwargs.pop("update_fields", None)
        return super().save(*args, **kwargs)
