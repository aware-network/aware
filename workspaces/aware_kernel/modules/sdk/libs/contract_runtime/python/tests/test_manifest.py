from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from aware_sdk_contract_runtime.manifest import (
    AwareSdkTomlSpec,
    SdkManifestMeaningCodecError,
    decode_sdk_manifest_meaning,
    encode_sdk_manifest_meaning,
    load_aware_sdk_toml_spec_from_text,
    parse_sdk_manifest_bytes,
)

REPO_ROOT = Path(__file__).resolve().parents[8]


def _v1_fixture() -> bytes:
    return b"""aware_sdk = 1
[sdk]
package_name = "example-sdk"
fqn_prefix = "example_sdk"
[build]
"""


def test_every_repository_sdk_manifest_has_one_parsed_meaning() -> None:
    paths = sorted(
        path
        for path in REPO_ROOT.glob("workspaces/**/aware.sdk.toml")
        if b"aware_sdk = " in path.read_bytes()
    )
    assert paths
    for path in paths:
        body = path.read_bytes()
        expected = load_aware_sdk_toml_spec_from_text(
            toml_text=body.decode("utf-8"), toml_path=path
        )
        parsed = parse_sdk_manifest_bytes(body, path_label=str(path))
        assert type(parsed) is AwareSdkTomlSpec
        assert parsed == expected, path
        encoded = encode_sdk_manifest_meaning(parsed)
        assert decode_sdk_manifest_meaning(encoded) == parsed
        assert (
            encode_sdk_manifest_meaning(decode_sdk_manifest_meaning(encoded)) == encoded
        )


def test_codec_refuses_copy_shape_and_noncanonical_bytes() -> None:
    path = next(
        path
        for path in REPO_ROOT.glob("workspaces/**/aware.sdk.toml")
        if b"aware_sdk = " in path.read_bytes()
    )
    parsed = parse_sdk_manifest_bytes(path.read_bytes())
    canonical = encode_sdk_manifest_meaning(parsed)
    with pytest.raises(SdkManifestMeaningCodecError, match="canonical"):
        decode_sdk_manifest_meaning(canonical + b" ")
    raw = json.loads(canonical)
    raw["meaning"]["aware_sdk"] = True
    with pytest.raises(SdkManifestMeaningCodecError, match="scalar"):
        decode_sdk_manifest_meaning(
            json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
        )
    with pytest.raises(SdkManifestMeaningCodecError, match="duplicate"):
        decode_sdk_manifest_meaning(b'{"format":"x","format":"x"}')


def test_v1_codec_shape_is_unchanged_and_feature_selection_is_rejected() -> None:
    v1 = parse_sdk_manifest_bytes(_v1_fixture())
    v1_body = encode_sdk_manifest_meaning(v1)
    assert json.loads(v1_body)["format"] == "aware.sdk.manifest.meaning.v1"
    assert "definition" not in json.loads(v1_body)["meaning"]
    assert "generation_profiles" not in json.loads(v1_body)["meaning"]
    assert v1.generation_profiles == []
    assert decode_sdk_manifest_meaning(v1_body) == v1

    with pytest.raises(ValueError, match="unexpected|Unknown|not allowed"):
        parse_sdk_manifest_bytes(
            _v1_fixture()
            + b'[definition]\nselected_operation_refs = ["example_sdk.alpha"]\n'
        )
    wrong_tag = json.loads(v1_body)
    wrong_tag["format"] = "aware.sdk.manifest.meaning.v2"
    with pytest.raises(SdkManifestMeaningCodecError, match="envelope"):
        decode_sdk_manifest_meaning(
            json.dumps(wrong_tag, sort_keys=True, separators=(",", ":")).encode()
        )


@pytest.mark.parametrize(
    "body, expected",
    [
        (
            _v1_fixture()
            + b'[definition]\nselected_operation_refs = ["example_sdk.alpha"]\n',
            "unexpected|Unknown|not allowed",
        ),
        (_v1_fixture().replace(b"aware_sdk = 1", b"aware_sdk = 2"), "expected 1"),
        (
            _v1_fixture().replace(b"aware_sdk = 1", b"aware_sdk = true"),
            "positive integer",
        ),
    ],
)
def test_manifest_rejects_feature_selection_and_invalid_versions(
    body: bytes, expected: str
) -> None:
    with pytest.raises(ValueError, match=expected):
        parse_sdk_manifest_bytes(body)


def test_legacy_model_and_loader_are_exact_aliases() -> None:
    legacy_root = (
        REPO_ROOT
        / "workspaces/aware_kernel/modules/sdk/ontology/runtime/python/aware_sdk_runtime/manifest"
    )

    def load_file(name: str) -> Any:
        module_spec = importlib.util.spec_from_file_location(
            f"test_legacy_sdk_{name}", legacy_root / f"{name}.py"
        )
        assert module_spec is not None and module_spec.loader is not None
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module

    legacy_spec = load_file("spec")
    legacy_loader = load_file("loader")
    assert legacy_spec.AwareSdkTomlSpec is AwareSdkTomlSpec
    path = next(
        path
        for path in REPO_ROOT.glob("workspaces/**/aware.sdk.toml")
        if b"aware_sdk = " in path.read_bytes()
    )
    assert legacy_loader.load_aware_sdk_toml_spec(
        toml_path=path
    ) == parse_sdk_manifest_bytes(path.read_bytes(), path_label=str(path))
