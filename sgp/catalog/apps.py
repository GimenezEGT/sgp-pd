from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "sgp.catalog"
    label = "catalog"
    verbose_name = "Cadastros de apoio"

    def ready(self):
        from sgp.files import access

        from . import event_types  # noqa: F401
        from .files_access import catalog_file_policy

        access.register(catalog_file_policy)
