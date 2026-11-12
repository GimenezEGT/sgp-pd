"""Assinatura, bloqueio, adendos, prazo e testemunha (FR-006 a FR-009, SC-001)."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connection, transaction
from django.urls import reverse
from django.utils import timezone

from sgp.core.models import ImmutableRecordError
from sgp.notebook import search, services
from sgp.notebook.content import entry_hash
from sgp.notebook.models import EntryMaterial, EntryStatus, NotebookEntry, SignatureRole

from .conftest import png_file


@pytest.mark.req("008:FR-006")
def test_assinatura_com_reautenticacao_e_resumo(make_entry, analyst, colleague, signing, events):
    entry = make_entry()
    signing.enable(analyst, colleague)
    with pytest.raises(ValidationError, match="incorreta"):
        services.sign_entry(entry, by=analyst, password="errada")
    assert len(events("signatures.failed")) == 1
    with pytest.raises(PermissionDenied):
        services.sign_entry(entry, by=colleague, password=signing.password)
    signature = services.sign_entry(entry, by=analyst, password=signing.password)
    entry.refresh_from_db()
    assert entry.status == EntryStatus.SIGNED and entry.signed_at
    assert signature.role == SignatureRole.AUTHOR and signature.content_hash == entry_hash(entry)
    assert events("notebook.signed")[-1].new_value["resumo"] == signature.content_hash


@pytest.mark.req("008:FR-007")
@pytest.mark.req("008:SC-001")
def test_entrada_assinada_nao_muda_no_servico_nem_no_banco(
    signed_entry, analyst, project, make_lot
):
    entry = signed_entry()
    lot = make_lot(project, analyst, code="L-BLOQ")
    with pytest.raises(PermissionDenied):
        services.update_entry(entry, by=analyst, data={"conclusion": "Mudou"})
    with pytest.raises(PermissionDenied):
        services.add_material(entry, by=analyst, kind="lot", code="L-BLOQ")
    with pytest.raises(PermissionDenied):
        services.add_attachment(entry, by=analyst, uploaded=png_file())
    with pytest.raises(DatabaseError), transaction.atomic():
        NotebookEntry.objects.filter(pk=entry.pk).update(conclusion="Adulterado")
    with pytest.raises(DatabaseError), transaction.atomic():
        NotebookEntry.objects.filter(pk=entry.pk).update(status=EntryStatus.OPEN)
    with pytest.raises(DatabaseError), transaction.atomic():
        EntryMaterial.objects.create(
            entry=entry, kind="lot", lot=lot, code=lot.code, version=lot.version, added_by=analyst
        )
    entry.refresh_from_db()
    assert entry.conclusion == "<p>Ok</p>"


@pytest.mark.req("008:FR-007")
@pytest.mark.req("008:SC-001")
def test_adendo_assinado_e_imutavel_sem_mudar_o_original(
    signed_entry, analyst, colleague, signing, make_entry, events
):
    entry = signed_entry()
    original = entry_hash(entry)
    with pytest.raises(ValidationError, match="texto do adendo"):
        services.add_addendum(entry, by=analyst, text="  ", password=signing.password)
    signing.enable(colleague)
    first = services.add_addendum(
        entry, by=analyst, text="Corrigido: pH 7,2", password=signing.password
    )
    second = services.add_addendum(
        entry, by=colleague, text="<p>Complemento do colega</p>", password=signing.password
    )
    assert (first.number, second.number) == (1, 2)
    assert first.signatures.get().content_hash == first.content_hash
    assert entry_hash(NotebookEntry.objects.get(pk=entry.pk)) == original
    assert services.verify(entry)["entry_ok"] and services.verify(entry)["addenda_ok"]
    first.text = "Outro"
    with pytest.raises(ImmutableRecordError):
        first.save()
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("UPDATE notebook_addendum SET text = 'x' WHERE id = %s", [first.pk])
    with pytest.raises(PermissionDenied):
        services.add_addendum(make_entry(), by=analyst, text="Aberta", password=signing.password)
    assert len(events("notebook.addendum_added")) == 2


@pytest.mark.req("008:FR-008")
def test_entrada_aberta_alem_do_prazo_aparece_atrasada(make_entry, settings):
    entry = make_entry()
    assert search.situation(entry) == "open"
    NotebookEntry.objects.filter(pk=entry.pk).update(created_at=timezone.now() - timedelta(days=8))
    entry.refresh_from_db()
    assert search.situation(entry) == "overdue"
    settings.NOTEBOOK_SIGN_DAYS = 10
    assert search.situation(entry) == "open"


@pytest.mark.req("008:FR-009")
def test_testemunha_diferente_do_autor_com_acesso(
    signed_entry, analyst, leader, outsider, quality, signing, events
):
    entry = signed_entry(relevant=True)
    assert search.situation(entry) == "awaiting_witness"
    signing.enable(leader, outsider, quality, analyst)
    with pytest.raises(PermissionDenied, match="autor"):
        services.witness_entry(entry, by=analyst, password=signing.password)
    with pytest.raises(PermissionDenied, match="acesso"):
        services.witness_entry(entry, by=outsider, password=signing.password)
    signature = services.witness_entry(entry, by=leader, password=signing.password)
    entry.refresh_from_db()
    assert entry.status == EntryStatus.WITNESSED and signature.content_hash == entry_hash(entry)
    assert search.situation(entry) == "witnessed"
    assert len(events("notebook.witnessed")) == 1
    with pytest.raises(PermissionDenied):
        services.witness_entry(entry, by=quality, password=signing.password)
    plain = signed_entry(relevant=False)
    with pytest.raises(PermissionDenied, match="relevante"):
        services.witness_entry(plain, by=leader, password=signing.password)


@pytest.mark.req("008:FR-009")
def test_relevancia_pelo_autor_ou_gestor_ate_a_testemunha(
    signed_entry, make_entry, analyst, colleague, manager, leader, signing, events
):
    entry = make_entry()
    services.set_relevance(entry, by=analyst, relevant=True)
    with pytest.raises(PermissionDenied):
        services.set_relevance(entry, by=colleague, relevant=False)
    signed = signed_entry(relevant=False)
    services.set_relevance(signed, by=manager, relevant=True)
    signed.refresh_from_db()
    assert signed.relevant and signed.relevant_by == manager
    signing.enable(leader)
    services.witness_entry(signed, by=leader, password=signing.password)
    signed.refresh_from_db()
    with pytest.raises(PermissionDenied):
        services.set_relevance(signed, by=manager, relevant=False)
    assert len(events("notebook.relevance_changed")) == 2


@pytest.mark.req("008:FR-009")
def test_conteudo_adulterado_bloqueia_a_testemunha(signed_entry, leader, signing, events):
    entry = signed_entry(relevant=True)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE notebook_notebookentry DISABLE TRIGGER notebook_entry_locked")
        cursor.execute(
            "UPDATE notebook_notebookentry SET conclusion = 'adulterado' WHERE id = %s", [entry.pk]
        )
        cursor.execute("ALTER TABLE notebook_notebookentry ENABLE TRIGGER notebook_entry_locked")
    entry.refresh_from_db()
    assert not services.verify(entry)["entry_ok"]
    signing.enable(leader)
    with pytest.raises(ValidationError, match="não confere"):
        services.witness_entry(entry, by=leader, password=signing.password)
    assert len(events("notebook.integrity_failed")) == 1
    entry.refresh_from_db()
    assert entry.status == EntryStatus.SIGNED


@pytest.mark.req("008:FR-006")
def test_telas_de_assinar_testemunhar_e_adendo(
    client, signed_entry, make_entry, analyst, leader, signing
):
    signing.enable(analyst, leader)
    entry = make_entry(relevant=True)
    client.force_login(analyst)
    client.post(reverse("notebook:sign", args=[entry.pk]), {"senha": signing.password})
    entry.refresh_from_db()
    assert entry.status == EntryStatus.SIGNED
    client.post(
        reverse("notebook:addendum_add", args=[entry.pk]),
        {"texto": "Correção pela tela", "senha": signing.password},
    )
    assert entry.addenda.count() == 1
    client.force_login(leader)
    page = client.get(reverse("notebook:detail", args=[entry.pk])).content.decode()
    assert "Assinar como testemunha" in page and "Correção pela tela" in page
    client.post(reverse("notebook:witness", args=[entry.pk]), {"senha": signing.password})
    entry.refresh_from_db()
    assert entry.status == EntryStatus.WITNESSED
