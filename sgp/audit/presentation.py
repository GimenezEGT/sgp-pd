"""Apresentação de eventos para quem consulta a trilha: máscara de campos sensíveis e rótulo do
projeto (código ou nome). Não altera o que está gravado."""

from django.apps import apps

from . import masking


def _project_model():
    try:
        return apps.get_model("projects", "Project")
    except LookupError:
        return None


class EventPresenter:
    def __init__(self, viewer):
        self.viewer = viewer
        self._mask_cache: dict = {}
        self._projects: dict = {}

    def values(self, event) -> tuple:
        return masking.present(event, self.viewer, self._mask_cache)

    def project_label(self, project_id) -> str:
        if project_id is None:
            return ""
        if project_id not in self._projects:
            model = _project_model()
            row = None
            if model is not None:
                row = model.objects.filter(pk=project_id).values_list("code", "title").first()
            self._projects[project_id] = (row[0] or row[1]) if row else str(project_id)
        return self._projects[project_id]

    def decorate(self, events) -> list:
        decorated = []
        for event in events:
            event.display_old, event.display_new = self.values(event)
            event.project_label = self.project_label(event.project_id)
            decorated.append(event)
        return decorated
