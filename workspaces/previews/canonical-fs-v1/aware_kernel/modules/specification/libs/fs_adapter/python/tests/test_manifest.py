from __future__ import annotations

import tomllib

import pytest
from aware_specification_fs_adapter.manifest import ManifestError, parse_manifest
from jsonschema import Draft202012Validator


def test_manifest_parses_canonical_fixture(canonical_tree, schema_bytes: bytes) -> None:
    root, spec_root = canonical_tree
    schema = tomllib.loads("value = 1")
    assert schema == {"value": 1}
    import json

    validator = Draft202012Validator(json.loads(schema_bytes))
    parsed = parse_manifest(
        (root / spec_root / "aware.spec.toml").read_text(), validator
    )
    assert parsed.specification["key"] == "example.spec"


def test_raw_dotted_key_rejects() -> None:
    with pytest.raises(ManifestError):
        parse_manifest("aware.value = 1\n")


@pytest.mark.parametrize(
    "source",
    [
        "[specification.alias]\nvalue = 1\n",
        '["specification".alias]\nvalue = 1\n',
        '"aware".value = 1\n',
    ],
)
def test_all_raw_dotted_key_forms_reject(source: str) -> None:
    with pytest.raises(ManifestError):
        parse_manifest(source)
