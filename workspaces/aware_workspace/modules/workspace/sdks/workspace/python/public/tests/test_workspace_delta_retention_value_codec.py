"""Production descriptive parity and strict codecs, not executable retention."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import stat
import subprocess
import sys
import tomllib
import types
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
from aware_workspace_sdk import repository_delta_retention_codec as codec
from aware_workspace_sdk import repository_delta_retention_values as values
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").is_file()
)
SDK = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware"
AUTHORED = SDK / "repository_delta_retention_values.aware"
FIXTURE = Path(__file__).parent / "fixtures/workspace_delta_retention_values.aware"
LEDGER = json.loads(
    (
        ROOT
        / "docs/reports/workspace-delta-retention-production-values-inputs-20261010.json"
    ).read_text()
)
OBS = values.WorkspaceRepositoryDeltaRetentionObservation
EVIDENCE = values.WorkspaceRepositoryDeltaRetentionRefusalEvidence
VALUE_TYPES = (OBS, EVIDENCE)
PHASES = get_args(values.WorkspaceRepositoryDeltaRetentionPhase)
CODES = get_args(values.WorkspaceRepositoryDeltaRetentionRefusalCode)
to_payload = codec.repository_delta_retention_value_to_payload
from_payload = codec.repository_delta_retention_value_from_payload
to_json = codec.repository_delta_retention_value_to_json
from_json = codec.repository_delta_retention_value_from_json
ERROR = codec.WorkspaceDeltaRetentionValueError


def observation(phase="allocated", *, nullable=False):
    return OBS(
        "retention:é",
        None if nullable else "binding:é",
        phase,
        "generation:1",
        2**63 + 19,
        ("known", "é", "known"),
    )


def sample(value_type, *, nullable=False):
    value = observation(nullable=nullable)
    return (
        value if value_type is OBS else EVIDENCE(CODES[-1], None if nullable else value)
    )


def lower(*, combined=False):
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())["sdk"]
    selected = [AUTHORED]
    if combined:
        selected.extend(
            SDK / name
            for name in (
                "repository_publication_values.aware",
                "repository_publication_ports.aware",
            )
        )
    documents = tuple(
        parse_neutral_aware_source(
            p.read_text(), source_path="/sdk/workspace/" + p.name
        )
        for p in selected
    )
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=manifest["package_name"],
                fqn_prefix=manifest["fqn_prefix"],
                sources_root="/sdk/workspace",
                dependencies=(),
                documents=documents,
                namespace_by_source_path=tuple((d.source_path, "") for d in documents),
            ),
        ),
        selected_package_names=frozenset({manifest["package_name"]}),
    )


@pytest.mark.parametrize("path", tuple(LEDGER["preserved_inputs"]))
def test_all_49_inputs_remain_committed_current_and_mode_bound(path):
    p, pin = ROOT / path, LEDGER["preserved_inputs"][path]
    assert hashlib.sha256(p.read_bytes()).hexdigest() == pin["sha256"]
    assert stat.S_IMODE(p.stat().st_mode) == pin["mode"]
    assert (
        subprocess.check_output(
            ["git", "show", LEDGER["revision"] + ":" + path], cwd=ROOT
        )
        == p.read_bytes()
    )
    assert (
        subprocess.check_output(
            ["git", "ls-tree", LEDGER["revision"], "--", path], cwd=ROOT, text=True
        ).split()[0]
        == pin["git_mode"]
    )


@pytest.mark.parametrize("value_type", VALUE_TYPES)
def test_real_production_lowering_matches_python_fields_types_order_and_enums(
    value_type,
):
    meaning = lower()
    owner = "aware_workspace_sdk." + value_type.__name__
    members = {
        e.fqn.rsplit(".", 1)[1]: meaning_value_to_json(e.payload)
        for e in meaning.entries
        if e.kind == "member" and e.fqn.rsplit(".", 1)[0] == owner
    }
    hints = get_type_hints(value_type)
    assert set(members) == set(hints)
    for position, field in enumerate(dataclasses.fields(value_type)):
        annotation = hints[field.name]
        nullable = get_origin(annotation) is types.UnionType
        if nullable:
            annotation = next(a for a in get_args(annotation) if a is not type(None))
        entry = members[field.name]
        assert entry["position"] == position
        assert entry["nullable"] is nullable
        assert entry["identity_key"] is False
        spelling = entry["type_expression"].removesuffix("?")
        if get_origin(annotation) is Literal:
            enums = sorted(
                (
                    e
                    for e in meaning.entries
                    if e.kind == "enum_option"
                    and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + spelling
                ),
                key=lambda e: meaning_value_to_json(e.payload)["position"],
            )
            assert tuple(e.fqn.rsplit(".", 1)[1] for e in enums) == get_args(annotation)
        elif get_origin(annotation) is tuple:
            assert spelling == "String[]"
            assert get_args(annotation) == (str, Ellipsis)
            assert entry["collection"] is True
        else:
            assert spelling == {str: "String", int: "Int"}.get(
                annotation, annotation.__name__
            )


@pytest.mark.parametrize("value_type", VALUE_TYPES)
@pytest.mark.parametrize("nullable", (False, True))
def test_roundtrip_preserves_nulls_exact_type_order_and_input_without_authority(
    value_type, nullable
):
    original = sample(value_type, nullable=nullable)
    payload = to_payload(original)
    saved = copy.deepcopy(payload)
    decoded = from_payload(value_type, payload)
    assert (
        type(decoded) is value_type and decoded == original and decoded is not original
    )
    assert payload == saved
    assert tuple(payload) == tuple(f.name for f in dataclasses.fields(value_type))
    assert from_json(value_type, to_json(original)) == original
    assert to_json(original) == to_json(decoded)
    for name in (
        "verify_repository_binding",
        "initialize_delta_retention",
        "release_retention",
        "record_body",
    ):
        assert not hasattr(decoded, name)


@pytest.mark.parametrize("phase", PHASES)
@pytest.mark.parametrize("code", CODES)
def test_every_finite_phase_and_refusal_pair_preserves_known_evidence(phase, code):
    value = EVIDENCE(code, observation(phase))
    assert from_json(EVIDENCE, to_json(value)) == value
    assert from_payload(EVIDENCE, to_payload(value)).observation.phase == phase


@pytest.mark.parametrize("code", CODES)
def test_unavailable_observation_stays_none_not_an_effect_free_or_caller_owned_claim(
    code,
):
    value = EVIDENCE(code, None)
    assert to_payload(value) == {"code": code, "observation": None}
    assert from_json(EVIDENCE, to_json(value)) == value


FIELDS = tuple(
    (value_type, field.name)
    for value_type in VALUE_TYPES
    for field in dataclasses.fields(value_type)
)


@pytest.mark.parametrize(("value_type", "field"), FIELDS)
def test_missing_or_extra_field_refuses_including_required_nulls(value_type, field):
    payload = to_payload(sample(value_type, nullable=True))
    missing = dict(payload)
    del missing[field]
    for invalid in (missing, dict(payload, restore_authority=True)):
        saved = copy.deepcopy(invalid)
        with pytest.raises(ERROR):
            from_payload(value_type, invalid)
        with pytest.raises(ERROR):
            from_json(value_type, json.dumps(invalid))
        assert invalid == saved


BAD_FIELDS = (
    ("retention_ref", None),
    ("retention_ref", 7),
    ("retention_ref", "\ud800"),
    ("repository_binding_ref", True),
    ("repository_binding_ref", "\udfff"),
    ("phase", "published"),
    ("phase", 1),
    ("phase", None),
    ("provider_generation", False),
    ("provider_generation", "\ud800"),
    ("original_process_id", True),
    ("original_process_id", 1.0),
    ("original_process_id", None),
    ("original_process_id", float("inf")),
    ("diagnostics", None),
    ("diagnostics", "diagnostic"),
    ("diagnostics", [False]),
    ("diagnostics", ["\ud800"]),
)


@pytest.mark.parametrize(("field", "invalid"), BAD_FIELDS)
@pytest.mark.parametrize("nested", (False, True))
def test_malformed_primitives_and_nested_evidence_are_typed_refusals(
    field, invalid, nested
):
    payload = to_payload(observation())
    payload[field] = invalid
    wrapped = {"code": CODES[0], "observation": payload} if nested else payload
    saved = repr(wrapped)
    with pytest.raises(ERROR):
        from_payload(EVIDENCE if nested else OBS, wrapped)
    assert repr(wrapped) == saved


@pytest.mark.parametrize(("field", "invalid"), BAD_FIELDS)
def test_encoding_validates_even_caller_constructed_or_mutated_values(field, invalid):
    value = observation()
    if field == "diagnostics" and type(invalid) is list:
        invalid = tuple(invalid)
    object.__setattr__(value, field, invalid)
    with pytest.raises(ERROR):
        to_payload(value)
    with pytest.raises(ERROR):
        to_json(value)


def test_collections_are_detached_in_both_directions_and_keep_duplicates_and_order():
    original = EVIDENCE(CODES[0], observation())
    payload = to_payload(original)
    decoded = from_payload(EVIDENCE, payload)
    payload["observation"]["diagnostics"].append("mutated")
    assert original.observation.diagnostics == ("known", "é", "known")
    assert decoded.observation.diagnostics == original.observation.diagnostics
    second = to_payload(original)
    assert second["observation"]["diagnostics"] == ["known", "é", "known"]
    assert (
        second["observation"]["diagnostics"]
        is not payload["observation"]["diagnostics"]
    )


@pytest.mark.parametrize("invalid", (None, [], 1, True, "receipt"))
@pytest.mark.parametrize("value_type", VALUE_TYPES)
def test_non_object_root_is_refused(value_type, invalid):
    with pytest.raises(ERROR):
        from_payload(value_type, invalid)
    with pytest.raises(ERROR):
        from_json(value_type, json.dumps(invalid))


@pytest.mark.parametrize("invalid", ("unknown", "", None, 1, True))
def test_refusal_code_is_exact_finite_vocabulary(invalid):
    with pytest.raises(ERROR):
        from_payload(EVIDENCE, {"code": invalid, "observation": None})
    with pytest.raises(ERROR):
        to_payload(EVIDENCE(invalid, None))


@pytest.mark.parametrize(
    "number", ("NaN", "Infinity", "-Infinity", "1e999", "1.0", "1e0", "-1e999")
)
@pytest.mark.parametrize("nested", (False, True))
def test_json_rejects_nonfinite_overflow_and_all_float_tokens_before_selection(
    number, nested
):
    source = to_json(observation()).replace(
        str(observation().original_process_id), number
    )
    if nested:
        source = '{"code":"retention_not_issued","observation":' + source + "}"
    with pytest.raises(ERROR):
        from_json(EVIDENCE if nested else OBS, source)


@pytest.mark.parametrize(
    "source",
    (
        '{"code":"retention_not_issued","code":"retention_owner_mismatch","observation":null}',
        '{"code":"retention_not_issued","observation":null,"observation":null}',
        '{"code":"retention_not_issued","observation":',
        "{",
        "",
        '{"observation":null,}',
    ),
)
def test_duplicate_or_malformed_json_refuses_without_normalizing_input(source):
    saved = source
    with pytest.raises(ERROR):
        from_json(EVIDENCE, source)
    assert source == saved


def test_duplicate_nested_fields_are_not_overwritten():
    nested = to_json(observation()).replace(
        '"phase":"allocated"', '"phase":"active","phase":"allocated"'
    )
    with pytest.raises(ERROR, match="duplicate field"):
        from_json(
            EVIDENCE, '{"code":"retention_not_issued","observation":' + nested + "}"
        )


def test_deep_json_recursion_has_typed_refusal():
    with pytest.raises(ERROR):
        from_json(OBS, "[" * 2000 + "0" + "]" * 2000)


@pytest.mark.parametrize("error_type", (ValueError, RecursionError))
def test_serializer_failure_preserves_value_and_has_typed_refusal(
    monkeypatch, error_type
):
    original = observation()
    payload = to_payload(original)

    def unavailable(*args, **kwargs):
        raise error_type("serializer unavailable")

    monkeypatch.setattr(codec.json, "dumps", unavailable)
    with pytest.raises(ERROR) as refused:
        to_json(original)
    assert type(refused.value.__cause__) is error_type
    assert to_payload(original) == payload


@pytest.mark.parametrize("source", (None, b"{}", {}, [], 2))
def test_json_requires_text(source):
    with pytest.raises(ERROR):
        from_json(OBS, source)


@pytest.mark.parametrize("value_type", VALUE_TYPES)
def test_forged_uninitialized_dataclass_is_a_typed_encoding_refusal(value_type):
    with pytest.raises(ERROR, match="missing authored"):
        to_payload(object.__new__(value_type))


def test_subclasses_proxies_and_unselected_targets_cannot_encode_or_decode():
    class Subclass(OBS):
        pass

    class Proxy:
        def __getattr__(self, name):
            raise AssertionError("proxy attributes must not be touched")

    class EqualType:
        def __eq__(self, other):
            raise AssertionError("type equality is not selection")

    for fake in (Proxy(), Subclass(**dataclasses.asdict(observation())), object()):
        with pytest.raises(ERROR):
            to_payload(fake)
    for target in (
        Proxy,
        Subclass,
        object,
        "WorkspaceRepositoryDeltaRetentionClient",
        EqualType(),
    ):
        with pytest.raises(ERROR):
            from_payload(target, to_payload(observation()))
        with pytest.raises(ERROR):
            from_json(target, "{}")


def test_non_string_keys_and_mapping_or_collection_subclasses_refuse():
    class DictSubclass(dict):
        pass

    class ListSubclass(list):
        pass

    class TupleSubclass(tuple):
        pass

    for invalid in (
        DictSubclass(to_payload(observation())),
        {1: "wrong"},
        dict(to_payload(observation()), diagnostics=ListSubclass()),
    ):
        with pytest.raises(ERROR):
            from_payload(OBS, invalid)
    with pytest.raises(ERROR):
        to_payload(dataclasses.replace(observation(), diagnostics=TupleSubclass()))


@pytest.mark.parametrize("value_type", VALUE_TYPES)
def test_bindings_are_frozen_slotted_required_data_not_runtime_admission(value_type):
    value = sample(value_type)
    assert not hasattr(value, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(value, dataclasses.fields(value_type)[0].name, "mutated")
    with pytest.raises((TypeError, AttributeError)):
        value.extra = True
    assert all(
        field.default is dataclasses.MISSING
        and field.default_factory is dataclasses.MISSING
        for field in dataclasses.fields(value_type)
    )


def test_production_preserves_accepted_fixture_body_and_existing_manifest_selection():
    assert (
        AUTHORED.read_text().split("\n", 2)[2] == FIXTURE.read_text().split("\n", 2)[2]
    )
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())
    assert "*.aware" in manifest["build"]["include_paths"]
    assert AUTHORED.parent == SDK
    assert lower().canonical_bytes() == lower().canonical_bytes()
    assert {p.source_sha256 for e in lower().entries for p in e.provenance} == {
        hashlib.sha256(AUTHORED.read_bytes()).hexdigest()
    }


def test_neutral_descriptive_sources_compose_without_namespace_collision_or_capabilities():
    standalone, combined = lower(), lower(combined=True)
    isolated = {
        (e.kind, e.fqn): meaning_value_to_json(e.payload) for e in standalone.entries
    }
    composed = {
        (e.kind, e.fqn): meaning_value_to_json(e.payload) for e in combined.entries
    }
    assert all(composed[key] == payload for key, payload in isolated.items())
    names = {e.fqn.rsplit(".", 1)[1] for e in standalone.entries if e.kind == "symbol"}
    assert names == set(values.__all__)


def test_pure_modules_export_exact_supported_data_and_codecs_without_live_facade():
    assert len(values.__all__) == 4 and len(codec.__all__) == 5
    for module in (values, codec):
        assert all(getattr(module, name) is not None for name in module.__all__)
        for name in (
            "WorkspaceRepositoryDeltaRetentionClient",
            "WorkspaceRepositoryDeltaRetentionFactory",
            "WorkspaceRepositoryDeltaRetentionRefusal",
            "FilesystemRepositoryDeltaRetentionOwner",
        ):
            assert not hasattr(module, name)


def test_fresh_source_import_and_roundtrip_refuse_operational_owner_imports():
    script = """
import importlib.abc, json, sys
blocked = ("aware_workspace_runtime", "aware_workspace_fs_adapter", "aware_workspace_service_sdk_adapter", "aware_issue", "aware_environment", "aware_local_dev", "aware_workspace_ontology")
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.startswith(blocked): raise AssertionError(fullname)
sys.meta_path.insert(0, Guard())
from aware_workspace_sdk import repository_delta_retention_values as v
from aware_workspace_sdk import repository_delta_retention_codec as c
value = v.WorkspaceRepositoryDeltaRetentionRefusalEvidence("retention_supplier_unavailable", None)
assert c.repository_delta_retention_value_from_json(type(value), c.repository_delta_retention_value_to_json(value)) == value
assert not any(name.startswith(blocked) for name in sys.modules)
print(json.dumps({"ok": True, "root_exports": __import__("aware_workspace_sdk").__all__}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout) == {"ok": True, "root_exports": []}
