from django.apps import AppConfig


class FormTemplatesConfig(AppConfig):
    name = "sgp.formtemplates"
    label = "formtemplates"
    verbose_name = "Modelos de formulário"

    def ready(self):
        from . import event_types  # noqa: F401
