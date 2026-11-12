"""Saída, Alteração e versões de modelo (US2, US6, US7: FR-004, FR-007, FR-011, FR-020, FR-021)."""

import pytest
from django.core.exceptions import ValidationError

from sgp.accounts.profiles import Profile
from sgp.formtemplates import services as template_services
from sgp.projects.models import Project
from sgp.subdocuments import numbering, services
from sgp.subdocuments.models import Subdocument
from sgp.vocab.models import get_term

pytestmark = [pytest.mark.django_db]


def chain(project, make_subdocument, approve_quick, until):
    for code in (
        "formulacao",
        "lote-piloto",
        "rapd",
        "analise-critica",
        "validacao",
        "verificacao-final",
    ):
        if code == until:
            break
        approve_quick(make_subdocument(project, code))


@pytest.mark.req("004:FR-020")
@pytest.mark.req("004:FR-011")
def test_itens_mapa_so_em_projeto_mapa(project, approved_entry, make_subdocument, approve_quick):
    chain(project, make_subdocument, approve_quick, None)
    exit_doc = make_subdocument(project, "saida")
    keys = [topic["key"] for _, topic in numbering.visible_topics(exit_doc)]
    assert "lotes_piloto_producao" not in keys and len(keys) == 10
    assert not any("MAPA" in item for item in services.completeness(exit_doc))
    Project.objects.filter(pk=project.pk).update(regulatory_body="MAPA")
    exit_doc.refresh_from_db()
    keys = [topic["key"] for _, topic in numbering.visible_topics(exit_doc)]
    assert "lotes_piloto_producao" in keys and len(keys) == 12


@pytest.mark.req("004:FR-020")
def test_setores_e_insumos_novos(
    project, approved_entry, make_subdocument, approve_quick, analyst, make_material
):
    chain(project, make_subdocument, approve_quick, None)
    exit_doc = make_subdocument(project, "saida")
    old = make_material(analyst, code="MP-VELHO", new_to_company=False)
    new = make_material(analyst, code="MP-NOVO", new_to_company=True)
    with pytest.raises(ValidationError, match="não pode ser escolhido"):
        services.save_subdocument(
            exit_doc,
            by=analyst,
            data={
                "topics": {
                    "novas_materias_primas": {
                        "na": False,
                        "justification": "",
                        "values": {"insumos": [old.pk]},
                    }
                }
            },
        )
    with pytest.raises(ValidationError, match="opção inválida"):
        services.save_subdocument(
            exit_doc,
            by=analyst,
            data={
                "topics": {
                    "setores": {
                        "na": False,
                        "justification": "",
                        "values": {"setores": ["financeiro"]},
                    }
                }
            },
        )
    saved = services.save_subdocument(
        exit_doc,
        by=analyst,
        data={
            "topics": {
                "novas_materias_primas": {
                    "na": False,
                    "justification": "",
                    "values": {"insumos": [new.pk]},
                },
                "setores": {
                    "na": False,
                    "justification": "",
                    "values": {"setores": ["producao-i", "sac"]},
                },
            }
        },
    )
    assert saved.topic_data("setores")["values"]["setores"] == ["producao-i", "sac"]


@pytest.mark.req("004:FR-021")
def test_alteracao_sobe_a_versao_e_marca_para_revisao(
    project, approved_entry, make_subdocument, approve_quick, analyst, manager, events, signing
):
    formulation = approve_quick(make_subdocument(project, "formulacao"))
    change = make_subdocument(project, "alteracao")
    assert (change.changed_version, change.new_version) == (1, 2)
    topics = {
        "justificativa": {"na": False, "justification": "", "values": {"texto": "Troca do tampão"}},
        "requisitos_entrada": {
            "na": False,
            "justification": "",
            "values": {"afetados": ["armazenamento"], "novo_conteudo": "2 a 30 °C"},
        },
        "analise_risco": {"na": False, "justification": "", "values": {"texto": "", "anexos": []}},
        "subdocumentos_afetados": {
            "na": False,
            "justification": "",
            "values": {"subdocumentos": [formulation.pk]},
        },
    }
    change = services.save_subdocument(change, by=analyst, data={"topics": topics})
    with pytest.raises(ValidationError, match="preencha Avaliação de risco ou Anexos"):
        signing.submit("subdocument", change, analyst)
    topics["analise_risco"]["values"]["texto"] = "Risco baixo; estabilidade a confirmar"
    change = services.save_subdocument(change, by=analyst, data={"topics": topics})
    signing.submit_and_approve("subdocument", change, analyst, manager)
    project.refresh_from_db()
    assert project.version == 2
    version_event = events("projects.version_changed")[-1]
    assert version_event.old_value == {"versao": "01"} and version_event.new_value == {
        "versao": "02"
    }
    formulation.refresh_from_db()
    approved_entry.refresh_from_db()
    assert (
        formulation.review_requested_by == change and approved_entry.review_requested_by == change
    )
    assert len(events("subdocuments.review_requested")) == 2


