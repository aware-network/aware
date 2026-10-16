"""Real authored tree value parity; no live admission or tree execution claim."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import tomllib
import types
from pathlib import Path
from typing import Literal, get_args, get_origin, get_type_hints

import pytest
from aware_issue_sdk import repository_tree_projection_codec as codec
from aware_issue_sdk import repository_tree_projection_values as values
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source
from tree_sitter_aware.ontology_meaning import meaning_value_to_json
from tree_sitter_aware.ontology_meaning_resolver import (
    OntologyMeaningPackageInput,
    resolve_ontology_meaning,
)

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "aware.repo.toml").is_file()
)
AUTHORED = ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/aware"
RECORDS = (
    values.IssueTreeProjectionRequest,
    values.IssueTreeBindingObservation,
    values.IssueTreeAdmissionObservation,
    values.IssueTreeResourceCleanup,
    values.IssueTreeAdmissionCleanup,
)
ENUMS = (
    "IssueTreePhase",
    "IssueTreeConsumptionState",
    "IssueTreeCleanupState",
    "IssueTreeResourceOwnership",
)


def sample(record):
    binding = values.IssueTreeBindingObservation(
        "plan",
        "workspace-provider",
        "generation",
        "binding",
        "repository",
        (11, 13),
        "codex-test",
        17,
        19,
        "workflow",
        "layout",
        "source",
        "physical",
        "sha256:" + "a" * 64,
        3,
        ("public/é.py", "public/.scratch"),
        ("public",),
        ("public/.scratch",),
    )
    resource = values.IssueTreeResourceCleanup(
        "resource",
        "preparation-reference",
        None,
        "released",
        True,
        "unknown",
        ("original close return unavailable",),
    )
    samples = {
        values.IssueTreeProjectionRequest: values.IssueTreeProjectionRequest(
            "fb/2026-10-12/tree",
            "sha256:" + "b" * 64,
            "author",
            "declared-author",
            "intent",
        ),
        values.IssueTreeBindingObservation: binding,
        values.IssueTreeResourceCleanup: resource,
        values.IssueTreeAdmissionObservation: values.IssueTreeAdmissionObservation(
            "fb/2026-10-12/tree",
            "request",
            binding,
            "aware.protocol.toml",
            "sha256:" + "c" * 64,
            (23, 29),
            "issue-generation",
            "admission",
            None,
            "retired",
            "unknown",
            "unknown",
            False,
            ("spent return unavailable",),
            False,
        ),
        values.IssueTreeAdmissionCleanup: values.IssueTreeAdmissionCleanup(
            "fb/2026-10-12/tree",
            "request",
            "admission",
            None,
            (resource,),
            "unknown",
            False,
            ("publication unchanged; cleanup unknown",),
        ),
    }
    return samples[record]


@pytest.fixture(scope="module")
def meaning():
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    path = "/sdk/issue/repository_tree_projection_values.aware"
    parsed = parse_neutral_aware_source(
        (AUTHORED / "repository_tree_projection_values.aware").read_text(),
        source_path=path,
    )
    package = manifest["sdk"]
    return resolve_ontology_meaning(
        (
            OntologyMeaningPackageInput(
                package_name=package["package_name"],
                fqn_prefix=package["fqn_prefix"],
                sources_root="/sdk/issue",
                dependencies=(),
                documents=(parsed,),
                namespace_by_source_path=((path, ""),),
            ),
        ),
        selected_package_names=frozenset({package["package_name"]}),
    )


@pytest.mark.parametrize("record", RECORDS)
def test_real_lowering_preserves_exact_accepted_schema_and_python_field_order(
    record, meaning
):
    joined = json.loads(
        (
            ROOT
            / "docs/reports/workspace-repository-tree-projection-inputs-20261011.json"
        ).read_text()
    )["joined_freeze_candidate"]
    accepted = joined["supplier_schemas"][record.__name__]
    members = {
        entry.fqn.rsplit(".", 1)[1]: meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "member"
        and entry.fqn.rsplit(".", 1)[0] == "aware_issue_sdk." + record.__name__
    }
    ordered = tuple(sorted(members, key=lambda name: members[name]["position"]))
    assert ordered == tuple(accepted["fields"])
    assert ordered == tuple(field.name for field in dataclasses.fields(record))
    assert tuple(codec.tree_projection_value_to_payload(sample(record))) == ordered
    assert codec.tree_projection_value_schema_id(record) == accepted["schema_id"]
    hints = get_type_hints(record)
    for name, hint in hints.items():
        nullable = get_origin(hint) is types.UnionType and type(None) in get_args(hint)
        if nullable:
            hint = next(arg for arg in get_args(hint) if arg is not type(None))
        collection = get_origin(hint) is tuple
        if collection:
            hint = get_args(hint)[0]
        primitive = hint in (str, int, bool) or hint == Literal[False]
        if primitive:
            type_name = (
                "Bool"
                if hint == Literal[False]
                else {str: "String", int: "Int", bool: "Bool"}[hint]
            )
        elif get_origin(hint) is Literal:
            type_name = next(
                enum
                for enum in ENUMS
                if get_args(getattr(values, enum)) == get_args(hint)
            )
        else:
            type_name = hint.__name__
        assert members[name]["nullable"] is nullable
        assert members[name]["collection"] is collection
        assert members[name]["primitive"] is primitive
        assert members[name]["type_name"] == type_name
    if record is values.IssueTreeAdmissionObservation:
        assert members["binding"]["nullable"] is True
        assert members["authority_source_identity"]["nullable"] is True
        assert members["authority_source_identity"]["collection"] is True
    if record is values.IssueTreeAdmissionCleanup:
        assert members["resources"]["collection"] is True


@pytest.mark.parametrize("name", ENUMS)
def test_all_enum_literals_genuinely_lower_without_new_authority(name, meaning):
    entries = [
        entry
        for entry in meaning.entries
        if entry.kind == "symbol" and entry.fqn == "aware_issue_sdk." + name
    ]
    assert len(entries) == 1
    payload = meaning_value_to_json(entries[0].payload)
    assert payload["kind"] == "enum_def"
    options = [
        meaning_value_to_json(entry.payload)
        for entry in meaning.entries
        if entry.kind == "enum_option"
        and entry.fqn.rsplit(".", 1)[0] == "aware_issue_sdk." + name
    ]
    assert tuple(
        option["name"] for option in sorted(options, key=lambda o: o["position"])
    ) == get_args(getattr(values, name))


@pytest.mark.parametrize("record", RECORDS)
def test_roundtrip_is_detached_preserves_unknowns_and_never_issues_authority(record):
    value = sample(record)
    payload = codec.tree_projection_value_to_payload(value)
    saved = json.dumps(payload)
    decoded = codec.tree_projection_value_from_payload(record, payload)
    assert decoded == value and type(decoded) is record
    assert (
        codec.tree_projection_value_from_json(
            record, codec.tree_projection_value_to_json(value)
        )
        == value
    )
    assert json.dumps(payload) == saved
    if record is values.IssueTreeAdmissionObservation:
        payload["binding"]["effect_paths"].clear()
        payload["diagnostics"].append("foreign")
        assert decoded.binding.effect_paths == ("public/é.py", "public/.scratch")
        assert (
            decoded.consumption_state == "unknown" and decoded.authorizes_retry is False
        )
    if record is values.IssueTreeAdmissionCleanup:
        payload["resources"][0]["diagnostics"].clear()
        assert decoded.resources[0].diagnostics == (
            "original close return unavailable",
        )
        assert decoded.cleanup_state == "unknown" and decoded.ledger_complete is False


@pytest.mark.parametrize("record", RECORDS)
def test_every_missing_field_and_unknown_field_refuses_without_input_mutation(record):
    payload = codec.tree_projection_value_to_payload(sample(record))
    for field in payload:
        invalid = dict(payload)
        del invalid[field]
        before = json.dumps(invalid)
        with pytest.raises(codec.IssueTreeProjectionValueError):
            codec.tree_projection_value_from_payload(record, invalid)
        assert json.dumps(invalid) == before
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_payload(record, dict(payload, admitted=True))


BAD_PATHS = [
    "",
    "/a",
    "a\\b",
    ".",
    "..",
    "a/../b",
    "a//b",
    "a/",
    "e\u0301/a",
    "a\ud800",
    "a" * 1025,
] + [f"a{chr(code)}b" for code in (*range(32), *range(127, 160))]


@pytest.mark.parametrize("path", BAD_PATHS)
@pytest.mark.parametrize(
    "field", ("effect_paths", "read_guard_paths", "scratch_effect_paths")
)
def test_all_path_collections_require_exact_nfc_boundaries(field, path):
    value = dataclasses.replace(
        sample(values.IssueTreeBindingObservation), **{field: (path,)}
    )
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(value)


@pytest.mark.parametrize(
    "field", ("effect_paths", "read_guard_paths", "scratch_effect_paths")
)
def test_repeated_paths_refuse_but_original_unsorted_order_is_preserved(field):
    original = sample(values.IssueTreeBindingObservation)
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            dataclasses.replace(original, **{field: ("a", "a")})
        )
    value = dataclasses.replace(original, **{field: ("z", "a")})
    assert getattr(
        codec.tree_projection_value_from_json(
            type(value), codec.tree_projection_value_to_json(value)
        ),
        field,
    ) == ("z", "a")


def issue_path_value(field, path):
    if field in ("effect_paths", "read_guard_paths", "scratch_effect_paths"):
        return dataclasses.replace(
            sample(values.IssueTreeBindingObservation), **{field: (path,)}
        )
    record = (
        values.IssueTreeAdmissionObservation
        if field == "authority_source_path"
        else values.IssueTreeResourceCleanup
    )
    return dataclasses.replace(sample(record), **{field: path})


@pytest.mark.parametrize("components", (64, 65, 128, 512))
@pytest.mark.parametrize(
    "field",
    (
        "effect_paths",
        "read_guard_paths",
        "scratch_effect_paths",
        "authority_source_path",
        "path",
    ),
)
def test_c_path_depth_corresponds_across_public_owner_codecs(components, field):
    from aware_workspace_sdk import repository_tree_projection_codec as workspace_codec
    from aware_workspace_sdk import (
        repository_tree_projection_values as workspace_values,
    )

    path = "/".join(["a"] * components)
    assert len(path.encode("utf-8")) <= 1024
    workspace = workspace_values.WorkspaceTreeFileIntent(
        path, "CREATE", "source.py", 0o644
    )
    workspace_json = workspace_codec.repository_tree_projection_value_to_json(workspace)
    assert (
        workspace_codec.repository_tree_projection_value_from_json(
            type(workspace), workspace_json
        ).path
        == path
    )
    issue = issue_path_value(field, path)
    payload = codec.tree_projection_value_to_payload(issue)
    assert codec.tree_projection_value_from_payload(type(issue), payload) == issue
    assert (
        codec.tree_projection_value_from_json(
            type(issue), codec.tree_projection_value_to_json(issue)
        )
        == issue
    )


@pytest.mark.parametrize("components", (64, 65, 128))
def test_original_reader_captures_deep_source_without_issue_depth_narrowing(
    tmp_path, components
):
    from aware_workspace_runtime.source_observation_io import (
        SourceObservationLimits,
        capture_exact_paths,
        validate_relative_path,
    )

    path = "/".join(["a"] * components)
    assert len(validate_relative_path(path)) == components
    leaf = tmp_path / path
    leaf.parent.mkdir(parents=True)
    body = b"original source body\n"
    leaf.write_bytes(body)
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        assert capture_exact_paths(
            descriptor,
            (path,),
            SourceObservationLimits(
                maximum_files=1, maximum_body_bytes=1024, maximum_total_bytes=1024
            ),
        ) == ((path, body),)
    finally:
        os.close(descriptor)
    observed = issue_path_value("effect_paths", path)
    assert (
        codec.tree_projection_value_from_json(
            type(observed), codec.tree_projection_value_to_json(observed)
        )
        == observed
    )


@pytest.mark.parametrize("bytes_count", (1024, 1025))
def test_shared_c_utf8_byte_ceiling_is_not_a_component_count(bytes_count):
    from aware_workspace_sdk import repository_tree_projection_codec as workspace_codec
    from aware_workspace_sdk import (
        repository_tree_projection_values as workspace_values,
    )

    path = "/".join(["a" * (204 + bytes_count - 1024)] + ["a" * 204] * 4)
    assert len(path.encode("utf-8")) == bytes_count
    workspace = workspace_values.WorkspaceTreeFileIntent(
        path, "CREATE", "source.py", 0o644
    )
    issue = issue_path_value("effect_paths", path)
    if bytes_count == 1024:
        workspace_codec.repository_tree_projection_value_to_json(workspace)
        codec.tree_projection_value_to_json(issue)
    else:
        with pytest.raises(workspace_codec.WorkspaceTreeProjectionValueError):
            workspace_codec.repository_tree_projection_value_to_json(workspace)
        with pytest.raises(codec.IssueTreeProjectionValueError):
            codec.tree_projection_value_to_json(issue)


@pytest.mark.parametrize("bad", (True, 1.0, "1", None, -1, 2**64))
@pytest.mark.parametrize("field", ("process_id", "thread_id", "transition_count"))
def test_integer_coordinates_cannot_be_coerced(field, bad):
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            dataclasses.replace(
                sample(values.IssueTreeBindingObservation), **{field: bad}
            )
        )


@pytest.mark.parametrize("bad", ([], [1], [1, 2, 3], [True, 2], [1.0, 2], [1, -1]))
def test_identity_is_exact_two_nonnegative_integers(bad):
    payload = codec.tree_projection_value_to_payload(
        sample(values.IssueTreeBindingObservation)
    )
    payload["target_root_identity"] = bad
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_payload(
            values.IssueTreeBindingObservation, payload
        )


@pytest.mark.parametrize("bad", (True, 1, "false", None))
def test_no_portable_observation_can_advertise_retry_permission(bad):
    value = dataclasses.replace(
        sample(values.IssueTreeAdmissionObservation), authorizes_retry=bad
    )
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(value)


@pytest.mark.parametrize("field", ("operation_ref", "profile"))
@pytest.mark.parametrize(
    "bad", ("protocol_specification_setup_v1", "repository_publication", "unknown", "")
)
def test_fixed_tree_purpose_cannot_reuse_other_admission_profiles(field, bad):
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            dataclasses.replace(
                sample(values.IssueTreeProjectionRequest), **{field: bad}
            )
        )


@pytest.mark.parametrize(
    "source",
    (
        "NaN",
        "Infinity",
        "-Infinity",
        "1e999",
        "1.0",
        "{}",
        "[]",
        "null",
        '{"x":1,"x":2}',
    ),
)
def test_invalid_json_refuses_before_provider_or_sdk_operation(source):
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_json(
            values.IssueTreeAdmissionObservation, source
        )


@pytest.mark.parametrize("field", ("phase", "consumption_state", "cleanup_state"))
def test_unknown_states_never_default_to_success_or_no_effect(field):
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            dataclasses.replace(
                sample(values.IssueTreeAdmissionObservation), **{field: "approved"}
            )
        )


def test_nested_duplicates_and_nonfinite_fields_refuse():
    value = sample(values.IssueTreeAdmissionObservation)
    source = codec.tree_projection_value_to_json(value)
    duplicate = source.replace('"process_id":17', '"process_id":17,"process_id":17')
    assert source != duplicate
    with pytest.raises(codec.IssueTreeProjectionValueError, match="duplicate"):
        codec.tree_projection_value_from_json(type(value), duplicate)
    overflow = source.replace('"process_id":17', '"process_id":1e999')
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_json(type(value), overflow)


def test_missing_nested_binding_fields_and_malformed_resources_refuse():
    observed = codec.tree_projection_value_to_payload(
        sample(values.IssueTreeAdmissionObservation)
    )
    del observed["binding"]["physical_preparation_ref"]
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_payload(
            values.IssueTreeAdmissionObservation, observed
        )
    cleanup = codec.tree_projection_value_to_payload(
        sample(values.IssueTreeAdmissionCleanup)
    )
    cleanup["resources"] = [None]
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_from_payload(
            values.IssueTreeAdmissionCleanup, cleanup
        )


def test_budget_refuses_direct_inputs_before_copying_and_matches_json_gate(monkeypatch):
    request = sample(values.IssueTreeProjectionRequest)
    payload = codec.tree_projection_value_to_payload(request)
    source = codec.tree_projection_value_to_json(request)
    monkeypatch.setattr(codec, "MAXIMUM_METADATA_BYTES", 20)
    for call in (
        lambda: codec.tree_projection_value_to_payload(request),
        lambda: codec.tree_projection_value_from_payload(type(request), payload),
        lambda: codec.tree_projection_value_from_json(type(request), source),
    ):
        with pytest.raises(codec.IssueTreeProjectionValueError, match="ceiling"):
            call()


def test_native_budget_refuses_before_detached_record_allocation(monkeypatch):
    request = sample(values.IssueTreeProjectionRequest)
    monkeypatch.setattr(codec, "MAXIMUM_METADATA_BYTES", 20)

    def forbidden(*args, **kwargs):
        raise AssertionError("record allocation before budget qualification")

    monkeypatch.setattr(codec, "_record", forbidden)
    with pytest.raises(codec.IssueTreeProjectionValueError, match="ceiling"):
        codec.tree_projection_value_to_payload(request)


def test_fixed_guard_digest_and_transition_ceiling_are_exact():
    value = sample(values.IssueTreeProjectionRequest)
    for bad in ("a" * 64, "sha256:" + "A" * 64, "sha256:" + "g" * 64):
        with pytest.raises(codec.IssueTreeProjectionValueError):
            codec.tree_projection_value_to_payload(
                dataclasses.replace(value, expected_issue_source_sha256=bad)
            )
    bound = sample(values.IssueTreeBindingObservation)
    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            dataclasses.replace(bound, transition_count=8193)
        )


def test_cycle_incomplete_instance_and_subclasses_are_typed_refusals():
    payload = codec.tree_projection_value_to_payload(
        sample(values.IssueTreeAdmissionCleanup)
    )
    payload["diagnostics"] = [payload]
    with pytest.raises(codec.IssueTreeProjectionValueError, match="cyclic"):
        codec.tree_projection_value_from_payload(
            values.IssueTreeAdmissionCleanup, payload
        )
    incomplete = object.__new__(values.IssueTreeProjectionRequest)
    with pytest.raises(codec.IssueTreeProjectionValueError, match="incomplete"):
        codec.tree_projection_value_to_payload(incomplete)

    class Subclass(values.IssueTreeProjectionRequest):
        pass

    with pytest.raises(codec.IssueTreeProjectionValueError):
        codec.tree_projection_value_to_payload(
            Subclass("issue", "sha256:" + "a" * 64, "actor", "evidence", "intent")
        )


def test_canonical_source_manifest_and_original_v0_are_unchanged():
    manifest = tomllib.loads((AUTHORED / "aware.sdk.toml").read_text())
    assert "*.aware" in manifest["build"]["include_paths"]
    capture = json.loads(
        (
            ROOT
            / "docs/reports/issue-repository-tree-projection-preimages-20261012.json"
        ).read_text()
    )
    pin = next(
        pin
        for pin in capture["preimages"]
        if pin["path"].endswith("/aware_issue_sdk/source_projection.py")
    )
    # The value-only cut's whole-file guard is superseded by the admitted C
    # runtime extension. Preserve every original v0 byte as the exact prefix,
    # and continue verifying the historical pin rather than rewriting it.
    predecessor = subprocess.check_output(
        ["git", "show", f"{capture['capture_revision']}:{pin['path']}"], cwd=ROOT
    )
    assert hashlib.sha256(predecessor).hexdigest() == pin["committed_sha256"]
    assert (ROOT / pin["path"]).read_bytes().startswith(predecessor)
    assert not any(
        hasattr(values, name)
        for name in ("admit_tree_projection", "consume_tree_projection_admission")
    )
    for module in (values, codec):
        assert all(hasattr(module, name) for name in module.__all__)


def test_fresh_value_imports_do_not_select_runtime_physical_or_service_owners():
    source = """
