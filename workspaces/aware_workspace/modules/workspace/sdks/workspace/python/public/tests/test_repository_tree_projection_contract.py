"""Frozen authored tree parity and strict portable evidence; no tree effects."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields, replace
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
from aware_workspace_sdk import repository_tree_projection_values as v
from aware_workspace_sdk.repository_source_projection_values import (
    RepositoryObservationCoordinate,
)
from aware_workspace_sdk.repository_tree_projection_codec import (
    WorkspaceTreeProjectionValueError,
    repository_tree_projection_value_clone,
    repository_tree_projection_value_digest,
    repository_tree_projection_value_from_json,
    repository_tree_projection_value_from_payload,
    repository_tree_projection_value_to_json,
    repository_tree_projection_value_to_payload,
    repository_tree_projection_value_validate_equal,
)
from aware_workspace_sdk.repository_workflow_source_values import (
    MAX_WORKFLOW_SOURCE_BYTES,
    MAX_WORKFLOW_SOURCE_FILES,
    WorkspaceWorkflowSourceBinding,
)
from aware_workspace_sdk.repository_workflow_values import WorkspaceWorkflowMarker
from tree_sitter_aware.neutral_ir import parse_neutral_aware_source

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
)
SDK = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace"


@pytest.mark.parametrize(
    "kind,mode,accepted",
    [
        ("create", 0o600, True),
        ("create", 0o644, True),
        ("create", 0o755, True),
        ("mode", 0o600, False),
        ("create", 0o777, False),
        ("mode", 0o755, True),
    ],
)
def test_private_scratch_mode_preserves_legacy_and_explicit_owner_footprint(
    kind, mode, accepted
):
    value = v.WorkspaceTreeScratchEffect(
        ".aware-tree-private", "replacement_body", 0, kind, mode
    )
    if accepted:
        assert repository_tree_projection_value_clone(value) == value
    else:
        with pytest.raises(WorkspaceTreeProjectionValueError):
            repository_tree_projection_value_clone(value)


FROZEN = ROOT / "docs/reports/workspace-repository-tree-projection-inputs-20261011.json"
EMPTY = v.WorkspaceTreeEntryPin(False, *([None] * 8))
DIGEST = "sha256:" + hashlib.sha256(b"new").hexdigest()
OLD_DIGEST = "sha256:" + hashlib.sha256(b"old").hexdigest()
REF = "sha256:" + "0" * 64
CLEANUP = v.WorkspaceTreeProjectionCleanupObservation(
    None, (), (), "completed", True, ()
)


def source():
    return WorkspaceWorkflowSourceBinding(
        REF,
        "workflow:1",
        "attempt:1",
        REF,
        "generation:1",
        "codex-fixture",
        1,
        2,
        REF,
        REF,
        "/source",
        "/target",
        (1, 2),
        (3, 4),
        "a" * 40,
        "portable",
        REF,
        (WorkspaceWorkflowMarker("python_version", "3.12"),),
        REF,
        "aware.workspace.package-source-checkout.v2",
        REF,
        1,
        1,
        3,
        MAX_WORKFLOW_SOURCE_FILES,
        MAX_WORKFLOW_SOURCE_BYTES,
        "refs/heads/main",
        None,
    )


def pin(*, directory=False):
    return v.WorkspaceTreeEntryPin(
        True,
        3,
        4,
        0 if directory else 3,
        1,
        1,
        0o755 if directory else 0o644,
        2 if directory else 1,
        None if directory else OLD_DIGEST,
    )


def request(*, kind="CREATE", mode=0o644):
    return v.WorkspaceTreeProjectionRequest(
        "workflow:1",
        "layout:1",
        "invocation:1",
        source(),
        (
            v.WorkspaceTreeFileIntent(
                "pkg/output.py",
                kind,
                None if kind == "DELETE" else "public/source.py",
                None if kind == "DELETE" else mode,
            ),
        ),
        (v.WorkspaceTreeAncestorIntent("pkg", "create", 0o755),),
        "descriptor_walk_v1",
        v.DEFAULT_TREE_LIMITS,
    )


def binding(*, kind="CREATE", mode=0o644, limits=v.DEFAULT_TREE_LIMITS):
    deleted = kind == "DELETE"
    row = v.WorkspaceTreeFileTransition(
        "pkg/output.py",
        kind,
        None if deleted else "public/source.py",
        None if deleted else "package/source.py",
        EMPTY if kind == "CREATE" else pin(),
        None if kind == "CREATE" else "body:old",
        None if deleted else "body:new",
        None if deleted else DIGEST,
        None if deleted else 3,
        None if deleted else mode,
    )
    value = v.WorkspaceTreeProjectionBinding(
        "plan:1",
        "provider:1",
        "generation:1",
        "codex-fixture",
        1,
        2,
        REF,
        (3, 4),
        source(),
        RepositoryObservationCoordinate(REF, "epoch:1", 0, REF, "policy:1", "1"),
        "workflow:1",
        "layout:1",
        "invocation:1",
        REF,
        "physical:1",
        "request:1",
        REF,
        REF,
        2,
        (row,),
        (v.WorkspaceTreeAncestorTransition("pkg", "create", EMPTY, 0o755),),
        (),
        ("pkg", "pkg/output.py"),
        (),
        limits,
        "pending",
    )
    # Independent stdlib construction of the accepted canonical commitment.
    payload = asdict(value)
    del payload["binding_ref"]
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return replace(
        value, binding_ref="sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
    )


def observation():
    bound = binding()
    return v.WorkspaceTreeProjectionObservation(
        "result:1",
        bound,
        None,
        (),
        0,
        0,
        "prepared",
        (),
        "not_attempted",
        "not_attempted",
        "not_attempted",
        "retained",
        "not_attempted",
        "none",
        CLEANUP,
        True,
        (),
    )


def examples():
    bound = binding()
    before = pin()
    effect = v.WorkspaceTreePhysicalEffect(
        "effect:1",
        0,
        "pkg",
        "ancestor",
        "directory_create",
        "applied",
        None,
        (3, 4),
        None,
        None,
        None,
        0,
        None,
        0o755,
        True,
        None,
    )
    receipt = v.WorkspaceTreeTransitionReceipt(
        bound.binding_ref,
        "invocation:1",
        "consumption:1",
        "physical:1",
        0,
        "pkg",
        "directory_create",
        (effect,),
        EMPTY,
        pin(directory=True),
        None,
        None,
        None,
        "applied",
        "complete",
        True,
        "matched",
        "retained",
        "persisted",
        (),
        CLEANUP,
    )
    return (
        request().files[0],
        request().ancestors[0],
        request(),
        v.DEFAULT_TREE_LIMITS,
        before,
        bound.files[0],
        bound.ancestors[0],
        v.WorkspaceTreeScratchEffect(
            "pkg/.reserved", "replacement_body", 1, "create", 0o644
        ),
        bound,
        v.WorkspaceTreeProjectionPlanObservation(bound, "prepared", CLEANUP, True, ()),
        effect,
        receipt,
        v.WorkspaceTreeResourceCleanup(
            "resource:1", "descriptor", None, "owned", True, "completed", ()
        ),
        CLEANUP,
        observation(),
        v.WorkspaceTreeProjectionResolution(
            observation(), "historical_descriptive", False
        ),
        v.WorkspaceTreeProjectionRefusalEvidence(
            "stale_source", observation(), CLEANUP, ("source drift",), False
        ),
    )


@pytest.mark.parametrize("example", examples(), ids=lambda item: type(item).__name__)
def test_all_closed_values_canonical_roundtrip_and_detachment(example):
    text = repository_tree_projection_value_to_json(example)
    decoded = repository_tree_projection_value_from_json(type(example), text)
    assert decoded == example and decoded is not example
    assert repository_tree_projection_value_to_json(decoded) == text
    assert repository_tree_projection_value_clone(example) == example
    payload = repository_tree_projection_value_to_payload(example)
    assert text == json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    assert (
        repository_tree_projection_value_digest(example)
        == "sha256:" + hashlib.sha256(text.encode()).hexdigest()
    )


def test_actual_parser_and_python_match_all_frozen_fields_and_enums():
    frozen = json.loads(FROZEN.read_text())["joined_freeze_candidate"]
    path = SDK / "aware/repository_tree_projection_values.aware"
    parsed = parse_neutral_aware_source(path.read_text(), source_path=str(path))
    nodes = list(parsed.root.children)

    def walk(node):
        yield node
        for child in node.children:
            yield from walk(child)

    assert not any(n.kind in ("ERROR", "MISSING") for n in walk(parsed.root))
    classes = {
        next(n.text for n in node.children if n.field_name == "name"): node
        for node in nodes
        if node.kind == "class_def"
    }
    assert set(classes) == set(frozen["schemas"])
    for cls in v.TREE_VALUE_TYPES:
        expected = frozen["schemas"][cls.__name__]
        assert [field.name for field in fields(cls)] == list(expected["fields"])
        assert v.TREE_SCHEMA_IDS[cls] == expected["schema_id"]
        definitions = {
            next(n.text for n in item.children if n.field_name == "name"): next(
                n.text for n in item.children if n.field_name == "type"
            )
            for item in classes[cls.__name__].children
            if item.kind == "attr_def"
        }

        def aware_type(annotation):
            if annotation.endswith(" | None"):
                return aware_type(annotation[:-7]) + "?"
            if annotation.startswith("tuple["):
                return aware_type(annotation[6:-6]) + "[]"
            return {"str": "String", "int": "Int", "bool": "Bool"}.get(
                annotation, annotation
            )

        assert definitions == {
            name: aware_type(kind) for name, kind in expected["fields"].items()
        }
        # get_type_hints resolves every annotation, including retained sibling types.
        assert set(get_type_hints(cls)) == set(expected["fields"])
    enums = {
        next(n.text for n in node.children if n.field_name == "name"): [
            n.text for n in node.children if n.kind == "enum_value_def"
        ]
        for node in nodes
        if node.kind == "enum_def"
    }
    for name, members in frozen["enums"].items():
        assert list(get_args(getattr(v, name))) == members
        assert enums[name] == members


@pytest.mark.parametrize("kind", ["CREATE", "UPDATE", "DELETE"])
def test_all_three_file_kinds_have_lawful_portable_vectors(kind):
    bound = binding(kind=kind)
    assert (
        repository_tree_projection_value_from_json(
            type(bound), repository_tree_projection_value_to_json(bound)
        )
        == bound
    )


def test_map_only_mode_change_and_equal_byte_mode_are_distinct_intents():
    base = binding(kind="UPDATE")
    row = replace(base.files[0], successor_digest=OLD_DIGEST)
    normal = replace(
        request(kind="UPDATE"),
        files=(replace(request(kind="UPDATE").files[0], requested_mode=0o644),),
    )
    executable = replace(
        normal, files=(replace(normal.files[0], requested_mode=0o755),)
    )
    assert row.before.content_digest == row.successor_digest
    assert repository_tree_projection_value_digest(
        normal
    ) != repository_tree_projection_value_digest(executable)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/absolute",
        "../out",
        "a/../out",
        "a//out",
        "a/",
        "a\\b",
        "a\x00b",
        "e\u0301",
        "a\u200db",
        "a" * 256,
        "\ud800",
    ],
)
def test_noncanonical_paths_refuse(path):
    value = v.WorkspaceTreeFileIntent(path, "CREATE", "public/source.py", 0o644)
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(value)


@pytest.mark.parametrize("mode", [None, 0, 0o600, 0o777, True, -1, 2**64 + 1])
def test_successor_modes_are_exact_and_explicit(mode):
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(
            v.WorkspaceTreeFileIntent("out", "CREATE", "source", mode)
        )


@pytest.mark.parametrize(
    "change",
    [
        {"files": []},
        {"confinement_profile": "continuous_root_v1"},
        {"ancestors": []},
        {"workflow_ref": "foreign"},
        {"limits": {"maximum_file_transitions": True}},
        {"files": [{"path": "out"}]},
        {"unexpected": None},
    ],
)
def test_malformed_request_and_omitted_required_fields_refuse(change):
    payload = repository_tree_projection_value_to_payload(request())
    payload.update(change)
    if change == {"files": []}:
        # An explicit directory-only request remains legal; there is no implicit prune.
        assert (
            repository_tree_projection_value_from_payload(
                v.WorkspaceTreeProjectionRequest, payload
            ).files
            == ()
        )
    else:
        with pytest.raises(WorkspaceTreeProjectionValueError):
            repository_tree_projection_value_from_payload(
                v.WorkspaceTreeProjectionRequest, payload
            )


@pytest.mark.parametrize(
    "field",
    [
        "binding_ref",
        "request_digest",
        "provider_generation",
        "execution_id",
        "target_root_identity",
        "files",
        "effect_paths",
    ],
)
def test_binding_commitment_and_correspondence_reject_substitution(field):
    payload = repository_tree_projection_value_to_payload(binding())
    if field == "target_root_identity":
        payload[field] = [9, 9]
    elif field == "files":
        payload[field][0]["requested_mode"] = 0o755
    elif field == "effect_paths":
        payload[field].append("foreign")
    else:
        payload[field] = (
            ("sha256:" + "1" * 64)
            if field.endswith("digest") or field == "binding_ref"
            else "foreign"
        )
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_from_payload(
            v.WorkspaceTreeProjectionBinding, payload
        )


@pytest.mark.parametrize("field", list(asdict(v.DEFAULT_TREE_LIMITS)))
@pytest.mark.parametrize("bad", [0, -1, True, 2**64 + 1])
def test_every_limit_rejects_empty_or_hostile_numeric_value(field, bad):
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(
            replace(v.DEFAULT_TREE_LIMITS, **{field: bad})
        )


def test_combined_budget_and_original_body_quota_are_conjunctive():
    for limits in (
        replace(v.DEFAULT_TREE_LIMITS, maximum_combined_body_bytes=5),
        replace(v.DEFAULT_TREE_LIMITS, maximum_retained_bodies=1),
        replace(v.DEFAULT_TREE_LIMITS, maximum_file_bytes=2),
    ):
        with pytest.raises(WorkspaceTreeProjectionValueError):
            repository_tree_projection_value_to_payload(
                binding(kind="UPDATE", limits=limits)
            )


def test_requested_metadata_limit_applies_before_admission():
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(
            replace(
                request(),
                limits=replace(v.DEFAULT_TREE_LIMITS, maximum_metadata_bytes=1),
            )
        )


@pytest.mark.parametrize("kind", ["request", "binding"])
def test_order_duplicates_and_ancestor_collision_reject(kind):
    value = request() if kind == "request" else binding()
    malformed = replace(value, files=(value.files[0], value.files[0]))
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(malformed)
    row = replace(value.files[0], path="pkg")
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(replace(value, files=(row,)))


@pytest.mark.parametrize(
    "name", ["device", "inode", "size_bytes", "mode", "content_digest"]
)
def test_absence_cannot_invent_stat_or_body_evidence(name):
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(
            replace(EMPTY, **{name: REF if name == "content_digest" else 1})
        )


@pytest.mark.parametrize(
    "text",
    [
        "{} ",
        "{}\n",
        '{"exists":false,"exists":false}',
        '{"exists":NaN}',
        "[" * 1000 + "]" * 1000,
        "{",
        "null",
        "[]",
        '"\\ud800"',
    ],
)
def test_bad_or_noncanonical_json_rejects(text):
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_from_json(v.WorkspaceTreeEntryPin, text)


def test_arbitrary_class_native_bytes_and_tuple_subclasses_are_behavior_free():
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("hostile value executed")

    class HostileTuple(tuple):
        def __iter__(self):
            calls.append("iter")
            raise AssertionError("hostile sequence executed")

    for value in (
        Hostile(),
        b"native body",
        replace(request(), files=HostileTuple(request().files)),
    ):
        with pytest.raises(WorkspaceTreeProjectionValueError):
            repository_tree_projection_value_to_json(value)
    assert calls == []


def test_slot_replacement_rejects_before_descriptor_dispatch(monkeypatch):
    calls = []

    class Poison:
        def __get__(self, receiver, owner):
            calls.append("descriptor")
            raise AssertionError("foreign descriptor executed")

    value = v.WorkspaceTreeFileIntent("out", "CREATE", "source", 0o644)
    monkeypatch.setattr(v.WorkspaceTreeFileIntent, "path", Poison())
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(value)
    assert calls == []


def test_detached_nested_payload_cannot_mutate_original_binding():
    original = binding()
    payload = repository_tree_projection_value_to_payload(original)
    payload["source_binding"]["marker_environment"][0]["value"] = "changed"
    assert original.source_binding.marker_environment[0].value == "3.12"
    assert repository_tree_projection_value_clone(original) == original


@pytest.mark.parametrize(
    "retry_type",
    [v.WorkspaceTreeProjectionResolution, v.WorkspaceTreeProjectionRefusalEvidence],
)
def test_historical_receipts_cannot_authorize_retry(retry_type):
    value = (
        examples()[-2]
        if retry_type is v.WorkspaceTreeProjectionResolution
        else examples()[-1]
    )
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(replace(value, authorizes_retry=True))


def test_substituted_or_reordered_receipts_do_not_form_an_original_prefix():
    result = observation()
    receipt = examples()[11]
    malformed = replace(result, receipts=(replace(receipt, ordinal=1),))
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(malformed)
    malformed = replace(result, receipts=(replace(receipt, invocation_ref="foreign"),))
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_json(malformed)


@pytest.mark.parametrize("field", list(asdict(v.DEFAULT_TREE_LIMITS)))
def test_every_limit_refuses_one_above_its_accepted_ceiling(field):
    cap = asdict(v.DEFAULT_TREE_LIMITS)[field]
    with pytest.raises(WorkspaceTreeProjectionValueError, match="ceiling"):
        repository_tree_projection_value_to_payload(
            replace(v.DEFAULT_TREE_LIMITS, **{field: cap + 1})
        )


def test_4096_files_can_exceed_body_quota_before_any_commitment_check():
    base = binding(kind="UPDATE")
    rows = tuple(
        replace(
            base.files[0],
            path=f"file-{i:04}.py",
            before_body_ref=f"before:{i}",
            successor_body_ref=f"after:{i}",
        )
        for i in range(4096)
    )
    value = replace(
        base,
        files=rows,
        ancestors=(),
        transition_count=4096,
        effect_paths=tuple(row.path for row in rows),
    )
    with pytest.raises(WorkspaceTreeProjectionValueError, match="body quota"):
        repository_tree_projection_value_to_payload(value)


@pytest.mark.parametrize("field", ["physical_effects", "error_refs"])
def test_per_receipt_subeffect_and_error_budgets_cannot_expand(field):
    receipt = examples()[11]
    item = receipt.physical_effects[0] if field == "physical_effects" else "error:1"
    with pytest.raises(WorkspaceTreeProjectionValueError, match="collection exceeds"):
        repository_tree_projection_value_to_payload(
            replace(receipt, **{field: (item,) * 17})
        )


def test_nonexact_dictionary_keys_reject_without_foreign_hash_or_equality():
    calls = []

    class Key(str):
        def __hash__(self):
            calls.append("hash")
            return super().__hash__()

        def __eq__(self, other):
            calls.append("eq")
            return super().__eq__(other)

    payload = repository_tree_projection_value_to_payload(EMPTY)
    payload[Key("exists")] = payload.pop("exists")
    calls.clear()
    with pytest.raises(WorkspaceTreeProjectionValueError, match="exact text"):
        repository_tree_projection_value_from_payload(v.WorkspaceTreeEntryPin, payload)
    assert calls == []


def test_original_pre_epoch_timestamps_remain_exact_observation_evidence():
    before = replace(pin(), mtime_ns=-1, ctime_ns=-(2**63))
    text = repository_tree_projection_value_to_json(before)
    assert (
        repository_tree_projection_value_from_json(v.WorkspaceTreeEntryPin, text)
        == before
    )


def test_standalone_transition_also_enforces_the_preimage_ceiling():
    row = binding(kind="UPDATE").files[0]
    row = replace(row, before=replace(row.before, size_bytes=v.MAX_TREE_FILE_BYTES + 1))
    with pytest.raises(WorkspaceTreeProjectionValueError, match="preimage exceeds"):
        repository_tree_projection_value_to_json(row)


def large_cleanup_evidence():
    resources = tuple(
        v.WorkspaceTreeResourceCleanup(
            f"descriptor:{i}",
            "descriptor",
            f"p/{i}",
            "released",
            True,
            "completed",
            (),
        )
        for i in range(5000)
    )
    completed = replace(CLEANUP, resources=resources)
    prior = replace(
        completed,
        resources=(
            replace(resources[0], ownership="owned", cleanup_state="not_attempted"),
            *resources[1:],
        ),
        cleanup_state="not_attempted",
    )
    return v.WorkspaceTreeProjectionRefusalEvidence(
        "cleanup_unknown",
        replace(observation(), cleanup=prior),
        completed,
        (),
        False,
    )


def test_resource_table_preserves_every_row_order_and_prior_disposition():
    original = large_cleanup_evidence()
    payload = repository_tree_projection_value_to_payload(original)
    assert payload["encoding"] == "aware.workspace.tree-cleanup-resource-table.v1"
    assert len(payload["resources"]) == 5001
    text = repository_tree_projection_value_to_json(original)
    assert len(text.encode()) < v.MAX_TREE_METADATA_BYTES
    detached = repository_tree_projection_value_from_json(type(original), text)
    assert detached == original and detached is not original
    assert detached.cleanup.resources is not original.cleanup.resources
    assert detached.observation.cleanup.resources[0].ownership == "owned"
    assert detached.cleanup.resources[0].ownership == "released"
    assert tuple(row.resource_ref for row in detached.cleanup.resources) == tuple(
        row.resource_ref for row in original.cleanup.resources
    )
    assert repository_tree_projection_value_to_json(detached) == text
    assert not detached.authorizes_retry


@pytest.mark.parametrize(
    "poison",
    [
        "encoding",
        "type",
        "extra",
        "unused",
        "range",
        "zero",
        "adjacent",
        "collection",
        "table",
    ],
)
def test_resource_table_rejects_bad_envelope_and_ranges(poison):
    original = large_cleanup_evidence()
    payload = repository_tree_projection_value_to_payload(original)
    ranges = payload["value"]["cleanup"]["resources"]["ranges"]
    if poison == "encoding":
        payload["encoding"] = "foreign"
    elif poison == "type":
        payload["type"] = v.TREE_SCHEMA_IDS[v.WorkspaceTreeEntryPin]
    elif poison == "extra":
        payload["authority"] = True
    elif poison == "unused":
        payload["resources"].append(
            dict(payload["resources"][0], resource_ref="unused")
        )
    elif poison == "range":
        ranges[:] = [[len(payload["resources"]), 1]]
    elif poison == "zero":
        ranges[:] = [[0, 0]]
    elif poison == "adjacent":
        ranges[:] = [[0, 1], [1, 4999]]
    elif poison == "collection":
        ranges[:] = [[0, 5000], [0, 5000]]
    else:
        payload["resources"] = [payload["resources"][0]] * (v.MAX_TREE_RECEIPTS + 1)
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_from_payload(type(original), payload)


def test_resource_table_expansion_budget_rejects_before_unbounded_allocation(
    monkeypatch,
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    original = large_cleanup_evidence()
    payload = repository_tree_projection_value_to_payload(original)
    monkeypatch.setattr(codec, "_MAX_RESOURCE_REFERENCES", 6000)
    with pytest.raises(WorkspaceTreeProjectionValueError, match="expansion"):
        repository_tree_projection_value_from_payload(type(original), payload)


def test_resource_envelope_foreign_keys_and_containers_have_zero_dispatch():
    calls = []

    class Key(str):
        def __eq__(self, other):
            calls.append("equal")
            return False

        __hash__ = str.__hash__

    payload = repository_tree_projection_value_to_payload(large_cleanup_evidence())
    payload[Key("foreign")] = True
    calls.clear()
    with pytest.raises(WorkspaceTreeProjectionValueError, match="exact text"):
        repository_tree_projection_value_from_payload(
            v.WorkspaceTreeProjectionRefusalEvidence, payload
        )
    assert not calls


def test_small_tree_metadata_keeps_original_bare_canonical_wire():
    assert "encoding" not in repository_tree_projection_value_to_payload(observation())
    assert repository_tree_projection_value_to_json(CLEANUP) == json.dumps(
        asdict(CLEANUP), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def resource_occurrence_value(resource_count=5000, *, shared=True, receipt_count=1000):
    original = binding()
    files = tuple(replace(original.files[0], path=f"f{i:04d}") for i in range(1000))
    bound = replace(
        original,
        files=files,
        ancestors=(),
        effect_paths=tuple(row.path for row in files),
        transition_count=1000,
    )
    commitment = asdict(bound)
    del commitment["binding_ref"]
    text = json.dumps(
        commitment, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    bound = replace(
        bound, binding_ref="sha256:" + hashlib.sha256(text.encode()).hexdigest()
    )
    cleanup = large_cleanup_evidence().cleanup
    cleanup = replace(cleanup, resources=cleanup.resources[:resource_count])
    prototype = next(
        row for row in examples() if type(row) is v.WorkspaceTreeTransitionReceipt
    )
    receipts = tuple(
        replace(
            prototype,
            binding_ref=bound.binding_ref,
            ordinal=i,
            path=row.path,
            kind="CREATE",
            before=EMPTY,
            after=pin(),
            physical_effects=(),
            cleanup=cleanup if shared else replace(cleanup),
        )
        for i, row in enumerate(files[:receipt_count])
    )
    return replace(
        observation(),
        binding=bound,
        receipts=receipts,
        completed_prefix=receipt_count,
        pending_ordinal=None,
        phase="complete",
        cleanup=cleanup,
    )


@pytest.mark.parametrize("shared", [False, True])
@pytest.mark.parametrize("resource_count", [1000, 5000])
def test_logical_expansion_is_independent_of_snapshot_identity(shared, resource_count):
    original = resource_occurrence_value(resource_count, shared=shared)
    if resource_count == 5000:
        with pytest.raises(WorkspaceTreeProjectionValueError, match="expansion"):
            repository_tree_projection_value_to_json(original)
    else:
        text = repository_tree_projection_value_to_json(original)
        detached = repository_tree_projection_value_from_json(type(original), text)
        assert detached == original
        assert repository_tree_projection_value_to_json(detached) == text


@pytest.mark.parametrize("shared_payload", [False, True])
def test_payload_aliases_cannot_bypass_logical_expansion(shared_payload):
    original = resource_occurrence_value(receipt_count=800)
    payload = repository_tree_projection_value_to_payload(original)
    node = payload["value"]
    for ordinal in range(800, 1000):
        node["receipts"].append(
            dict(node["receipts"][0], ordinal=ordinal, path=f"f{ordinal:04d}")
        )
    node["completed_prefix"] = 1000
    if shared_payload:
        for row in node["receipts"]:
            row["cleanup"] = node["cleanup"]
    with pytest.raises(WorkspaceTreeProjectionValueError, match="expansion"):
        repository_tree_projection_value_from_payload(type(original), payload)


@pytest.mark.parametrize("shared", [False, True])
def test_nested_memo_cost_counts_exact_boundary_once_per_occurrence(
    monkeypatch, shared
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    original = large_cleanup_evidence()
    cleanup = replace(original.cleanup, resources=original.cleanup.resources[:4])
    original = replace(
        original,
        cleanup=cleanup,
        observation=replace(
            original.observation, cleanup=cleanup if shared else replace(cleanup)
        ),
    )
    # Force the compact path with a small declared threshold, retaining the real
    # cost logic without allocating millions of rows in a boundary control.
    monkeypatch.setattr(codec.values, "MAX_TREE_RECEIPTS", 7)
    monkeypatch.setattr(codec, "_MAX_RESOURCE_REFERENCES", 8)
    text = repository_tree_projection_value_to_json(original)
    assert repository_tree_projection_value_from_json(type(original), text) == original
    monkeypatch.setattr(codec, "_MAX_RESOURCE_REFERENCES", 7)
    with pytest.raises(WorkspaceTreeProjectionValueError, match="expansion"):
        repository_tree_projection_value_to_json(original)


@pytest.mark.parametrize("example", examples(), ids=lambda value: type(value).__name__)
@pytest.mark.parametrize("same_object", [False, True])
def test_equality_validation_matches_original_codec_for_every_value(
    example, same_object
):
    expected = (
        example if same_object else repository_tree_projection_value_clone(example)
    )
    before = repository_tree_projection_value_to_json(example)
    assert (
        repository_tree_projection_value_validate_equal(
            example, expected_value=expected
        )
        is None
    )
    assert repository_tree_projection_value_to_json(example) == before


@pytest.mark.parametrize("side", ["value", "expected"])
def test_equality_rejects_genuine_difference_and_invalid_commitment(side):
    first, second = request(), replace(request(), layout_ref="other-layout")
    assert repository_tree_projection_value_clone(first) != second
    with pytest.raises(WorkspaceTreeProjectionValueError, match="values differ"):
        repository_tree_projection_value_validate_equal(first, expected_value=second)
    genuine = binding()
    poisoned = replace(genuine, binding_ref=REF)
    with pytest.raises(WorkspaceTreeProjectionValueError, match="commitment"):
        repository_tree_projection_value_validate_equal(
            poisoned if side == "value" else genuine,
            expected_value=poisoned if side == "expected" else genuine,
        )


@pytest.mark.parametrize("side", ["value", "expected"])
@pytest.mark.parametrize("poison", ["foreign", "sequence", "primitive", "missing"])
def test_equality_rejects_hostile_values_before_any_behavior(side, poison):
    calls = []

    class Hostile:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign attribute dispatch")

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("foreign equality dispatch")

    class HostileTuple(tuple):
        def __iter__(self):
            calls.append("iteration")
            raise AssertionError("foreign iteration dispatch")

    genuine = request()
    if poison == "foreign":
        bad = Hostile()
    elif poison == "sequence":
        bad = replace(genuine, files=HostileTuple(genuine.files))
    elif poison == "primitive":
        bad = replace(genuine, layout_ref=Hostile())
    else:
        bad = object.__new__(type(genuine))
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_validate_equal(
            bad if side == "value" else genuine,
            expected_value=bad if side == "expected" else genuine,
        )
    assert calls == []


def test_equality_revalidates_identical_values_and_changed_slot_descriptors(
    monkeypatch,
):
    calls = []
    original = request()
    assert (
        repository_tree_projection_value_validate_equal(
            original, expected_value=original
        )
        is None
    )
    object.__setattr__(original.files[0], "requested_mode", 0o777)
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_validate_equal(
            original, expected_value=original
        )

    class Poison:
        def __get__(self, receiver, owner):
            calls.append("descriptor")
            raise AssertionError("foreign descriptor dispatch")

    original = request()
    monkeypatch.setattr(v.WorkspaceTreeFileIntent, "path", Poison())
    with pytest.raises(WorkspaceTreeProjectionValueError, match="descriptor"):
        repository_tree_projection_value_validate_equal(
            original, expected_value=original
        )
    assert calls == []


@pytest.mark.parametrize("side", ["value", "expected"])
@pytest.mark.parametrize("shared", [False, True])
def test_equality_enforces_original_logical_expansion_on_both_sides(side, shared):
    genuine = resource_occurrence_value(1000)
    excessive = resource_occurrence_value(5000, shared=shared)
    with pytest.raises(WorkspaceTreeProjectionValueError, match="expansion"):
        repository_tree_projection_value_validate_equal(
            excessive if side == "value" else genuine,
            expected_value=excessive if side == "expected" else genuine,
        )


def test_equality_keeps_requested_wire_budget_and_allocates_no_detached_records(
    monkeypatch,
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    original, expected = binding(), binding()
    original_convert = codec._convert
    decoded = []

    def count_decode(*args, **kwargs):
        if kwargs.get("decode"):
            decoded.append(args[0])
        return original_convert(*args, **kwargs)

    monkeypatch.setattr(codec, "_convert", count_decode)
    assert repository_tree_projection_value_clone(original) == expected
    assert decoded  # The genuine predecessor path allocates detached records.
    decoded.clear()
    assert (
        repository_tree_projection_value_validate_equal(
            original, expected_value=expected
        )
        is None
    )
    assert decoded == []
    excessive = request()
    excessive = replace(
        excessive,
        limits=replace(excessive.limits, maximum_metadata_bytes=1),
    )
    with pytest.raises(WorkspaceTreeProjectionValueError, match="byte bound"):
        repository_tree_projection_value_validate_equal(
            excessive, expected_value=excessive
        )


@pytest.fixture(scope="module")
def metadata_predecessor_codec():
    import subprocess
    import types

    path = "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public/aware_workspace_sdk/repository_tree_projection_codec.py"
    body = subprocess.run(
        ["git", "-C", str(ROOT), "show", "658128f5fe78:" + path],
        check=True,
        capture_output=True,
    ).stdout
    pins = json.loads(
        (
            ROOT
            / "docs/reports/workspace-tree-metadata-serialization-preimages-20261013.json"
        ).read_text()
    )["preimages"]
    pin = next(row for row in pins if row["path"] == path)
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    module = types.ModuleType("aware_workspace_sdk._metadata_predecessor")
    module.__package__ = "aware_workspace_sdk"
    exec(compile(body, "<pinned-descriptive-codec>", "exec"), vars(module))  # noqa: S102 -- digest-pinned historical descriptive codec, not authority
    return module


@pytest.mark.parametrize("example", examples(), ids=lambda item: type(item).__name__)
def test_compiled_schema_keeps_predecessor_wire_and_detachment(
    metadata_predecessor_codec, example
):
    old = metadata_predecessor_codec
    assert repository_tree_projection_value_to_json(
        example
    ) == old.repository_tree_projection_value_to_json(example)
    assert repository_tree_projection_value_digest(
        example
    ) == old.repository_tree_projection_value_digest(example)
    clone = repository_tree_projection_value_clone(example)
    assert clone == old.repository_tree_projection_value_clone(example)
    assert clone is not example


@pytest.mark.parametrize("codepoint", range(128))
def test_ascii_path_acceptance_matches_original_unicode_rules(
    metadata_predecessor_codec, codepoint
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    path = "prefix/a" + chr(codepoint) + "z"
    outcomes = []
    for method in (metadata_predecessor_codec._path, codec._path):
        try:
            method(path)
        except ValueError:
            outcomes.append(False)
        else:
            outcomes.append(True)
    assert outcomes[0] == outcomes[1]


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".",
        "..",
        "a/../b",
        "a//b",
        "/a",
        "a/",
        "a\\b",
        "a" * 255,
        "a" * 256,
        "a/b/c",
        "é",
        "e\u0301",
        "日本語/a",
        "a\u00a0b",
        "a\u200bb",
        "a\u2028b",
        "a\ue000b",
        "a\U0001f600b",
        "a\u0378b",
        "a\u0085b",
        "é" * 127,
        "é" * 128,
    ],
)
def test_unicode_and_path_boundaries_match_original_rules(
    metadata_predecessor_codec, path
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    outcomes = []
    for method in (metadata_predecessor_codec._path, codec._path):
        try:
            method(path, maximum=512)
        except ValueError:
            outcomes.append(False)
        else:
            outcomes.append(True)
    assert outcomes[0] == outcomes[1]


def test_compiled_type_lookup_rejects_foreign_metaclass_without_behavior():
    calls = []

    class ForeignMeta(type):
        def __hash__(cls):
            calls.append("hash")
            raise AssertionError("foreign class hash")

        def __eq__(cls, other):
            calls.append("equality")
            raise AssertionError("foreign class equality")

    class Foreign(metaclass=ForeignMeta):
        pass

    for value_type in (None, Foreign):
        with pytest.raises(WorkspaceTreeProjectionValueError):
            repository_tree_projection_value_from_payload(value_type, {})
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_to_payload(Foreign())
    assert calls == []


@pytest.mark.parametrize("example", examples(), ids=lambda item: type(item).__name__)
def test_binding_cut_preserves_predecessor_single_field_validation(
    metadata_predecessor_codec, example
):
    """Apply independent field poisons; compare actual old/new wire or refusal."""
    old = metadata_predecessor_codec
    for field in fields(example):
        original = getattr(example, field.name)
        replacements = (
            ("", "../outside", "é", "bad\ud800")
            if type(original) is str
            else (None, 0, "false")
            if type(original) is bool
            else (True, -1, 2**64 + 1)
            if type(original) is int
            else ((), None)
            if type(original) is tuple
            else (None, 1)
        )
        for replacement in replacements:
            value = object.__new__(type(example))
            for member in fields(example):
                descriptor = vars(type(example))[member.name]
                descriptor.__set__(
                    value,
                    replacement
                    if member.name == field.name
                    else getattr(example, member.name),
                )
            outcomes = []
            for encode in (
                old.repository_tree_projection_value_to_json,
                repository_tree_projection_value_to_json,
            ):
                try:
                    outcomes.append(("wire", encode(value)))
                except ValueError as error:
                    outcomes.append(("refusal", type(error).__name__, str(error)))
            assert outcomes[0] == outcomes[1], (type(example), field.name, replacement)


@pytest.mark.parametrize("side", ["value", "expected"])
def test_binding_cut_rejects_literal_foreign_metaclass_without_behavior(side):
    calls = []

    class Meta(type):
        def __eq__(cls, other):
            calls.append("class equality")
            raise AssertionError("foreign class equality")

        def __hash__(cls):
            calls.append("class hash")
            raise AssertionError("foreign class hash")

    class Foreign(metaclass=Meta):
        def __eq__(self, other):
            calls.append("value equality")
            raise AssertionError("foreign value equality")

    genuine = request()
    bad = replace(genuine, confinement_profile=Foreign())
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_validate_equal(
            bad if side == "value" else genuine,
            expected_value=bad if side == "expected" else genuine,
        )
    assert calls == []


@pytest.mark.parametrize("side", ["value", "expected"])
def test_binding_cut_fresh_transition_slots_after_success(side, monkeypatch):
    calls = []
    value, other = binding(), binding()
    repository_tree_projection_value_validate_equal(value, expected_value=value)

    class Poison:
        def __get__(self, receiver, owner):
            calls.append("foreign descriptor")
            raise AssertionError("foreign descriptor")

    with monkeypatch.context() as patch:
        patch.setattr(v.WorkspaceTreeFileTransition, "path", Poison())
        with pytest.raises(WorkspaceTreeProjectionValueError, match="descriptor"):
            repository_tree_projection_value_validate_equal(
                value if side == "value" else other,
                expected_value=other if side == "value" else value,
            )
    assert calls == []
    object.__setattr__(value.files[0], "successor_digest", "sha256:not-a-digest")
    with pytest.raises(WorkspaceTreeProjectionValueError, match="digest"):
        repository_tree_projection_value_validate_equal(value, expected_value=value)


@pytest.mark.parametrize("annotation", [str | None, int | None, bool | None])
@pytest.mark.parametrize("depth", [0, 23, 24, 25])
def test_binding_cut_optional_scalar_depth_and_types_match_predecessor(
    metadata_predecessor_codec, annotation, depth
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    for value in (None, False, True, -1, 2**64, 2**64 + 1, "ascii", "é", "bad\ud800"):
        results = []
        for method in (metadata_predecessor_codec._convert, codec._convert):
            try:
                results.append(
                    ("value", method(annotation, value, decode=False, depth=depth))
                )
            except ValueError as error:
                results.append(("refusal", str(error)))
        assert results[0] == results[1]


@pytest.fixture(scope="module")
def complete_binding_predecessor_codec():
    import subprocess
    import types

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    packet = json.loads(
        (
            root
            / "docs/reports/workspace-tree-complete-binding-conversion-performance-inputs-20261013.json"
        ).read_text()
    )
    pin = packet["preimages"][0]
    body = subprocess.check_output(
        ["git", "show", packet["capture_revision"] + ":" + pin["path"]], cwd=root
    )
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    module = types.ModuleType("aware_workspace_sdk._complete_binding_predecessor")
    module.__package__ = "aware_workspace_sdk"
    exec(compile(body, pin["path"], "exec"), vars(module))  # noqa: S102 -- digest-verified committed source
    return module


@pytest.mark.parametrize("example", examples(), ids=lambda item: type(item).__name__)
def test_complete_binding_cut_matches_current_predecessor_fields_and_wire(
    complete_binding_predecessor_codec, example
):
    old = complete_binding_predecessor_codec
    assert repository_tree_projection_value_to_json(
        example
    ) == old.repository_tree_projection_value_to_json(example)
    for definition in fields(example):
        for poison in (None, True, -1, 2**64 + 1, "\ud800", "x" * 16385):
            bad = replace(example)
            object.__setattr__(bad, definition.name, poison)
            outcomes = []
            for encode in (
                old.repository_tree_projection_value_to_json,
                repository_tree_projection_value_to_json,
            ):
                try:
                    outcomes.append(("wire", encode(bad)))
                except ValueError as error:
                    outcomes.append(("refusal", str(error)))
            assert outcomes[0] == outcomes[1], (
                type(example).__name__,
                definition.name,
                poison,
            )


@pytest.mark.parametrize("depth", (22, 23, 24, 25))
@pytest.mark.parametrize("present", (False, True))
def test_native_scalar_field_depth_preserves_original_optional_checks(
    complete_binding_predecessor_codec, depth, present
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    value = (
        pin()
        if present
        else replace(
            pin(),
            exists=False,
            device=None,
            inode=None,
            size_bytes=None,
            mtime_ns=None,
            ctime_ns=None,
            mode=None,
            link_count=None,
            content_digest=None,
        )
    )
    outcomes = []
    for module in (complete_binding_predecessor_codec, codec):
        try:
            outcomes.append(
                (
                    "payload",
                    module._convert(type(value), value, decode=False, depth=depth),
                )
            )
        except ValueError as error:
            outcomes.append(("refusal", str(error)))
    assert outcomes[0] == outcomes[1]


@pytest.mark.parametrize(
    "path",
    [chr(code) for code in range(128)]
    + [
        "",
        "/a",
        "a/",
        "a//b",
        "a/./b",
        "a/../b",
        "a/.../b",
        "a" * 255,
        "a" * 256,
        "a/" + "x" * 256,
        " /file ",
        "é",
        "e\u0301",
        "漢/a",
        "\ud800",
    ],
)
def test_complete_binding_ascii_path_predicate_matches_current_predecessor(
    complete_binding_predecessor_codec, path
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    for candidate in (path, "prefix/" + path):
        outcomes = []
        for module in (complete_binding_predecessor_codec, codec):
            try:
                module._path(candidate, maximum=1024)
                outcomes.append(("accepted", None))
            except ValueError as error:
                outcomes.append((type(error).__name__, str(error)))
        assert outcomes[0] == outcomes[1], candidate


def test_complete_binding_preserves_both_full_passes_for_identical_operands(
    monkeypatch,
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    value = binding()
    original = codec.repository_tree_projection_value_to_payload
    calls = []

    def encode(member):
        calls.append(member)
        return original(member)

    monkeypatch.setattr(codec, "repository_tree_projection_value_to_payload", encode)
    repository_tree_projection_value_validate_equal(value, expected_value=value)
    assert len(calls) == 2 and all(member is value for member in calls)
    object.__setattr__(value, "process_id", True)
    with pytest.raises(WorkspaceTreeProjectionValueError):
        repository_tree_projection_value_validate_equal(value, expected_value=value)


def test_complete_binding_preserves_all_previous_test_declarations():
    import ast

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    packet = json.loads(
        (
            root
            / "docs/reports/workspace-tree-complete-binding-conversion-performance-inputs-20261013.json"
        ).read_text()
    )
    pin = packet["preimages"][1]
    current = {
        node.name: hashlib.sha256(
            ast.dump(node, include_attributes=False).encode()
        ).hexdigest()
        for node in ast.parse(Path(__file__).read_bytes()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    for name, digest in pin["declarations"].items():
        assert current[name] == digest, name


@pytest.mark.parametrize(
    "mutation",
    ("code", "defaults", "keyword_defaults", "copied_function", "foreign_entry"),
)
def test_complete_binding_authenticates_specialized_schema_before_foreign_call(
    monkeypatch, mutation
):
    import sys
    import types

    from aware_workspace_sdk import repository_tree_projection_codec as codec

    value = binding()
    entry = codec._NATIVE_FIELDS_BY_ID[id(type(value))]
    function, original_code = entry[2]
    called = []
    original_profile = sys.getprofile()

    def foreign(annotation, value, definitions, depth, context):
        raise AssertionError("substituted native schema must never execute")

    def profile(frame, event, _arg):
        if event == "call" and frame.f_code is foreign.__code__:
            called.append(True)

    class ForeignEntry:
        def __getitem__(self, _key):
            called.append(True)
            raise AssertionError("foreign schema holder must never execute")

    try:
        sys.setprofile(profile)
        with monkeypatch.context() as patch:
            if mutation == "code":
                patch.setattr(function, "__code__", foreign.__code__)
            elif mutation == "defaults":
                patch.setattr(function, "__defaults__", (foreign,))
            elif mutation == "keyword_defaults":
                patch.setattr(function, "__kwdefaults__", {"guard": foreign})
            elif mutation == "copied_function":
                copied = types.FunctionType(original_code, dict(function.__globals__))
                patch.setitem(
                    codec._NATIVE_FIELDS_BY_ID,
                    id(type(value)),
                    (entry[0], entry[1], (copied, original_code)),
                )
            else:
                patch.setitem(
                    codec._NATIVE_FIELDS_BY_ID, id(type(value)), ForeignEntry()
                )
            with pytest.raises(WorkspaceTreeProjectionValueError):
                repository_tree_projection_value_validate_equal(
                    value, expected_value=value
                )
        assert called == []
        repository_tree_projection_value_validate_equal(value, expected_value=value)
    finally:
        sys.setprofile(original_profile)


@pytest.fixture(scope="module")
def fresh_wire_predecessor_codec():
    import subprocess
    import types

    packet = json.loads(
        (
            ROOT
            / "docs/reports/workspace-tree-fresh-binding-wire-performance-inputs-20261014.json"
        ).read_text()
    )
    pin = packet["preimages"][0]
    body = subprocess.check_output(
        ["git", "show", packet["capture_revision"] + ":" + pin["path"]], cwd=ROOT
    )
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    module = types.ModuleType("aware_workspace_sdk._fresh_wire_predecessor")
    module.__package__ = "aware_workspace_sdk"
    exec(compile(body, pin["path"], "exec"), vars(module))  # noqa: S102 -- digest-verified committed source
    return module


@pytest.mark.parametrize("example", examples(), ids=lambda item: type(item).__name__)
def test_fresh_wire_preserves_complete_payload_json_and_digest(
    fresh_wire_predecessor_codec, example
):
    old = fresh_wire_predecessor_codec
    assert repository_tree_projection_value_to_payload(
        example
    ) == old.repository_tree_projection_value_to_payload(example)
    assert repository_tree_projection_value_to_json(
        example
    ) == old.repository_tree_projection_value_to_json(example)
    assert repository_tree_projection_value_digest(
        example
    ) == old.repository_tree_projection_value_digest(example)
    repository_tree_projection_value_validate_equal(example, expected_value=example)


@pytest.mark.parametrize("example", (request(), binding()))
def test_fresh_wire_reuses_only_unchanged_sequence_measurement(monkeypatch, example):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    original = codec._wire
    measures = []

    def measure(payload):
        measures.append(payload)
        return original(payload)

    monkeypatch.setattr(codec, "_wire", measure)
    repository_tree_projection_value_validate_equal(example, expected_value=example)
    expected = 4 if type(example) is v.WorkspaceTreeProjectionBinding else 2
    assert len(measures) == expected
    # Each complete operand conversion owns fresh detached containers.
    assert measures[0] is not measures[expected // 2]


@pytest.mark.parametrize(
    "field,changed",
    (
        ("resource_ref", "resource:different"),
        ("kind", "different"),
        ("path", None),
        ("cleanup_attempted", False),
        ("diagnostics", ("second", "first")),
    ),
)
def test_fresh_wire_structural_keys_preserve_every_changed_field(
    fresh_wire_predecessor_codec, field, changed
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    row = replace(
        large_cleanup_evidence().cleanup.resources[0],
        path="pkg/file",
        cleanup_attempted=True,
        diagnostics=("first", "second"),
    )
    rows = (row, replace(row), replace(row, **{field: changed}))
    contexts = (
        fresh_wire_predecessor_codec._ResourceContext(),
        codec._ResourceContext(),
    )
    for context in contexts:
        assert [context.index(item) for item in rows] == [0, 0, 1]
    assert contexts[0].pool == contexts[1].pool


@pytest.mark.parametrize(
    "text,count,accepted",
    (
        ("a" * 10000, 200, True),
        ("\x01" * 256, 8192, False),
        ('"\\\n東京', 200, True),
    ),
)
def test_fresh_wire_conservative_row_bound_falls_back_without_new_refusal(
    fresh_wire_predecessor_codec, text, count, accepted
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    row = replace(
        large_cleanup_evidence().cleanup.resources[0], diagnostics=(text,) * count
    )
    outcomes = []
    for module in (fresh_wire_predecessor_codec, codec):
        context = module._ResourceContext()
        try:
            context.index(row)
        except module.WorkspaceTreeProjectionValueError as error:
            outcomes.append((False, str(error)))
            assert not context.pool and not context.keys
        else:
            outcomes.append((True, context.pool))
    assert outcomes[0] == outcomes[1]
    assert outcomes[0][0] is accepted


@pytest.mark.parametrize("shared", (False, True))
def test_fresh_wire_resource_envelope_remains_canonical(
    fresh_wire_predecessor_codec, shared
):
    value = resource_occurrence_value(500, shared=shared, receipt_count=20)
    old = fresh_wire_predecessor_codec.repository_tree_projection_value_to_json(value)
    current = repository_tree_projection_value_to_json(value)
    assert current == old
    decoded = repository_tree_projection_value_from_json(type(value), current)
    assert repository_tree_projection_value_to_json(decoded) == current


def test_fresh_wire_preserves_frozen_functions_and_prior_test_declarations():
    import ast
    import subprocess

    packet = json.loads(
        (
            ROOT
            / "docs/reports/workspace-tree-fresh-binding-wire-performance-inputs-20261014.json"
        ).read_text()
    )
    for pin in packet["preimages"]:
        before = subprocess.check_output(
            ["git", "show", packet["capture_revision"] + ":" + pin["path"]], cwd=ROOT
        )
        predecessor = {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(before).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        current = {
            node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse((ROOT / pin["path"]).read_bytes()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        names = (
            packet["frozen_functions"]
            if pin["path"].endswith("codec.py")
            else predecessor
        )
        for name in names:
            assert current[name] == predecessor[name], name


@pytest.mark.parametrize("extra", (0, 1))
def test_fresh_wire_row_preserves_exact_original_byte_boundary(
    fresh_wire_predecessor_codec, extra
):
    from aware_workspace_sdk import repository_tree_projection_codec as codec

    base = replace(
        large_cleanup_evidence().cleanup.resources[0],
        diagnostics=("a" * 16384,) * 511 + ("",),
    )
    size = len(
        json.dumps(
            asdict(base), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    )
    remainder = v.MAX_TREE_METADATA_BYTES - size + extra
    assert 0 < remainder <= 16384
    row = replace(base, diagnostics=base.diagnostics[:-1] + ("a" * remainder,))
    for module in (fresh_wire_predecessor_codec, codec):
        context = module._ResourceContext()
        if extra:
            with pytest.raises(
                module.WorkspaceTreeProjectionValueError, match="byte bound"
            ):
                context.index(row)
            assert not context.pool
        else:
            assert context.index(row) == 0
            assert len(context.pool) == 1
