from django.apps import AppConfig


class OperationsConfig(AppConfig):
    name = "sgp.operations"
    label = "operations"
    verbose_name = "Operação e validação"

    def ready(self):
        from sgp.audit.event_types import register_many

        register_many(
            {
                "operations.backup_requested": "Cópia de segurança pedida pela TI",
                "operations.backup_completed": "Cópia de segurança concluída",
                "operations.backup_failed": "Falha na cópia de segurança (alerta)",
                "operations.backup_removed": "Cópia de segurança removida pela retenção",
                "operations.backup_stale": "Sem cópia de segurança recente (alerta)",
                "operations.restore_requested": "Teste de restauração pedido pela TI",
                "operations.restore_tested": "Teste de restauração executado",
                "operations.qualification_requested": "Qualificação pedida pela tela",
                "operations.qualification_executed": "Qualificação executada",
                "operations.report_downloaded": "Relatório de qualificação baixado",
                "operations.access_review_exported": "Revisão de acessos exportada",
            }
        )
