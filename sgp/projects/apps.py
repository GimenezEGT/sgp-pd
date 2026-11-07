from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "sgp.projects"
    label = "projects"
    verbose_name = "Projetos"

    def ready(self):
        from . import event_types  # noqa: F401
