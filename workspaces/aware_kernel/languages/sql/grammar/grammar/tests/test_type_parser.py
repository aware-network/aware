"""Validation tests for SQL canonical TypeParser boundary (raw token SSOT)."""

from sql_grammar.type_parser import SqlTypeParser


def test_sql_parser_array_inner_extraction_all_syntaxes():
    p = SqlTypeParser()

    assert p.get_array_inner("TEXT[]") == "TEXT"
    assert p.get_array_inner("vector(512)[]") == "vector(512)"

    assert p.get_array_inner("ARRAY<INTEGER>") == "INTEGER"
    assert p.get_array_inner("array<boolean>") == "boolean"

    assert p.get_array_inner("ARRAY[TEXT]") == "TEXT"
    assert p.get_array_inner("ARRAY(TIMESTAMP WITH TIME ZONE)") == "TIMESTAMP WITH TIME ZONE"
    # Nested arrays (outer wrapper only)
    assert p.get_array_inner("TEXT[][]") == "TEXT[]"
    assert p.get_array_inner("ARRAY<INTEGER>[]") == "ARRAY<INTEGER>"
    assert p.get_array_inner("ARRAY(VECTOR(512))[]") == "ARRAY(VECTOR(512))"


def test_sql_parser_call_and_normalization():
    p = SqlTypeParser()

    assert p.get_call("vector(512)") == ("vector", "512")
    assert p.get_call("VECTOR ( 1536 )") == ("vector", "1536")
    assert p.get_call("timestamp(6)") == ("timestamp", "6")
    assert p.normalize_exact_token("VARCHAR(255)") == "varchar"
    assert p.normalize_exact_token("NUMERIC(precision, scale)") == "numeric"
    assert p.normalize_exact_token(' "TEXT" ') == "text"
    assert p.normalize_exact_token("DOUBLE   PRECISION") == "double precision"


def test_sql_parser_qualified_ident_detection():
    p = SqlTypeParser()
    assert p.is_qualified_ident("public.transaction_intent_status") is True
    assert p.is_qualified_ident('"public.transaction_intent_status"') is False
    assert p.is_qualified_ident("transaction_intent_status") is False
