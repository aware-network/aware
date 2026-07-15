import pytest

from aware_utils.string_transform import normalize_identifier, singularize


def test_singularize_ses_suffix_preserves_e():
    assert singularize("service_responses") == "service_response"
    assert singularize("diseases") == "disease"
    assert singularize("processes") == "process"
    assert singularize("boxes") == "box"


def test_normalize_identifier_strips_whitespace():
    assert normalize_identifier("\n  FooBar \t") == "FooBar"
    assert normalize_identifier("(\n  FooBar  )") == "FooBar"
    assert normalize_identifier("Name") == "Name"
    assert normalize_identifier(42) == "42"
