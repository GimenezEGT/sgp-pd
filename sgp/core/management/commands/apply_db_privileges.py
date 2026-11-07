from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sgp.core.db_privileges import apply_privileges, role_exists


class Command(BaseCommand):
    help = "Aplica os privilégios do papel de banco da aplicação (sem DELETE; sem UPDATE nas tabelas append-only)."

    def add_arguments(self, parser):
        parser.add_argument("--role", default=None, help="papel da aplicação (padrão: DB_APP_ROLE)")
        parser.add_argument(
            "--if-role-exists",
            action="store_true",
            help="não falha quando o papel não existe (uso em testes fora do contêiner)",
        )

    def handle(self, *args, **options):
        role = options["role"] or settings.DB_APP_ROLE
        if not role_exists(role):
            if options["if_role_exists"]:
                self.stdout.write(f"Papel {role} não existe; privilégios não aplicados.")
                return
            raise CommandError(f"O papel de banco {role} não existe.")
        result = apply_privileges(role)
        self.stdout.write(
            self.style.SUCCESS(
                f"Privilégios aplicados ao papel {role}. "
                f"Append-only: {', '.join(result['append_only']) or 'nenhuma'}. "
                f"Com DELETE: {', '.join(result['deletable']) or 'nenhuma'}."
            )
        )
