"""Layout publicado não muda; vínculos, conteúdo congelado e documentos gerados são somente de
inclusão (data-model.md da feature 006)."""

from django.db import migrations

from sgp.core.db_triggers import immutable_trigger_sql

LAYOUT_FORWARD = """
CREATE OR REPLACE FUNCTION documents_forbid_published_layout_change() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Modelo de layout não é apagado (%).', OLD.id;
    END IF;
    IF OLD.status = 'published' AND (
        NEW.definition IS DISTINCT FROM OLD.definition
        OR NEW.version <> OLD.version
        OR NEW.valid_from <> OLD.valid_from
        OR NEW.target <> OLD.target
        OR NEW.status <> OLD.status
        OR NEW.logo_id IS DISTINCT FROM OLD.logo_id
    ) THEN
        RAISE EXCEPTION 'Modelo de layout publicado não pode ser alterado (%).', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER documents_layout_published_immutable
    BEFORE UPDATE OR DELETE ON documents_layouttemplate
    FOR EACH ROW EXECUTE FUNCTION documents_forbid_published_layout_change();
"""
LAYOUT_REVERSE = """
DROP TRIGGER IF EXISTS documents_layout_published_immutable ON documents_layouttemplate;
DROP FUNCTION IF EXISTS documents_forbid_published_layout_change();
"""

TABLES = (
    ("documents_layoutbinding", "documents_layoutbinding_immutable"),
    ("documents_frozenrendering", "documents_frozenrendering_immutable"),
    ("documents_generateddocument", "documents_generateddocument_immutable"),
)


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_initial"),
        ("core", "0001_forbid_change_function"),
    ]

    operations = [
        migrations.RunSQL(LAYOUT_FORWARD, reverse_sql=LAYOUT_REVERSE),
        *[migrations.RunSQL(*immutable_trigger_sql(table, trigger)) for table, trigger in TABLES],
    ]
