"""Fixtures dos subdocumentos (feature 004). Dados fictícios criados só para os testes."""

from datetime import date

import pytest

from tests.catalog.conftest import lot_data, make_lot, make_material  # noqa: F401


@pytest.fixture
def manager(make_user):
    from sgp.accounts.profiles import Profile

    return make_user(None, Profile.RD_MANAGER)


@pytest.fixture
def project(open_project):
    return open_project()


@pytest.fixture
def analyst(project, make_user):
    from sgp.accounts.profiles import Profile
    from sgp.projects import services

    user = make_user(None, Profile.ANALYST)
    services.add_member(project, by=project.leader, user=user, role="Analista")
    return user


@pytest.fixture
def standard(make_user):
    from sgp.accounts.profiles import Profile
    from sgp.catalog import versioning
    from sgp.catalog.kinds import STANDARDS

    return versioning.create_record(
        STANDARDS,
        by=make_user(None, Profile.QUALITY),
        data={"identifier": "NBR TESTE 1:2026", "title": "Norma fictícia", "scope": "national"},
    )


def requirement_rows(applies=("exatidao", "precisao")):
    from sgp.vocab.models import Term

    rows = []
    for term in Term.objects.of("requisito-desempenho").order_by("position"):
        if term.code in applies:
            rows.append(
                {
                    "codigo": term.code,
                    "aplica": "sim",
                    "criterio": f"Critério {term.code}",
                    "justificativa": "",
                }
            )
        else:
            rows.append(
                {
                    "codigo": term.code,
                    "aplica": "nao",
                    "criterio": "",
                    "justificativa": "Não se aplica ao método",
                }
            )
    return rows


def entry_topics(standard_id, applies=("exatidao", "precisao")) -> dict:
    """Entrada completa (todos os obrigatórios) para os testes."""

    def topic(values, na=False, justification=""):
        return {"na": na, "justification": justification, "values": values}

    return {
        "amostras": topic({"tipos": ["soro"], "descricao": "Soro humano", "coleta": []}),
        "funcionalidade": topic({"funcao": ["diagnostico"], "descricao": ""}),
        "apresentacoes": topic({"reagentes": [{"reagente": "R1", "apresentacao": "2 x 50 mL"}]}),
        "armazenamento": topic(
            {
                "faixas": [{"reagente": "R1", "faixa": "2-8", "apos_aberto": "30 dias"}],
                "descricao": "",
            }
        ),
        "automacao": topic({"tipo": "manual", "descricao": ""}),
        "classificacao_uso": topic({"tipo": "unico", "descricao": ""}),
        "tipo_usuario": topic({"tipo": ["profissional"], "local_uso": "Laboratório"}),
        "filtros": topic({}, na=True, justification="Método sem leitura óptica"),
        "classificacao_risco": topic({"classe": "II", "regra": "Regra 5, item d"}),
        "requisitos_desempenho": topic({"requisitos": requirement_rows(applies)}),
        "requisitos_regulatorios": topic({"normas": [standard_id]}),
        "gerenciamento_risco": topic({"matriz": [], "descricao": "Matriz anexa ao projeto"}),
        "outros_dados": topic({"texto": "Metodologia enzimática"}),
    }


@pytest.fixture
def make_subdocument(analyst):
    from sgp.subdocuments import services
    from sgp.vocab.models import get_term

    def _make(project, code, by=None):
        return services.create_subdocument(
            project, get_term("tipo-subdocumento", code), by=by or analyst
        )

    return _make


@pytest.fixture
def approved_entry(project, analyst, manager, standard, make_subdocument, signing):
    from sgp.subdocuments import services

    entry = make_subdocument(project, "entrada")
    entry = services.save_subdocument(entry, by=analyst, data={"topics": entry_topics(standard.pk)})
    signing.submit_and_approve("subdocument", entry, analyst, manager)
    entry.refresh_from_db()
    return entry


@pytest.fixture
def approve_quick(manager):
    """Aprova pulando a completude (para preparar fluxo nos testes que não tratam dela)."""
    from django.utils import timezone

    from sgp.subdocuments.models import Subdocument, SubdocumentStatus

    def _approve(subdocument):
        Subdocument.objects.filter(pk=subdocument.pk).update(
            status=SubdocumentStatus.APPROVED, approved_by=manager, approved_at=timezone.now()
        )
        subdocument.refresh_from_db()
        return subdocument

    return _approve


TODAY = date(2026, 11, 7)
