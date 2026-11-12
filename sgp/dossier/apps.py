from django.apps import AppConfig


class DossierConfig(AppConfig):
    name = "sgp.dossier"
    label = "dossier"
    verbose_name = "Dossiê técnico para a ANVISA"

    def ready(self):
        from sgp.audit.event_types import register_many

        register_many(
            {
                "dossier.definition_published": "Definição do dossiê técnico publicada",
                "dossier.text_saved": "Texto padrão do dossiê gravado",
                "dossier.text_approved": "Texto padrão do dossiê aprovado com senha",
                "dossier.company_updated": "Dados da empresa e do responsável técnico alterados",
                "dossier.supplement_saved": "Complemento de item do dossiê gravado",
                "dossier.generated": "Dossiê técnico gerado",
                "dossier.downloaded": "Dossiê técnico baixado",
                "dossier.submitted": "Envio do dossiê técnico registrado",
                "dossier.result_recorded": "Resultado da petição registrado",
                "dossier.addendum_generated": "Aditamento do dossiê técnico gerado",
            }
        )
