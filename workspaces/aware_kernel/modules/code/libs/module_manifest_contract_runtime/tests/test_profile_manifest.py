"""Profile extraction parity and strict full-meaning codec proofs."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_module_manifest_contract_runtime.parser import AwareModuleTomlError
from aware_code_module_manifest_contract_runtime.profile_codec import (
    decode_profile_manifest,
    encode_profile_manifest,
)
from aware_code_module_manifest_contract_runtime.profile_parser import (
    parse_profile_manifest,
)

SOURCE = b"""aware_semantic_contract_profile = 1
[profile]
key = " custom.profile "
package_key = "different.package"
[[providers]]
module_id = " code "
provider_key = " aware_code "
[[providers]]
module_id = "api"
provider_key = "aware_api"
required = false
status = "inactive"
"""


def test_complete_meaning_and_order():
    value = parse_profile_manifest(SOURCE)
    assert value.profile.key == "custom.profile"
    assert value.profile.package_key == "different.package"
    assert value.profile.runtime_import_mode == "dynamic_contract_module"
    assert value.profile.runtime_import_required is True
    assert value.profile.status == "active"
    assert [
        (p.module_id, p.provider_key, p.required, p.status) for p in value.providers
    ] == [
        ("code", "aware_code", True, "active"),
        ("api", "aware_api", False, "inactive"),
    ]
    assert decode_profile_manifest(encode_profile_manifest(value)) == value


@pytest.mark.parametrize("version", [b"1", b"true"])
def test_version_quirk_preserved(version):
    value = parse_profile_manifest(SOURCE.replace(b"= 1", b"= " + version, 1))
    restored = decode_profile_manifest(encode_profile_manifest(value))
    assert type(restored.aware_semantic_contract_profile) is (
        bool if version == b"true" else int
    )


@pytest.mark.parametrize("version", [b"false", b"2", b"1.0", b'"1"'])
def test_invalid_versions(version):
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(SOURCE.replace(b"= 1", b"= " + version, 1))


@pytest.mark.parametrize(
    "body",
    [
        SOURCE.replace(b'"aware_api"', b'"aware_code"'),
        SOURCE.replace(b'" code "', b'"Code"'),
        SOURCE.replace(b"required = false", b"required = 0"),
        SOURCE.replace(b"[profile]", b"unknown = 1\n[profile]"),
        SOURCE.replace(b'package_key = "different.package"', b""),
        b'aware_semantic_contract_profile = 1\nproviders = []\n[profile]\nkey="p"\npackage_key="p"',
        b"not TOML",
    ],
)
def test_invalid_grammar(body):
    with pytest.raises(AwareModuleTomlError):
        parse_profile_manifest(body)


@pytest.mark.parametrize("newline", [b"\r", b"\r\n", b"\n"])
def test_filesystem_newline_parity(newline):
    assert parse_profile_manifest(
        SOURCE.replace(b"\n", newline)
    ) == parse_profile_manifest(SOURCE)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "extra",
        "null",
        "wrong_bool",
        "duplicate",
        "whitespace",
        "order",
        "version_float",
    ],
)
def test_strict_codec(mutation):
    body = encode_profile_manifest(parse_profile_manifest(SOURCE))
    raw = json.loads(body)
    if mutation == "missing":
        del raw["profile"]["status"]
    elif mutation == "extra":
        raw["extra"] = 1
    elif mutation == "null":
        raw["profile"]["runtime_import_required"] = None
    elif mutation == "wrong_bool":
        raw["providers"][0]["required"] = 1
    elif mutation == "version_float":
        raw["aware_semantic_contract_profile"] = 1.0
    elif mutation == "duplicate":
        body = body.replace(b'{"', b'{"contract":"duplicate","', 1)
    elif mutation == "whitespace":
        body += b"\n"
    elif mutation == "order":
        body = json.dumps(raw).encode()
    if mutation not in {"duplicate", "whitespace", "order"}:
        body = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ValueError):
        decode_profile_manifest(body)


def test_encode_rejects_noncanonical_model():
    model = parse_profile_manifest(SOURCE)
    with pytest.raises(ValueError):
        encode_profile_manifest(
            replace(model, profile=replace(model.profile, key=" padded "))
        )


def test_comment_only_source_changes_preserve_meaning():
    assert encode_profile_manifest(
        parse_profile_manifest(SOURCE)
    ) == encode_profile_manifest(parse_profile_manifest(b"# changed source\n" + SOURCE))


def test_repository_profiles():
    root = next(
        p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
    )
    paths = sorted(
        (root / "workspaces").glob(
            "*/semantic_contract/profiles/*/aware.semantic_contract_profile.toml"
        )
    )
    assert paths
    for path in paths:
        model = parse_profile_manifest(path.read_bytes(), source_label=str(path))
        assert decode_profile_manifest(encode_profile_manifest(model)) == model
