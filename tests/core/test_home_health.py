import pytest
from django.urls import reverse

from sgp.accounts.profiles import Profile

pytestmark = pytest.mark.django_db


def test_saude_responde_sem_login(client):
    response = client.get(reverse("core:health"))
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.req("001:FR-009")
def test_inicio_mostra_atalhos_da_soma_dos_perfis(client, login_as):
    login_as(Profile.ADMIN, Profile.QUALITY)
    response = client.get(reverse("core:home"))
    content = response.content.decode()
    assert response.status_code == 200
    assert "Pessoas e perfis" in content
    assert "Trilha de auditoria" in content
    assert "Integridade da trilha" in content


def test_inicio_do_leitor_nao_mostra_administracao(client, login_as):
    login_as(Profile.READER)
    content = client.get(reverse("core:home")).content.decode()
    assert "Pessoas e perfis" not in content
    assert "Trilha de auditoria" not in content
