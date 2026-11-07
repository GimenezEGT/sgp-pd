"""Manutenção das listas controladas pela Qualidade/AR (US5: FR-019 da feature 003)."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from sgp.accounts.profiles import Profile
from sgp.vocab import services
from sgp.vocab.models import Term, Vocabulary, active_terms, get_term

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def quality(make_user, vocab_seed):
    return make_user(None, Profile.QUALITY)


@pytest.fixture
def sample_types(vocab_seed):
    return Vocabulary.objects.get(code="tipo-amostra")


@pytest.mark.req("003:FR-019")
def test_carga_inicial_das_listas_de_amostras(sample_types):
    labels = list(active_terms("tipo-amostra").values_list("label", flat=True))
    assert labels == ["Soro", "Plasma", "Sangue total", "Urina", "Líquor", "DNA", "RNA", "Outros"]
    storage = list(active_terms("armazenamento").values_list("label", flat=True))
    assert storage == [chr(0x2212) + "20 °C", "2 a 8 °C", "2 a 30 °C", "15 a 30 °C", "37 °C"]


@pytest.mark.req("003:FR-019")
def test_incluir_termo_sobe_a_versao_e_vai_para_a_trilha(quality, sample_types, events):
    version = sample_types.version
    term = services.add_term(sample_types, by=quality, label="Swab nasal")
    sample_types.refresh_from_db()
    assert term.code == "swab-nasal" and term.position == 9
    assert sample_types.version == version + 1
    event = events("vocab.term_created")[-1]
    assert event.new_value == {
        "lista": "tipo-amostra",
        "rotulo": "Swab nasal",
        "versao_lista": version + 1,
    }
    with pytest.raises(ValidationError, match="Já existe o termo"):
        services.add_term(sample_types, by=quality, label="swab NASAL")


@pytest.mark.req("003:FR-019")
def test_corrigir_rotulo_exige_motivo(quality, sample_types, events):
    term = get_term("tipo-amostra", "outros")
    with pytest.raises(ValidationError, match="motivo"):
        services.relabel_term(term, by=quality, label="Outros (especificar)", reason="")
    services.relabel_term(
        term, by=quality, label="Outros (especificar)", reason="Rótulo do formulário"
    )
    assert Term.objects.get(pk=term.pk).label == "Outros (especificar)"
    event = events("vocab.term_updated")[-1]
    assert event.old_value == {"rotulo": "Outros"} and event.reason == "Rótulo do formulário"


@pytest.mark.req("003:FR-019")
def test_desativar_e_reativar_sem_apagar(quality, sample_types, events):
    term = get_term("tipo-amostra", "liquor")
    services.set_term_active(term, by=quality, active=False, reason="Fora de uso")
    assert not active_terms("tipo-amostra").filter(pk=term.pk).exists()
    assert Term.objects.filter(pk=term.pk).exists()
    services.set_term_active(term, by=quality, active=True, reason="Voltou a ser usado")
    assert active_terms("tipo-amostra").filter(pk=term.pk).exists()
    assert events("vocab.term_deactivated")[-1].new_value["ativo"] is False
    assert events("vocab.term_reactivated")[-1].old_value == {"ativo": False}


@pytest.mark.req("003:FR-019")
def test_so_a_qualidade_altera_listas(client, login_as, sample_types, make_user, events):
    with pytest.raises(ValidationError, match="Só a Qualidade"):
        services.add_term(sample_types, by=make_user(None, Profile.RD_MANAGER), label="Novo")
    login_as(Profile.ANALYST, Profile.RD_MANAGER, Profile.ADMIN)
    response = client.post(reverse("vocab:detail", args=["tipo-amostra"]), {"label": "Novo"})
    assert response.status_code == 403
    assert events("auth.permission_denied")
    assert not Term.objects.filter(label="Novo").exists()


@pytest.mark.req("003:FR-019")
def test_fluxo_pelas_telas(client, quality, sample_types):
    client.force_login(quality)
    assert "Tipos de amostra" in client.get(reverse("vocab:lists")).content.decode()
    client.post(
        reverse("vocab:detail", args=["tipo-amostra"]), {"label": "Swab nasal", "reason": ""}
    )
    term = Term.objects.get(label="Swab nasal")
    client.post(
        reverse("vocab:term", args=[term.pk]),
        {"action": "desativar", "label": term.label, "reason": "Teste de desativação"},
    )
    assert not Term.objects.get(pk=term.pk).is_active
    page = client.get(reverse("vocab:detail", args=["tipo-amostra"])).content.decode()
    assert "Swab nasal" in page and "Desativado" in page
    sample_types.refresh_from_db()
    assert sample_types.version == 3
