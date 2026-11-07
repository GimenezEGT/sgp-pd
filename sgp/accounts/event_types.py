"""Eventos de auditoria de autenticação, pessoas e perfis (contrato eventos-auditoria.md)."""

from sgp.audit.event_types import register_many

register_many(
    {
        "auth.login_succeeded": "Login aceito",
        "auth.login_failed": "Login recusado",
        "auth.login_blocked": "Tentativa durante bloqueio",
        "auth.lockout_started": "Login bloqueado por tentativas",
        "auth.lockout_released": "Login desbloqueado",
        "auth.auth_unavailable": "Serviço de autenticação indisponível",
        "auth.logout": "Logout",
        "auth.session_expired": "Sessão encerrada por inatividade",
        "auth.permission_denied": "Acesso negado",
        "accounts.user_created": "Cadastro de pessoa criado",
        "accounts.user_updated": "Cadastro de pessoa alterado",
        "accounts.profile_granted": "Perfil concedido",
        "accounts.profile_revoked": "Perfil revogado",
        "accounts.access_requested": "Acesso solicitado",
        "accounts.access_request_decided": "Solicitação de acesso decidida",
    }
)
