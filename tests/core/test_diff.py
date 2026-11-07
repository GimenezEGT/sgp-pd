from sgp.core.diff import changed_fields


def test_so_campos_alterados_entram_no_evento():
    old, new = changed_fields(
        {"a": 1, "b": "x", "c": [1]}, {"a": 1, "b": "y", "c": [1, 2], "d": None}
    )
    assert old == {"b": "x", "c": [1]}
    assert new == {"b": "y", "c": [1, 2]}


def test_sem_mudanca_retorna_vazio():
    assert changed_fields({"a": 1}, {"a": 1}) == ({}, {})
