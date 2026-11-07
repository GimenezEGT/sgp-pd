"""Backend de autenticação falso para os testes de regra: simula o diretório da rede (AD)."""

DIRECTORY: dict[str, dict] = {}
STATE = {"unavailable": False, "calls": 0}
DEFAULT_PASSWORD = "Senha#Teste1"


def reset() -> None:
    DIRECTORY.clear()
    STATE.update(unavailable=False, calls=0)


def add_person(username, password=DEFAULT_PASSWORD, groups=(), disabled=False, **attrs) -> None:
    data = {
        "full_name": f"Pessoa {username}",
        "first_name": "Pessoa",
        "last_name": username,
        "email": f"{username}@teste.local",
        "job_title": "Analista de P&D",
    }
    data.update(attrs)
    DIRECTORY[username.strip().lower()] = {
        "password": password,
        "attrs": data,
        "groups": {group.lower() for group in groups},
        "disabled": disabled,
    }


def set_groups(username, groups) -> None:
    DIRECTORY[username.lower()]["groups"] = {group.lower() for group in groups}


class FakeNetworkBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        STATE["calls"] += 1
        if STATE["unavailable"]:
            import ldap
            from django_auth_ldap.backend import ldap_error

            ldap_error.send(
                sender=type(self),
                context="authenticate",
                user=None,
                request=request,
                exception=ldap.SERVER_DOWN({"desc": "Can't contact LDAP server"}),
            )
            return None
        key = (username or "").strip().lower()
        entry = DIRECTORY.get(key)
        if entry is None or entry["disabled"] or entry["password"] != password:
            return None
        from sgp.accounts.models import User

        user = User.objects.filter(username=key).first() or User(username=key)
        for name, value in entry["attrs"].items():
            setattr(user, name, value)
        user.save()
        user.network_group_dns = set(entry["groups"])
        return user

    def get_user(self, user_id):
        from sgp.accounts.models import User

        return User.objects.filter(pk=user_id).first()
