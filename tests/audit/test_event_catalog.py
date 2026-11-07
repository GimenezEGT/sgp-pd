"""Catálogo mínimo de eventos da feature 001 (FR-017)."""

import pytest

from sgp.audit.event_types import EVENT_TYPES, choices, label_for, register

REQUIRED = {
    "auth.login_succeeded",
    "auth.login_failed",
    "auth.logout",
    "auth.session_expired",
    "auth.lockout_started",
    "auth.lockout_released",
    "auth.login_blocked",
    "auth.auth_unavailable",
    "auth.permission_denied",
    "accounts.access_requested",
    "accounts.access_request_decided",
    "accounts.user_created",
    "accounts.user_updated",
    "accounts.profile_granted",
    "accounts.profile_revoked",
    "audit.exported",
    "audit.chain_verified",
}


@pytest.mark.req("001:FR-017")
def test_eventos_minimos_registrados_com_rotulo():
    assert REQUIRED <= set(EVENT_TYPES)
    for code in REQUIRED:
        assert label_for(code) and label_for(code) != code


def test_rotulo_duplicado_diferente_e_recusado():
    with pytest.raises(ValueError):
        register("audit.exported", "Outro rótulo")


def test_escolhas_ordenadas_por_rotulo():
    labels = [label for _, label in choices()]
    assert labels == sorted(labels)
