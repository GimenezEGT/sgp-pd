"""Modelo publicado não muda (FR-004 da feature 004): gatilho contra UPDATE do conteúdo."""

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION formtemplates_forbid_published_change() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Modelo de formulário não é apagado (%).', OLD.id;
    END IF;
    IF OLD.status = 'published' AND (
        NEW.definition IS DISTINCT FROM OLD.definition
        OR NEW.form_version <> OLD.form_version
        OR NEW.reference <> OLD.reference
        OR NEW.valid_from <> OLD.valid_from
        OR NEW.subdocument_type_id <> OLD.subdocument_type_id
        OR NEW.status <> OLD.status
    ) THEN
        RAISE EXCEPTION 'Modelo de formulário publicado não pode ser alterado (%).', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER formtemplates_published_immutable
    BEFORE UPDATE OR DELETE ON formtemplates_formtemplate
    FOR EACH ROW EXECUTE FUNCTION formtemplates_forbid_published_change();
"""
REVERSE = """
DROP TRIGGER IF EXISTS formtemplates_published_immutable ON formtemplates_formtemplate;
DROP FUNCTION IF EXISTS formtemplates_forbid_published_change();
"""


class Migration(migrations.Migration):
    dependencies = [("formtemplates", "0001_initial")]

    operations = [migrations.RunSQL(FORWARD, reverse_sql=REVERSE)]
