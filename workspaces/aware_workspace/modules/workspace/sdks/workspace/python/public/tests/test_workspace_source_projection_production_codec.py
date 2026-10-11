"""Authored production parity and detached codecs, not executable authority."""

from __future__ import annotations

import ast
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
from aware_workspace_sdk import repository_source_projection_codec as codec
from aware_workspace_sdk import repository_source_projection_values as values
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
SOURCE = SDK / "repository_source_projection_values.aware"
FIXTURE = Path(__file__).parent / "fixtures/workspace_source_projection_values.aware"
SIGNATURES = (
    Path(__file__).parent / "fixtures/workspace_source_projection_signatures.pyi"
)
LEDGER = json.loads(
    (
        ROOT
        / "docs/reports/workspace-source-projection-production-inputs-20261010.json"
    ).read_text()
)
VALUE_TYPES = values.SOURCE_PROJECTION_VALUE_TYPES
ERROR = codec.WorkspaceSourceProjectionValueError
to_payload = codec.repository_source_projection_value_to_payload
from_payload = codec.repository_source_projection_value_from_payload
to_json = codec.repository_source_projection_value_to_json
from_json = codec.repository_source_projection_value_from_json
ENUMS = {
    name: getattr(values, name)
    for name in values.__all__
    if get_origin(getattr(values, name)) is Literal
}
RENAMES = LEDGER["name_mapping"]


def sample(annotation, *, nulls=False):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is types.UnionType:
        return None if nulls else sample(arguments[0], nulls=nulls)
    if annotation is str:
        return "descriptive:é"
    if annotation is int:
        return 2**63 + 19
    if annotation is bool:
        return not nulls
    if origin is Literal:
        return arguments[-1] if nulls else arguments[0]
    if origin is tuple:
        return (sample(arguments[0], nulls=nulls),) * 2
    hints = get_type_hints(annotation)
    return annotation(
        **{
            field.name: sample(hints[field.name], nulls=nulls)
            for field in dataclasses.fields(annotation)
        }
    )


