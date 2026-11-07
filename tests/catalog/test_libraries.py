"""Normas, referências e busca enquanto digita (US5: FR-007, FR-018, SC-004 da feature 003)."""

import time
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.catalog import versioning
from sgp.catalog.kinds import REFERENCES, STANDARDS
from sgp.catalog.models import BibliographicReference, Material, Standard

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def editor(make_user):
    return make_user(None, Profile.QUALITY)


def make_standard(by, identifier="NBR ISO 13485:2016", scope="national"):
    return versioning.create_record(
        STANDARDS,
        by=by,
        data={"identifier": identifier, "title": "Título da norma", "scope": scope},
    )


@pytest.mark.req("003:FR-018")
def test_norma_com_identificacao_unica_entre_vigentes(editor):
    standard = make_standard(editor)
    assert standard.get_scope_display() == "Nacional"
    with pytest.raises(ValidationError, match="Já existe norma vigente"):
        make_standard(editor)
    international = make_standard(editor, identifier="CLSI EP25", scope="international")
    assert international.get_scope_display() == "Internacional"


@pytest.mark.req("003:FR-018")
def test_norma_repetida_pela_tela(client, editor):
    make_standard(editor)
    client.force_login(editor)
    response = client.post(
        reverse("catalog:new", args=["normas"]),
        {"identifier": "NBR  ISO 13485:2016", "title": "Outra", "scope": "national"},
    )
    assert "Já existe norma vigente" in response.content.decode()
    assert Standard.objects.count() == 1


@pytest.mark.req("003:FR-018")
def test_referencia_com_ano_e_doi_opcionais(client, editor):
    reference = versioning.create_record(
        REFERENCES, by=editor, data={"citation": "AUTOR, A. Título. Revista, 2020."}
    )
    assert reference.year is None and reference.doi_or_url == ""
    client.force_login(editor)
    response = client.post(
        reverse("catalog:new", args=["referencias"]),
        {"citation": "AUTOR, B. Outro título.", "year": "1200", "doi_or_url": ""},
    )
    assert "Ano fora do intervalo" in response.content.decode()
    client.post(
        reverse("catalog:new", args=["referencias"]),
        {"citation": "AUTOR, B. Outro título.", "year": "2021", "doi_or_url": "10.1000/xyz"},
    )
    assert BibliographicReference.objects.filter(year=2021, doi_or_url="10.1000/xyz").exists()


@pytest.mark.req("003:FR-007")
def test_busca_por_trecho_de_codigo_ou_descricao(client, editor, make_material):
    make_material(editor, code="MP-ALFA-01", description="Cloreto de magnésio")
    make_material(editor, code="MP-BETA-02", description="Tampão fosfato")
    inactive = make_material(editor, code="MP-ALFA-99", description="Desativado")
    versioning.set_active(inactive, by=editor, active=False, reason="Fora de uso")
    client.force_login(editor)
    by_code = client.get(
        reverse("catalog:search", args=["insumos"]), {"q": "alfa"}
    ).content.decode()
    assert "MP-ALFA-01" in by_code and "MP-BETA-02" not in by_code and "MP-ALFA-99" not in by_code
    by_text = client.get(
        reverse("catalog:search", args=["insumos"]), {"q": "fosf"}
    ).content.decode()
    assert "MP-BETA-02" in by_text
    empty = client.get(reverse("catalog:search", args=["insumos"]), {"q": ""}).content.decode()
    assert "MP-" not in empty


@pytest.mark.req("003:FR-007")
def test_busca_traz_so_vigentes_e_ate_20(client, editor, make_material):
    material = make_material(editor, code="MP-VERS")
    versioning.lock_version(material, by=editor, reason="Assinado")
    successor, _ = versioning.update_record(
        material, by=editor, data={"description": "Nova"}, reason="Correção"
    )
    for index in range(25):
        make_material(editor, code=f"MP-LOTE-{index:02d}")
    client.force_login(editor)
    fragment = client.get(
        reverse("catalog:search", args=["insumos"]), {"q": "MP-"}
    ).content.decode()
    assert fragment.count("<li") == 20
    versions = client.get(
        reverse("catalog:search", args=["insumos"]), {"q": "VERS"}
    ).content.decode()
    assert f'data-registro="{successor.pk}"' in versions
    assert f'data-registro="{material.pk}"' not in versions


@pytest.mark.req("003:FR-007")
def test_lista_com_busca_e_desativados(client, editor, make_material):
    inactive = make_material(editor, code="MP-OFF")
    versioning.set_active(inactive, by=editor, active=False, reason="Fora de uso")
    client.force_login(editor)
    listing = client.get(reverse("catalog:list", args=["insumos"]), {"q": "OFF"}).content.decode()
    assert "MP-OFF" not in listing
    listing = client.get(
        reverse("catalog:list", args=["insumos"]), {"q": "OFF", "inativos": "1"}
    ).content.decode()
    assert "MP-OFF" in listing and "Desativado" in listing


@pytest.mark.req("003:FR-007")
def test_tipo_de_cadastro_inexistente(client, editor):
    client.force_login(editor)
    assert client.get(reverse("catalog:list", args=["bananas"])).status_code == 404


@pytest.mark.req("003:SC-004")
def test_busca_em_menos_de_1_segundo_com_10_mil_insumos(client, editor):
    Material.objects.bulk_create(
        [
            Material(
                lineage=uuid.uuid4(),
                code=f"COD-{index:05d}",
                description=f"Insumo de carga {index}",
                material_type="raw",
                created_by=editor,
            )
            for index in range(10_000)
        ],
        batch_size=2000,
    )
    client.force_login(editor)
    url = reverse("catalog:search", args=["insumos"])
    client.get(url, {"q": "COD-0"})
    start = time.monotonic()
    response = client.get(url, {"q": "carga 9876"})
    elapsed = time.monotonic() - start
    assert "COD-09876" in response.content.decode()
    assert elapsed < 1, f"busca levou {elapsed:.2f} s"