import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith(("aware_workspace", "aware_file_system", "aware_issue_operational_runtime", "aware_issue_fs_adapter", "aware_issue_service")):
            raise AssertionError("excluded owner import: "+fullname)
sys.meta_path.insert(0,Block())
from aware_issue_sdk import repository_tree_projection_values as v
from aware_issue_sdk import repository_tree_projection_codec as c
assert c.tree_projection_value_from_json(v.IssueTreeProjectionRequest,c.tree_projection_value_to_json(v.IssueTreeProjectionRequest("issue","sha256:"+"a"*64,"actor","evidence","intent"))).client_intent_id=="intent"
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", source],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture(scope="module")
def performance_predecessor_codec():
    """Use the committed admission preimage, preserving prior vector tests."""
    import importlib.util

    capture = json.loads(
        (
            ROOT
            / "docs/reports/issue-tree-path-observation-performance-inputs-20261013.json"
        ).read_text()
    )
    pin = next(
        row
        for row in capture["preimages"]
        if row["path"].endswith("/repository_tree_projection_codec.py")
    )
    source = subprocess.check_output(
        ["git", "show", f"{capture['capture_revision']}:{pin['path']}"], cwd=ROOT
    )
    assert hashlib.sha256(source).hexdigest() == pin["sha256"]
    name = "aware_issue_sdk._performance_predecessor_codec"
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(name, loader=None)
    )
    exec(compile(source, pin["path"], "exec"), module.__dict__)  # noqa: S102 -- hash-verified committed predecessor
    return module