@pytest.mark.req("004:FR-021")
def test_alteracao_so_aceita_topicos_da_entrada(project, approved_entry, make_subdocument, analyst):
    change = make_subdocument(project, "alteracao")
    with pytest.raises(ValidationError, match="tópicos inexistentes"):
        services.save_subdocument(
            change,
            by=analyst,
            data={
                "topics": {
                    "requisitos_entrada": {
                        "na": False,
                        "justification": "",
                        "values": {"afetados": ["inventado"]},
                    }
                }
            },
        )


@pytest.mark.req("004:FR-007")
@pytest.mark.req("004:SC-002")
def test_nova_versao_do_modelo_nao_altera_documento_iniciado(
    project, approved_entry, make_subdocument, analyst, make_user
):
    quality = make_user(None, Profile.QUALITY)
    formulation_type = get_term("tipo-subdocumento", "formulacao")
    started = make_subdocument(project, "formulacao")
    data_before = started.data
    draft = template_services.create_draft(formulation_type, by=quality)
    definition = dict(draft.definition)
    definition["topics"] = [
        dict(draft.topics[0], label="Nome do Produto (revisado)")
    ] + draft.topics[1:]
    template_services.update_draft(draft, by=quality, data={}, definition=definition)
    template_services.publish(draft, by=quality)
    started.refresh_from_db()
    assert started.template.form_version == 5 and started.data == data_before
    assert numbering.visible_topics(started)[0][1]["label"] == "Nome do Produto"
    other = make_user(None, Profile.PROJECT_LEADER)
    assert template_services.current_template(formulation_type).form_version == 6
    assert other.pk


@pytest.mark.req("004:FR-007")
def test_migracao_pelo_gestor(
    project, approved_entry, make_subdocument, analyst, manager, make_user, events
):
    quality = make_user(None, Profile.QUALITY)
    formulation_type = get_term("tipo-subdocumento", "formulacao")
    started = make_subdocument(project, "formulacao")
    services.save_subdocument(
        started,
        by=analyst,
        data={
            "topics": {
                "complementares": {
                    "na": False,
                    "justification": "",
                    "values": {"texto": "Texto que vai sumir"},
                }
            }
        },
    )
    draft = template_services.create_draft(formulation_type, by=quality)
    definition = dict(draft.definition)
    definition["topics"] = [topic for topic in draft.topics if topic["key"] != "complementares"]
    template_services.update_draft(draft, by=quality, data={}, definition=definition)
    template_services.publish(draft, by=quality)
    with pytest.raises(ValidationError, match="Só o Gestor"):
        services.migrate_template(started, by=analyst, reason="x")
    with pytest.raises(ValidationError, match="motivo"):
        services.migrate_template(started, by=manager, reason="")
    migrated = services.migrate_template(started, by=manager, reason="Formulário 06 vigente")
    assert migrated.template.form_version == 6
    assert (
        migrated.unmapped_data["05"]["complementares"]["values"]["texto"] == "Texto que vai sumir"
    )
    assert events("subdocuments.template_migrated")[-1].reason == "Formulário 06 vigente"
    approved_entry_doc = Subdocument.objects.get(pk=approved_entry.pk)
    with pytest.raises(ValidationError):
        services.migrate_template(approved_entry_doc, by=manager, reason="x")


@pytest.mark.req("004:FR-004")
def test_vigencia_futura(make_user):
    from datetime import timedelta

    from django.utils import timezone

    quality = make_user(None, Profile.QUALITY)
    rapd = get_term("tipo-subdocumento", "rapd")
    draft = template_services.create_draft(rapd, by=quality)
    template_services.update_draft(
        draft,
        by=quality,
        data={"valid_from": timezone.localdate() + timedelta(days=30)},
        definition=draft.definition,
    )
    template_services.publish(draft, by=quality)
    assert template_services.current_template(rapd).form_version == 5
    future = timezone.localdate() + timedelta(days=31)
    assert template_services.current_template(rapd, on=future).form_version == 6
