"""Modelos de entrada por tipo de experimento (FR-005)."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from sgp.notebook import services
from sgp.notebook.models import EntryTemplate

pytestmark = pytest.mark.req("008:FR-005")

DATA = {
    "name": "Teste de formulação",
    "objective": "Avaliar a formulação candidata",
    "procedure": "- Pesar os insumos\n- Dissolver",
}


def test_qualidade_e_gestor_mantem_modelos(quality, manager, analyst, events):
    template = services.create_template(by=quality, data=DATA)
    assert template.version == 1 and template.procedure.startswith("<ul>")
    services.create_template(by=manager, data={**DATA, "name": "Estabilidade preliminar"})
    with pytest.raises(PermissionDenied):
        services.create_template(by=analyst, data={**DATA, "name": "Outro"})
    with pytest.raises(ValidationError, match="Já existe"):
        services.create_template(by=quality, data={**DATA, "name": "teste de FORMULAÇÃO"})
    assert len(events("notebook.template_created")) == 2


def test_alteracao_cria_versao_e_entrada_antiga_nao_muda(quality, make_entry, events):
    first = services.create_template(by=quality, data=DATA)
    old_entry = make_entry(template=first)
    assert old_entry.objective == "<p>Avaliar a formulação candidata</p>"
    assert old_entry.template == first
    with pytest.raises(ValidationError, match="motivo"):
        services.update_template(first, by=quality, data=DATA, reason="")
    second = services.update_template(
        first, by=quality, data={**DATA, "objective": "Comparar duas formulações"}, reason="Escopo"
    )
    first.refresh_from_db()
    assert (second.version, second.lineage, second.is_current) == (2, first.lineage, True)
    assert not first.is_current
    old_entry.refresh_from_db()
    assert old_entry.objective == "<p>Avaliar a formulação candidata</p>"
    new_entry = make_entry("Nova", template=second)
    assert new_entry.objective == "<p>Comparar duas formulações</p>"
    with pytest.raises(ValidationError, match="vigente"):
        make_entry("Com a versão velha", template=first)
    with pytest.raises(ValidationError, match="Nada mudou"):
        services.update_template(
            second, by=quality, data={**DATA, "objective": "Comparar duas formulações"}, reason="x"
        )
    assert events("notebook.template_updated")[-1].reason == "Escopo"


def test_desativar_tira_da_escolha(quality, make_entry):
    template = services.create_template(by=quality, data=DATA)
    services.deactivate_template(template, by=quality, reason="Substituído por procedimento")
    assert template not in services.active_templates()
    with pytest.raises(ValidationError):
        make_entry(template=EntryTemplate.objects.get(pk=template.pk))


def test_telas_dos_modelos(client, quality, analyst):
    client.force_login(analyst)
    assert client.get(reverse("notebook:templates")).status_code == 200
    assert client.post(reverse("notebook:templates"), DATA).status_code == 403
    client.force_login(quality)
    response = client.post(reverse("notebook:templates"), DATA)
    template = EntryTemplate.objects.get(name=DATA["name"])
    assert response.status_code == 302
    detail = reverse("notebook:template_detail", args=[template.pk])
    client.post(detail, {**DATA, "procedure": "Novo procedimento", "motivo": "Revisão"})
    assert EntryTemplate.objects.filter(lineage=template.lineage).count() == 2
    page = client.get(detail).content.decode()
    assert "Versão 2" in page and "substituída" in page