@pytest.mark.parametrize(
    "value",
    [chr(code) for code in range(256)]
    + [
        "é",
        "e\u0301",
        "漢",
        "🙂",
        "\ud800",
        "a" * 1024,
        "a" * 1025,
        "é" * 512,
        "é" * 513,
    ],
)
def test_performance_text_and_path_predicates_match_original(
    value, performance_predecessor_codec
):
    for text in (value, "a" + value + "b", "a/" + value + "/b"):
        for name in ("_text", "_path"):
            outcomes = []
            for module in (performance_predecessor_codec, codec):
                try:
                    getattr(module, name)(text, "value")
                except module.IssueTreeProjectionValueError as error:
                    outcomes.append((False, str(error)))
                else:
                    outcomes.append((True, None))
            assert outcomes[0] == outcomes[1]


@pytest.mark.parametrize("record", RECORDS)
def test_owner_clone_matches_original_and_revalidates_each_invocation(
    record, performance_predecessor_codec
):
    from aware_issue_operational_runtime.source_projection import _tree_clone

    value = sample(record)
    predecessor = performance_predecessor_codec.tree_projection_value_from_payload(
        record, performance_predecessor_codec.tree_projection_value_to_payload(value)
    )
    cloned = _tree_clone(value)
    assert cloned == predecessor and cloned is not value
    assert codec.tree_projection_value_to_json(
        cloned
    ) == performance_predecessor_codec.tree_projection_value_to_json(predecessor)
    if record is values.IssueTreeAdmissionObservation:
        assert cloned.binding is not value.binding
        object.__setattr__(value.binding, "effect_paths", ("../changed",))
    elif record is values.IssueTreeAdmissionCleanup:
        assert cloned.resources[0] is not value.resources[0]
        object.__setattr__(value.resources[0], "diagnostics", ("\x00",))
    else:
        object.__setattr__(value, dataclasses.fields(record)[0].name, "\x00")
    with pytest.raises(codec.IssueTreeProjectionValueError):
        _tree_clone(value)
    # A failed source mutation cannot alter the already detached observation.
    assert codec.tree_projection_value_to_json(
        cloned
    ) == performance_predecessor_codec.tree_projection_value_to_json(predecessor)


