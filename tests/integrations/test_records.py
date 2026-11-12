"""Registros do contrato: PDF oficial no registro do documento, lote citado em subdocumento
aprovado e números com vírgula decimal (convergência da 012: FR-004, FR-008)."""

import pytest

from sgp.integrations import services
from sgp.integrations.models import IntegrationMessage


@pytest.mark.req("012:FR-004")
@pytest.mark.req("012:SC-001")
def test_pdf_oficial_atualiza_o_mesmo_registro_do_documento(
    gateway, configured, approved_entry, analyst, it_admin, seal_cert, generate
):
    original = IntegrationMessage.objects.get(record_type="documento")
    assert original.payload["pdf_sha256"] == "" and original.target_key == original.idempotency_key
    first = generate("subdocument", approved_entry, "pdf", analyst).result
    assert first.official
    update = IntegrationMessage.objects.get(idempotency_key=f"{original.idempotency_key}:pdf")
    assert update.record_key == original.idempotency_key
    assert update.payload["pdf_sha256"] == first.file_hash
    assert update.payload["pdf_codigo_verificacao"] == first.verification_code
    generate("subdocument", approved_entry, "pdf", analyst)
    assert IntegrationMessage.objects.filter(record_type="documento").count() == 2
    services.dispatch(original.pk)
    services.dispatch(update.pk)
    stored = gateway.records["TESTE_DOCUMENTO"]
    assert list(stored) == [original.idempotency_key]
    assert stored[original.idempotency_key]["PDFHASH"] == first.file_hash
    assert stored[original.idempotency_key]["PDFCOD"] == first.verification_code
    _, _, raw = services.export("documento", "json", by=it_admin)
    import json

    rows = json.loads(raw)["registros"]
    assert [row["chave"] for row in rows] == [original.idempotency_key]
    assert rows[0]["pdf_sha256"] == first.file_hash


@pytest.mark.req("012:FR-004")
def test_lote_citado_em_subdocumento_aprovado_gera_registro(
    signed_project, create_sub, force_approve, member, manager, make_lot
):
    from sgp.audit.services import record_event

    lot = make_lot(signed_project, member, code="LP-INT-1")
    for code in ("entrada", "formulacao"):
        force_approve(create_sub(signed_project, code))
    pilot = create_sub(signed_project, "lote-piloto")
    force_approve(
        pilot,
        {
            "lote": {
                "na": False,
                "justification": "",
                "values": {"produto": "Produto fictício", "lotes": [lot.pk]},
            }
        },
    )
    record_event(
        "signatures.approved",
        actor=manager,
        object_type="signatures.subdocument",
        object_id=str(pilot.pk),
        object_repr=str(pilot),
        project_id=signed_project.pk,
    )
    message = IntegrationMessage.objects.get(record_type="lote")
    assert message.idempotency_key == f"lote:{lot.pk}:{lot.version}"
    payload = message.payload
    assert payload["codigo_lote"] == "LP-INT-1" and payload["codigo_projeto"] == signed_project.code
    assert payload["data_fabricacao"] == "2026-09-01" and payload["data_validade"] == "2027-09-01"
    assert payload["local"] == "Planta piloto" and payload["responsavel"]
    assert IntegrationMessage.objects.filter(record_type="documento", object_id=str(pilot.pk))


@pytest.mark.req("012:FR-008")
def test_resultado_de_estudo_com_virgula_decimal(signed_project, member, it_admin):
    from sgp.integrations import records
    from sgp.studies import services as studies
    from sgp.studies.models import Study
    from sgp.vocab.models import get_term

    study = studies.create_study(
        signed_project,
        by=member,
        data={"study_type": get_term("tipo-estudo", "repetibilidade"), "title": "Estudo fictício"},
    )
    Study.objects.filter(pk=study.pk).update(
        results={
            "criterios": [
                {
                    "rotulo": "CV",
                    "comparacao": "le",
                    "limite": "5.0",
                    "valor": "3.25",
                    "atendido": True,
                }
            ]
        }
    )
    study.refresh_from_db()
    kind, key, payload = records.study_result(study)
    assert payload["criterio"] == "CV ≤ 5,0"
    assert payload["resultado"] == "CV = 3,25" and payload["conclusao"] == "atendido"
    services.enqueue(kind, key, payload, project=signed_project, obj=study)
    _, _, data = services.export("resultado_estudo", "csv", by=it_admin)
    assert "CV = 3,25" in data.decode("utf-8")
