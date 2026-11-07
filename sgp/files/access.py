"""Quem pode ler um arquivo: decidido pelas apps donas do registro que o referencia.

Cada app registra uma política `policy(user, stored_file) -> bool`. O arquivo só é entregue se
alguma política permitir; arquivo sem dono conhecido é negado (menor privilégio, princípio VII).
"""

from collections.abc import Callable

Policy = Callable[[object, object], bool]

_POLICIES: list[Policy] = []


def register(policy: Policy) -> Policy:
    if policy not in _POLICIES:
        _POLICIES.append(policy)
    return policy


def can_read(user, stored) -> bool:
    return any(policy(user, stored) for policy in _POLICIES)
