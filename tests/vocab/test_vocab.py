"""Listas controladas como dados (constituição IV; feature 002)."""

import pytest

from sgp.core.models import DeletionNotAllowedError
from sgp.vocab.models import SUBDOCUMENT_TYPE, TECHNOLOGY, Term, active_terms, get_term

pytestmark = pytest.mark.django_db


@pytest.mark.req("002:FR-001")
def test_tecnologias_da_carga_inicial():
    assert [t.label for t in active_terms(TECHNOLOGY)] == [
        "Bioquímica",
        "Imunologia",
        "Biologia molecular",
        "Outras",
    ]


@pytest.mark.req("002:FR-006")
def test_tipos_de_subdocumento_do_psg20():
    labels = [t.label for t in active_terms(SUBDOCUMENT_TYPE)]
    assert labels[0] == "Entrada de Projeto" and labels[-1] == "Alteração de Projeto"
    assert len(labels) == 9


def test_termo_inativo_sai_das_listas_e_nao_e_apagado():
    term = get_term(TECHNOLOGY, "outras")
    term.is_active = False
    term.save()
    assert term not in active_terms(TECHNOLOGY)
    with pytest.raises(DeletionNotAllowedError):
        term.delete()
    assert Term.objects.filter(pk=term.pk).exists()
