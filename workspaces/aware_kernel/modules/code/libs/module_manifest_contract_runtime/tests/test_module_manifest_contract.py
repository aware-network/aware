import json
from dataclasses import FrozenInstanceError

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModuleTomlError,
    ModuleManifestMeaningError,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
)

SOURCE = b'aware=1\n[[packages]]\nid="hello"\nkind="code"\nmanifest="./libs//pyproject.toml"\n'


def test_complete_defaults_and_legacy_path_normalization():
    value = parse_module_manifest(SOURCE)
    assert value.aware == 1
    assert value.packages[0].manifest == "./libs//pyproject.toml"
    assert value.packages[0].visibility == "module"
    assert value.stable_ids_parity_policy == "warn"
    assert value.runtime is None
    assert decode_module_manifest_meaning(encode_module_manifest_meaning(value)) == value
    with pytest.raises(FrozenInstanceError):
        value.aware = 2


def test_boolean_aware_quirk_preserved_losslessly():
    value = parse_module_manifest(SOURCE.replace(b"aware=1", b"aware=true"))
    assert value.aware is True
    assert decode_module_manifest_meaning(encode_module_manifest_meaning(value)).aware is True


@pytest.mark.parametrize("body", [b"", b"aware=2\npackages=[]", b"aware=1\npackages=[]", b"aware=1\nunknown=0\npackages=[]", b"aware=1\naware=1", b"\xff"])
def test_invalid_source_refuses(body):
    with pytest.raises(AwareModuleTomlError):
        parse_module_manifest(body)


def test_diagnostic_label_does_not_change_meaning():
    assert parse_module_manifest(SOURCE, source_label="a") == parse_module_manifest(SOURCE, source_label="b")


@pytest.mark.parametrize("change", ["extra", "missing", "wrong_type", "nested_extra", "contract"])
def test_full_codec_rejects_foreign_meaning(change):
    raw = json.loads(encode_module_manifest_meaning(parse_module_manifest(SOURCE)))
    if change == "extra":
        raw["meaning"]["unknown"] = 1
    elif change == "missing":
        del raw["meaning"]["plugins"]
    elif change == "wrong_type":
        raw["meaning"]["packages"][0]["mirrors_ontology"] = 1
    elif change == "nested_extra":
        raw["meaning"]["packages"][0]["unknown"] = False
    else:
        raw["contract"] = "other"
    body = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ModuleManifestMeaningError):
        decode_module_manifest_meaning(body)


def test_noncanonical_and_duplicate_json_refuse():
    body = encode_module_manifest_meaning(parse_module_manifest(SOURCE))
    for candidate in (body + b"\n", body.replace(b'{', b'{"contract":"duplicate",', 1)):
        with pytest.raises(ModuleManifestMeaningError):
            decode_module_manifest_meaning(candidate)


def test_crlf_parity():
    assert parse_module_manifest(SOURCE) == parse_module_manifest(SOURCE.replace(b"\n", b"\r\n"))
