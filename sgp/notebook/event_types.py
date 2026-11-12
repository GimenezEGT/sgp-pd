"""Eventos do caderno de laboratório (contrato rotas-ui.md da feature 008)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "notebook.created": "Entrada do caderno criada",
        "notebook.updated": "Entrada do caderno alterada",
        "notebook.material_added": "Material ligado à entrada do caderno",
        "notebook.material_removed": "Material retirado da entrada do caderno",
        "notebook.attachment_added": "Anexo incluído na entrada do caderno",
        "notebook.attachment_removed": "Anexo retirado da entrada do caderno",
        "notebook.relevance_changed": "Relevância da entrada do caderno alterada",
        "notebook.signed": "Entrada do caderno assinada pelo autor",
        "notebook.witnessed": "Entrada do caderno assinada pela testemunha",
        "notebook.integrity_failed": "Conteúdo da entrada do caderno não confere com a assinatura",
        "notebook.addendum_added": "Adendo assinado incluído na entrada do caderno",
        "notebook.linked": "Vínculo da entrada do caderno incluído",
        "notebook.unlinked": "Vínculo da entrada do caderno retirado",
        "notebook.promoted": "Dados da entrada do caderno promovidos para estudo",
        "notebook.template_created": "Modelo de entrada do caderno criado",
        "notebook.template_updated": "Modelo de entrada do caderno alterado (nova versão)",
        "notebook.template_deactivated": "Modelo de entrada do caderno desativado",
    }
)
