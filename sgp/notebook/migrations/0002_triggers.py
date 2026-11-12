"""Entrada assinada não muda; materiais e anexos só mudam com a entrada aberta; adendos e
assinaturas são somente de inclusão (research R5 da feature 008)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

ENTRY_FORWARD = """
CREATE OR REPLACE FUNCTION notebook_forbid_locked_entry_change() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Entrada do caderno não é apagada (%).', OLD.id;
    END IF;
    IF OLD.status <> 'open' AND (
        NEW.project_id IS DISTINCT FROM OLD.project_id
        OR NEW.number IS DISTINCT FROM OLD.number
        OR NEW.author_id IS DISTINCT FROM OLD.author_id
        OR NEW.created_at IS DISTINCT FROM OLD.created_at
        OR NEW.title IS DISTINCT FROM OLD.title
        OR NEW.objective IS DISTINCT FROM OLD.objective
        OR NEW.hypothesis IS DISTINCT FROM OLD.hypothesis
        OR NEW.procedure IS DISTINCT FROM OLD.procedure
        OR NEW.results IS DISTINCT FROM OLD.results
        OR NEW.conclusion IS DISTINCT FROM OLD.conclusion
        OR NEW.template_id IS DISTINCT FROM OLD.template_id
        OR NEW.search_text IS DISTINCT FROM OLD.search_text
        OR NEW.signed_at IS DISTINCT FROM OLD.signed_at
        OR NEW.status = 'open'
    ) THEN
        RAISE EXCEPTION 'Entrada do caderno assinada não pode ser alterada (%).', OLD.id;
    END IF;
    IF OLD.status = 'witnessed' AND (
        NEW.status <> 'witnessed'
        OR NEW.witnessed_at IS DISTINCT FROM OLD.witnessed_at
        OR NEW.relevant IS DISTINCT FROM OLD.relevant
    ) THEN
        RAISE EXCEPTION 'Entrada do caderno testemunhada não pode ser alterada (%).', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER notebook_entry_locked
    BEFORE UPDATE OR DELETE ON notebook_notebookentry
    FOR EACH ROW EXECUTE FUNCTION notebook_forbid_locked_entry_change();

CREATE OR REPLACE FUNCTION notebook_forbid_closed_entry_items() RETURNS trigger AS $$
DECLARE
    entry_status varchar;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Material ou anexo do caderno não é apagado (%).', OLD.id;
    END IF;
    SELECT status INTO entry_status FROM notebook_notebookentry WHERE id = NEW.entry_id;
    IF entry_status IS DISTINCT FROM 'open' THEN
        RAISE EXCEPTION 'Entrada do caderno assinada não recebe nem perde materiais e anexos (%).',
            NEW.entry_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER notebook_material_entry_open
    BEFORE INSERT OR UPDATE OR DELETE ON notebook_entrymaterial
    FOR EACH ROW EXECUTE FUNCTION notebook_forbid_closed_entry_items();
CREATE TRIGGER notebook_attachment_entry_open
    BEFORE INSERT OR UPDATE OR DELETE ON notebook_entryattachment
    FOR EACH ROW EXECUTE FUNCTION notebook_forbid_closed_entry_items();
"""
ENTRY_REVERSE = """
DROP TRIGGER IF EXISTS notebook_attachment_entry_open ON notebook_entryattachment;
DROP TRIGGER IF EXISTS notebook_material_entry_open ON notebook_entrymaterial;
DROP FUNCTION IF EXISTS notebook_forbid_closed_entry_items();
DROP TRIGGER IF EXISTS notebook_entry_locked ON notebook_notebookentry;
DROP FUNCTION IF EXISTS notebook_forbid_locked_entry_change();
"""

TABLES = (
    ("notebook_addendum", "notebook_addendum_immutable"),
    ("notebook_notebooksignature", "notebook_signature_immutable"),
)


class Migration(migrations.Migration):
    dependencies = [
        ("notebook", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(ENTRY_FORWARD, reverse_sql=ENTRY_REVERSE),
        *[migrations.RunSQL(*immutable_trigger_sql(table, trigger)) for table, trigger in TABLES],
    ]