@pytest.mark.parametrize("shared", (False, True))
def test_owner_clone_charges_every_logical_occurrence_before_restoring(
    monkeypatch, shared
):
    from aware_issue_operational_runtime.source_projection import _tree_clone

    resource = sample(values.IssueTreeResourceCleanup)
    value = dataclasses.replace(
        sample(values.IssueTreeAdmissionCleanup),
        resources=(resource, resource if shared else dataclasses.replace(resource)),
    )
    ordinary = codec.tree_projection_value_to_json(value)
    monkeypatch.setattr(codec, "MAXIMUM_METADATA_BYTES", len(ordinary.encode()) - 1)
    with pytest.raises(codec.IssueTreeProjectionValueError, match="ceiling"):
        _tree_clone(value)
    monkeypatch.setattr(codec, "MAXIMUM_METADATA_BYTES", len(ordinary.encode()))
    assert codec.tree_projection_value_to_json(_tree_clone(value)) == ordinary


def test_owner_clone_rejects_malformed_native_before_detached_restoration():
    from aware_issue_operational_runtime.source_projection import _tree_clone

    class ForeignString(str):
        def encode(self, *args, **kwargs):
            raise AssertionError("foreign string behavior")

    value = dataclasses.replace(
        sample(values.IssueTreeProjectionRequest),
        client_intent_id=ForeignString("intent"),
    )
    with pytest.raises(codec.IssueTreeProjectionValueError):
        _tree_clone(value)
