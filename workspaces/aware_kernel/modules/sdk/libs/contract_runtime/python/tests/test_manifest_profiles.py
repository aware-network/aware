"""Authored profile carriage is not selected-definition or render authority."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from aware_sdk_contract_runtime.manifest import (
    AwareSdkTomlError,
    AwareSdkTomlGenerationProfileSpec,
    SdkManifestMeaningCodecError,
    decode_sdk_manifest_meaning,
    encode_sdk_manifest_meaning,
    parse_sdk_manifest_bytes,
)

MANIFEST = """aware_sdk = 1
[sdk]
package_name = "profile-probe"
fqn_prefix = "probe"
[build]
sources_dir = "."
include_paths = ["*.aware"]
compilation_mode = "sdk_ontology"
[targets.python]
root_dir = "python"
[targets.python.public_package]
package_dir = "probe"
[targets.dart]
root_dir = "dart"
[targets.dart.public_package]
package_dir = "probe"
"""
TABLES = """
[generation_profiles.legacy]
renderer_version = "aware.sdk.target-renderer.v6"
operations = ["probe.legacy"]
python_generated_dir = "python/probe/_generated"
dart_generated_dir = "dart/probe/lib/src/generated"
materialized_dir = "materialized"
[generation_profiles.reads]
renderer_version = "aware.sdk.target-renderer.v7"
operations = ["probe.observe"]
python_generated_dir = "python/probe/_read_generated"
dart_generated_dir = "dart/probe/lib/src/generated/read_v1"
materialized_dir = "materialized/read_v1"
"""


def profiled():
    return parse_sdk_manifest_bytes((MANIFEST + TABLES).encode())


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def test_original_reader_retains_every_exact_profile_and_canonical_codec():
    spec = profiled()
    assert [p.name for p in spec.generation_profiles] == ["legacy", "reads"]
    legacy, reads = spec.generation_profiles
    assert type(legacy) is AwareSdkTomlGenerationProfileSpec
    assert legacy.operations == ["probe.legacy"]
    assert reads.operations == ["probe.observe"]
    assert reads.renderer_version == "aware.sdk.target-renderer.v7"
    assert reads.materialized_dir == "materialized/read_v1"
    wire = encode_sdk_manifest_meaning(spec)
    assert json.loads(wire)["format"] == "aware.sdk.manifest.meaning.profiled.v1"
    assert decode_sdk_manifest_meaning(wire) == spec
    assert encode_sdk_manifest_meaning(decode_sdk_manifest_meaning(wire)) == wire
    before, after = TABLES.split("[generation_profiles.reads]")
    reordered = "[generation_profiles.reads]" + after + before
    assert parse_sdk_manifest_bytes((MANIFEST + reordered).encode()) == spec


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("[generation_profiles.legacy]", "[generation_profiles.BAD]"),
        ("aware.sdk.target-renderer.v7", "aware.sdk.target-renderer.v8"),
        ('operations = ["probe.observe"]', "operations = []"),
        ('operations = ["probe.observe"]', "operations = [true]"),
        ('operations = ["probe.observe"]', 'operations = "probe.observe"'),
        ('operations = ["probe.observe"]', 'operations = ["unqualified"]'),
        (
            'operations = ["probe.observe"]',
            'operations = ["probe.observe", "probe.observe"]',
        ),
        ('operations = ["probe.observe"]', 'operations = ["probe.z", "probe.a"]'),
        ('operations = ["probe.observe"]', 'operations = ["foreign.observe"]'),
        ('operations = ["probe.observe"]', 'operations = ["probe.legacy"]'),
        ("python/probe/_read_generated", "/python/probe/_read_generated"),
        ("python/probe/_read_generated", "python/probe/../_read_generated"),
        ("python/probe/_read_generated", "python/foreign/_read_generated"),
        ("python/probe/_read_generated", "python/probe/ padded"),
        ("dart/probe/lib/src/generated/read_v1", "dart/probe/generated"),
        ("materialized/read_v1", "unowned/read_v1"),
        ("materialized/read_v1", "materialized"),
        ("python/probe/_read_generated", "python/probe/_generated"),
        (
            "python/probe/_read_generated",
            "python/probe/_generated/sdk_contract.py/child",
        ),
        (
            'renderer_version = "aware.sdk.target-renderer.v7"',
            'unknown = 1\nrenderer_version = "aware.sdk.target-renderer.v7"',
        ),
        ('renderer_version = "aware.sdk.target-renderer.v7"\n', ""),
    ],
)
def test_profile_toml_rejects_invalid_declarations(old, new):
    with pytest.raises(AwareSdkTomlError):
        parse_sdk_manifest_bytes((MANIFEST + TABLES.replace(old, new)).encode())


@pytest.mark.parametrize(
    "tables",
    [
        "\n[generation_profiles]\n",
        "\n" + "\n".join(f"[generation_profiles.p{i}]" for i in range(33)),
        TABLES.replace(
            'operations = ["probe.observe"]',
            "operations = [" + ",".join(f'"probe.x{i:04}"' for i in range(1025)) + "]",
        ),
        TABLES.replace(
            'operations = ["probe.observe"]',
            "operations = [" + ",".join(f'"probe.x{i:04}"' for i in range(1024)) + "]",
        ),
        TABLES.replace("python/probe/_read_generated", "python/probe/" + "x" * 1024),
        TABLES.replace(
            "python/probe/_read_generated",
            "python/probe/" + "x" * (1024 - len("python/probe/")),
        ),
    ],
)
def test_profile_limits(tables):
    with pytest.raises(AwareSdkTomlError):
        parse_sdk_manifest_bytes((MANIFEST + tables).encode())


def test_profiles_require_explicit_target_rails_and_retain_unknown_key_rejection():
    for body in (
        MANIFEST.replace('root_dir = "python"\n', "") + TABLES,
        MANIFEST.replace('[targets.python.public_package]\npackage_dir = "probe"\n', "")
        + TABLES,
        MANIFEST
        + TABLES
        + '\n[definition]\nselected_operation_refs = ["probe.observe"]\n',
    ):
        with pytest.raises(AwareSdkTomlError):
            parse_sdk_manifest_bytes(body.encode())


@pytest.mark.parametrize(
    "mutation",
    ["tag", "empty", "unknown", "duplicate", "order", "renderer", "operations", "path"],
)
def test_meaning_codec_cannot_smuggle_invalid_profiles(mutation):
    raw = json.loads(encode_sdk_manifest_meaning(profiled()))
    profiles = raw["meaning"]["generation_profiles"]
    if mutation == "tag":
        raw["format"] = "aware.sdk.manifest.meaning.v1"
    elif mutation == "empty":
        raw["meaning"]["generation_profiles"] = []
    elif mutation == "unknown":
        profiles[0]["authority"] = "current"
    elif mutation == "duplicate":
        profiles[1]["name"] = profiles[0]["name"]
    elif mutation == "order":
        profiles.reverse()
    elif mutation == "renderer":
        profiles[0]["renderer_version"] = "auto"
    elif mutation == "operations":
        profiles[1]["operations"] = ["probe.legacy"]
    elif mutation == "path":
        profiles[0]["python_generated_dir"] = "outside"
    with pytest.raises(SdkManifestMeaningCodecError):
        decode_sdk_manifest_meaning(canonical(raw))


def test_codec_refuses_forged_in_memory_profile_and_legacy_retagging():
    spec = profiled()
    forged = replace(spec.generation_profiles[0], renderer_version="auto")
    with pytest.raises(SdkManifestMeaningCodecError):
        encode_sdk_manifest_meaning(replace(spec, generation_profiles=[forged]))
    raw = json.loads(
        encode_sdk_manifest_meaning(parse_sdk_manifest_bytes(MANIFEST.encode()))
    )
    raw["format"] = "aware.sdk.manifest.meaning.profiled.v1"
    with pytest.raises(SdkManifestMeaningCodecError):
        decode_sdk_manifest_meaning(canonical(raw))