def lower(*, combined=False):
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())["sdk"]
    sources = [SOURCE]
    if combined:
        sources.extend(
            SDK / name
            for name in (
                "repository_publication_values.aware",
                "repository_publication_ports.aware",
                "repository_delta_retention_values.aware",
            )
        )
    documents = tuple(
        parse_neutral_aware_source(
            p.read_text(), source_path="/sdk/workspace/" + p.name
        )
        for p in sources
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
def test_preserved_inputs_match_current_bytes_modes_and_committed_blobs(path):
    pin, target = LEDGER["preserved_inputs"][path], ROOT / path
    raw = target.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
    assert len(raw) == pin["size_bytes"]
    assert stat.S_IMODE(target.stat().st_mode) == pin["mode"]
    assert (
        subprocess.check_output(
            ["git", "show", LEDGER["revision"] + ":" + path], cwd=ROOT
        )
        == raw
    )
    entry = subprocess.check_output(
        ["git", "ls-tree", LEDGER["revision"], "--", path], cwd=ROOT, text=True
    ).split()
    assert entry[:3] == [pin["git_mode"], "blob", pin["git_blob"]]


def test_accepted_25_inputs_and_interface_inventory_remain_preserved():
    accepted = json.loads(
        (
            ROOT
            / "docs/reports/workspace-source-projection-authored-inputs-20261010.json"
        ).read_text()
    )
    assert accepted["inputs"] == LEDGER["original_inputs"]
    assert accepted["revision"] == LEDGER["original_input_revision"]
    assert accepted["qualification"]["port_signature_count"] == 17
    assert LEDGER["runtime_acceptance"] is LEDGER["installed_acceptance"] is False
    assert len(LEDGER["effect_paths"]) == 7


def test_production_source_is_exact_fixture_promotion_with_explicit_name_mapping():
    fixture = FIXTURE.read_text().replace(
        "// Unregistered descriptive qualification fixture, not an SDK implementation.",
        "// Authored descriptive source projection values. No executable owner ports.",
    )
    for before, after in RENAMES.items():
        fixture = fixture.replace(before, after)
    assert SOURCE.read_text() == fixture
    manifest = tomllib.loads((SDK / "aware.sdk.toml").read_text())
    assert manifest["build"]["sources_dir"] == "."
    assert manifest["build"]["include_paths"] == ["*.aware"]


@pytest.mark.parametrize("record", VALUE_TYPES)
def test_production_fields_match_real_authored_lowering(record):
    snapshot = lower()
    members = {
        e.fqn.rsplit(".", 1)[1]: meaning_value_to_json(e.payload)
        for e in snapshot.entries
        if e.kind == "member"
        and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + record.__name__
    }
    hints = get_type_hints(record)
    assert set(members) == set(hints)
    for index, field in enumerate(dataclasses.fields(record)):
        annotation = hints[field.name]
        nullable = get_origin(annotation) is types.UnionType
        if nullable:
            annotation = next(a for a in get_args(annotation) if a is not type(None))
        collection = get_origin(annotation) is tuple
        if collection:
            annotation = get_args(annotation)[0]
        member = members[field.name]
        assert member["position"] == index
        assert member["nullable"] is nullable
        assert member["collection"] is collection
        assert member["identity_key"] is False
        spelling = member["type_expression"].removesuffix("?").removesuffix("[]")
        if get_origin(annotation) is Literal:
            assert ENUMS[spelling] is annotation
        elif annotation in (str, int, bool):
            assert spelling == {str: "String", int: "Int", bool: "Bool"}[annotation]
        else:
            assert member["target_fqn"] == "aware_workspace_sdk." + annotation.__name__


@pytest.mark.parametrize("name", tuple(ENUMS))
def test_all_authored_enums_preserve_exact_option_order(name):
    options = sorted(
        (
            e
            for e in lower().entries
            if e.kind == "enum_option"
            and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + name
        ),
        key=lambda e: meaning_value_to_json(e.payload)["position"],
    )
    assert tuple(e.fqn.rsplit(".", 1)[1] for e in options) == get_args(ENUMS[name])


def test_combined_lowering_preserves_distinct_publication_and_source_effects():
    from aware_workspace_sdk.repository_publication.values import (
        WorkspaceRepositoryPhysicalEffect,
    )

    snapshot = lower(combined=True)
    for record in (
        WorkspaceRepositoryPhysicalEffect,
        values.WorkspaceSourcePhysicalEffect,
    ):
        members = {
            e.fqn.rsplit(".", 1)[1]
            for e in snapshot.entries
            if e.kind == "member"
            and e.fqn.rsplit(".", 1)[0] == "aware_workspace_sdk." + record.__name__
        }
        assert members == {f.name for f in dataclasses.fields(record)}
    assert len(dataclasses.fields(WorkspaceRepositoryPhysicalEffect)) == 13
    assert len(dataclasses.fields(values.WorkspaceSourcePhysicalEffect)) == 8


@pytest.mark.parametrize("record", VALUE_TYPES)
@pytest.mark.parametrize("nulls", [False, True])
def test_every_root_round_trips_in_both_formats_without_input_mutation(record, nulls):
    original = sample(record, nulls=nulls)
    payload = to_payload(original)
    saved = copy.deepcopy(payload)
    restored = from_payload(record, payload)
    assert type(restored) is record and restored == original
    assert payload == saved
    assert from_json(record, to_json(original)) == original
    assert tuple(payload) == tuple(f.name for f in dataclasses.fields(record))


FIELD_CASES = tuple(
    (record, field.name)
    for record in VALUE_TYPES
    for field in dataclasses.fields(record)
)


@pytest.mark.parametrize(("record", "field"), FIELD_CASES)
def test_each_required_field_refuses_omission_even_when_nullable(record, field):
    payload = to_payload(sample(record))
    payload.pop(field)
    saved = copy.deepcopy(payload)
    with pytest.raises(ERROR):
        from_payload(record, payload)
    assert payload == saved


@pytest.mark.parametrize(("record", "field"), FIELD_CASES)
def test_each_field_refuses_incorrect_nested_or_primitive_data(record, field):
    payload = to_payload(sample(record))
    annotation = get_type_hints(record)[field]
    if get_origin(annotation) is types.UnionType:
        annotation = next(a for a in get_args(annotation) if a is not type(None))
    payload[field] = True if annotation is int else 1 if annotation is bool else 3.25
    saved = copy.deepcopy(payload)
    with pytest.raises(ERROR):
        from_payload(record, payload)
    assert payload == saved


@pytest.mark.parametrize("record", VALUE_TYPES)
def test_extra_fields_and_forged_incomplete_values_refuse(record):
    payload = to_payload(sample(record))
    payload["restore_authority"] = True
    with pytest.raises(ERROR):
        from_payload(record, payload)
    forged = object.__new__(record)
    with pytest.raises(ERROR):
        to_payload(forged)


@pytest.mark.parametrize("record", VALUE_TYPES)
def test_subclasses_refuse_without_coercion(record):
    child = type("Foreign", (record,), {})
    with pytest.raises(ERROR):
        to_payload(sample(child))
    with pytest.raises(ERROR):
        from_payload(child, to_payload(sample(record)))


@pytest.mark.parametrize("name", tuple(ENUMS))
def test_unknown_finite_states_refuse_through_containing_root(name):
    for record in VALUE_TYPES:
        for field, annotation in get_type_hints(record).items():
            if annotation is ENUMS[name]:
                payload = to_payload(sample(record))
                payload[field] = "invented_state"
                with pytest.raises(ERROR):
                    from_payload(record, payload)
                return
    pytest.fail("No containing root for qualified enum")


@pytest.mark.parametrize("number", ("NaN", "Infinity", "-Infinity", "1e999", "1.0"))
def test_nonfinite_or_float_json_refuses_even_inside_extra_omitted_data(number):
    for field in ("cursor", "ignored"):
        source = json.dumps(to_payload(sample(values.RepositoryObservationCoordinate)))
        source = source[:-1] + ', "' + field + '": ' + number + "}"
        with pytest.raises(ERROR):
            from_json(values.RepositoryObservationCoordinate, source)


@pytest.mark.parametrize("source", ("null", "[]", "{", '{"x":1,"x":2}', '"scalar"'))
def test_malformed_root_and_duplicate_json_refuse(source):
    with pytest.raises(ERROR):
        from_json(values.WorkspaceSourceProjectionObservation, source)


def test_required_nulls_detachment_and_unknown_history_do_not_restore_authority():
    original = sample(values.WorkspaceSourceProjectionObservation)
    original = dataclasses.replace(
        original,
        phase="terminal",
        source_effect_state="unknown",
        physical_effect=None,
        execution_evidence=values.WorkspaceRepositoryMutationExecutionEvidence(
            "unavailable", "not_attempted", False, ("physical return unavailable",)
        ),
        convergence_state="unknown",
        ledger_complete=False,
    )
    payload = to_payload(original)
    restored = from_payload(type(original), payload)
    payload["diagnostics"].append("later caller edit")
    payload["binding"]["provider"]["provider_ref"] = "invented"
    assert restored == original
    assert (
        restored.source_effect_state == "unknown" and restored.physical_effect is None
    )
    assert not restored.ledger_complete
    for port in (
        "project_source",
        "verify_source_projection_plan",
        "enroll_issue_projection",
    ):
        assert not hasattr(restored, port)


def test_known_effect_survives_unknown_retention_cleanup_and_incomplete_ledger():
    original = sample(values.WorkspaceSourceProjectionObservation, nulls=True)
    original = dataclasses.replace(
        original,
        source_effect_state="applied",
        physical_effect=values.WorkspaceSourcePhysicalEffect(
            "applied",
            False,
            True,
            "sha256:" + "a" * 64,
            1,
            True,
            "sha256:" + "b" * 64,
            2,
        ),
        execution_evidence=values.WorkspaceRepositoryMutationExecutionEvidence(
            "returned", "unknown", False, ("retention unavailable",)
        ),
        ledger_complete=False,
    )
    assert from_json(type(original), to_json(original)) == original


def test_bad_utf8_and_non_text_json_refuse():
    value = sample(values.WorkspaceSourceProviderBinding)
    with pytest.raises(ERROR):
        to_payload(dataclasses.replace(value, execution_id="\ud800"))
    payload = to_payload(value)
    payload["execution_id"] = "\ud800"
    with pytest.raises(ERROR):
        from_payload(type(value), payload)
    with pytest.raises(ERROR):
        from_json(type(value), b"{}")


def test_collections_are_exact_and_detached_not_coerced():
    value = values.WorkspaceRepositoryMutationExecutionEvidence(
        "returned", "retained", True, ("x", "x")
    )
    with pytest.raises(ERROR):
        to_payload(dataclasses.replace(value, diagnostics=["x"]))
    payload = to_payload(value)
    payload["diagnostics"] = ("x",)
    with pytest.raises(ERROR):
        from_payload(type(value), payload)


def test_no_live_handle_or_generic_type_is_in_the_codec_registry():
    for value in (object(), Path("."), {"plan": "forged"}):
        with pytest.raises(ERROR):
            to_payload(value)
    for value_type in (object, dict, Path):
        with pytest.raises(ERROR):
            from_payload(value_type, {})
    assert len(VALUE_TYPES) == 13
    assert len(ENUMS) == 8
    for live in (
        "WorkspaceSourceProjectionPlan",
        "WorkspaceSourceProjectionAdmission",
        "IssueSourceProjectionAdmission",
    ):
        assert not hasattr(values, live)


def test_descriptive_module_imports_do_not_select_runtime_physical_or_foreign_owners():
    script = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(("aware_workspace_runtime", "aware_workspace_fs_adapter", "aware_issue", "aware_file_system", "aware_meta", "aware_workspace_sdk.service")):
            raise AssertionError("unexpected implementation import: " + fullname)
sys.meta_path.insert(0, Block())
from aware_workspace_sdk import repository_source_projection_values as v
from aware_workspace_sdk import repository_source_projection_codec as c
assert len(v.SOURCE_PROJECTION_VALUE_TYPES) == 13
assert c.repository_source_projection_value_from_json(v.WorkspaceSourceFileIdentity, '{"device":1,"inode":2}') == v.WorkspaceSourceFileIdentity(1,2)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_original_mirror_fields_remain_exact_without_original_constructor_aliasing():
    signatures = ast.parse(SIGNATURES.read_text())
    declarations = {n.name: n for n in signatures.body if isinstance(n, ast.ClassDef)}
    for before in (
        "RepositoryObservationCoordinate",
        "WorkspaceRepositoryPhysicalEffect",
        "WorkspaceRepositoryMutationExecutionEvidence",
    ):
        record = getattr(values, RENAMES.get(before, before))
        expected = [
            n.target.id
            for n in declarations[before].body
            if isinstance(n, ast.AnnAssign)
        ]
        assert tuple(f.name for f in dataclasses.fields(record)) == tuple(expected)


@pytest.mark.parametrize("state", ("none", "applied", "unknown"))
@pytest.mark.parametrize("exists", (False, True))
def test_genuine_original_physical_values_round_trip_as_detached_mirrors(state, exists):
    from aware_workspace_runtime.change_evidence import (
        WorkspaceRepositoryPhysicalEffect,
    )

    original = WorkspaceRepositoryPhysicalEffect(
        state,
        state == "applied",
        exists,
        "sha256:" + "a" * 64 if exists else None,
        1 if exists else None,
        exists,
        "sha256:" + "b" * 64 if exists else None,
        2 if exists else None,
    )
    payload = dataclasses.asdict(original)
    detached = from_payload(values.WorkspaceSourcePhysicalEffect, payload)
    assert to_payload(detached) == payload
    assert WorkspaceRepositoryPhysicalEffect(**to_payload(detached)) == original
    # Semantic evaluation remains original-owner work. There is no implicit
    # encoding of runtime objects as an SDK value or executable receipt.
    with pytest.raises(ERROR):
        to_payload(original)


@pytest.mark.parametrize(
    ("physical", "retention"),
    (
        ("not_dispatched", "not_attempted"),
        ("unavailable", "not_attempted"),
        ("returned", "not_attempted"),
        ("returned", "retained"),
        ("returned", "unknown"),
    ),
)
def test_genuine_execution_values_preserve_original_owner_validation(
    physical, retention
):
    from aware_workspace_runtime.repository_mutation import (
        WorkspaceRepositoryMutationExecutionEvidence,
    )

    original = WorkspaceRepositoryMutationExecutionEvidence(
        physical, retention, False, ("original diagnostic",)
    )
    descriptive = values.WorkspaceRepositoryMutationExecutionEvidence(
        original.physical_return_state,
        original.body_retention_state,
        original.ledger_complete,
        original.diagnostics,
    )
    decoded = from_json(type(descriptive), to_json(descriptive))
    assert decoded == descriptive
    assert (
        WorkspaceRepositoryMutationExecutionEvidence(
            decoded.physical_return_state,
            decoded.body_retention_state,
            decoded.ledger_complete,
            decoded.diagnostics,
        )
        == original
    )


def test_genuine_observation_coordinate_payload_preserves_original_owner_fields():
    from aware_workspace_runtime.repository_access import (
        RepositoryObservationCoordinate,
    )

    original = RepositoryObservationCoordinate(
        "binding:original", "epoch:1", 17, "snapshot", "visible", "1"
    )
    descriptive = from_payload(
        values.RepositoryObservationCoordinate, original.to_payload()
    )
    assert to_payload(descriptive) == original.to_payload()
    assert RepositoryObservationCoordinate(**to_payload(descriptive)) == original


def test_production_bindings_contain_no_port_signature_implementation():
    source = Path(values.__file__).read_text()
    assert "WorkspaceRepositorySourceProjectionClient" not in source
    assert "retain_projection_body" not in source
    assert "observe_source_projection_plan" not in source


@pytest.mark.parametrize("path", tuple(LEDGER["production"]["artifacts"]))
def test_production_artifacts_match_recorded_exact_byte_pins(path):
    assert (
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        == (LEDGER["production"]["artifacts"][path])
    )


@pytest.mark.parametrize("combined", (False, True))
def test_production_meaning_snapshots_match_recorded_provenance_digests(combined):
    snapshot = lower(combined=combined)
    pin = LEDGER["production"]["combined" if combined else "source"]
    assert snapshot.canonical_sha256 == pin["canonical_sha256"]
    assert len(snapshot.entries) == pin["entry_count"]
