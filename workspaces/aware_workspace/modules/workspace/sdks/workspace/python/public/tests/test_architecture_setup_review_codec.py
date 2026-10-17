"""Data-only contract proofs. No private-directory provider is simulated."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import tomllib
from pathlib import Path

import pytest
from aware_issue_sdk import operation as issue
from aware_workspace_sdk import architecture_setup_review_codec as c
from aware_workspace_sdk import architecture_setup_review_values as v
from aware_workspace_sdk.architecture_setup import ArchitectureSetupRequest
from aware_workspace_sdk.architecture_setup_command_values import (
    WorkspaceSetupA1CommandRequest,
    WorkspaceSetupA1ReviewGuards,
)
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

D = "sha256:" + "a" * 64
ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
)
PACKET = ROOT / "docs/reports/workspace-reviewed-refusal-artifact-inputs-20261017.json"
TYPES = {cls.__name__: cls for cls in v.REVIEW_FIELD_TYPES}
WIRE_TYPES = [cls for cls, wire in v.REVIEW_SCHEMA_IDS.items() if wire is not None]
VIEW_TYPES = [cls for cls, wire in v.REVIEW_SCHEMA_IDS.items() if wire is None]


@pytest.mark.parametrize(
    ("package", "relative"),
    [
        ("aware-workspace-sdk", "sdks/workspace/python/public"),
        ("aware-workspace-runtime", "libs/workspace_runtime"),
        ("aware-workspace-fs-adapter", "sdks/workspace/filesystem_adapter/python"),
    ],
)
def test_review_distribution_joins_finite_successor_edges(package, relative):
    """The profile must resolve actual suppliers and exclude old missing ports."""
    freeze = json.loads(PACKET.read_text())
    candidates = {row["package"]: row for row in freeze["versions"]}
    manifest = (
        ROOT
        / "workspaces/aware_workspace/modules/workspace"
        / relative
        / "pyproject.toml"
    )
    project = tomllib.loads(manifest.read_text())["project"]
    assert project["name"] == package
    assert project["version"] == candidates[package]["candidate"]
    base = [Requirement(text) for text in project["dependencies"]]
    review = [
        Requirement(text)
        for text in project.get("optional-dependencies", {}).get("setup_review", ())
    ]
    selected = base + review
    for text in candidates[package]["requires"]:
        declared = Requirement(text)
        matches = [
            req
            for req in selected
            if canonicalize_name(req.name) == canonicalize_name(declared.name)
            and req.extras == declared.extras
        ]
        assert matches, (package, text)
        assert all(req.specifier == declared.specifier for req in matches)
        owner = candidates.get(canonicalize_name(declared.name))
        if owner is not None:
            assert all(owner["candidate"] in req.specifier for req in matches)
            assert all(owner["current"] not in req.specifier for req in matches)
    if package != "aware-workspace-fs-adapter":
        assert review
        issue = next(req for req in review if req.name == "aware-issue-sdk")
        assert "0.10.6" in issue.specifier
        assert "0.10.5" not in issue.specifier
        assert not any("service" in req.name or "orm" in req.name for req in review)


def test_authored_review_fields_preserve_required_nulls_and_original_owner_names():
    """Run with the qualified union/presence parser, not the old host binding."""
    from tree_sitter_aware.neutral_ir import parse_neutral_aware_source

    path = (
        ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware/architecture_setup_review_values.aware"
    )
    document = parse_neutral_aware_source(path.read_text(), source_path=str(path))
    classes = {
        next(child.text for child in node.children if child.field_name == "name"): node
        for node in document.root.children
        if node.kind == "class_def"
    }
    assert set(classes) == {cls.__name__ for cls in WIRE_TYPES}
    owners = {
        "OriginalArchitectureRequest": "ArchitectureSetupRequest",
        "OriginalReviewRequest": "WorkspaceSetupA1CommandRequest",
        "OriginalReviewGuards": "WorkspaceSetupA1ReviewGuards",
        "OriginalIssueReadResult": "aware_issue_sdk.IssueReadProjectionResolveResult",
        "OriginalScopeRequest": "aware_issue_sdk.IssueBindScopePathsRequest",
        "OriginalWorkspaceClientCleanup": "WorkspaceSetupClientCleanup",
        "OriginalIssueClientCleanup": "aware_issue_sdk.IssueWorkspaceSetupClientCleanup",
        "OriginalIssueSourcesObservation": "aware_issue_sdk.IssueWorkspaceSetupSourcesObservation",
    }

    def spelling(kind):
        if kind.startswith("Nullable["):
            return spelling(kind[9:-1]) + "?"
        if kind.startswith("Array["):
            return spelling(kind[6:-1].rsplit(",", 1)[0]) + "[]"
        if kind in owners:
            return owners[kind]
        if kind.startswith("Private"):
            return "aware_file_system." + kind
        if kind in v.REVIEW_ENUMS:
            return "SetupReview" + kind
        if kind in ("Bool", "False"):
            return "Bool"
        if kind in v.REVIEW_SCALARS:
            return "Int" if v.REVIEW_SCALARS[kind]["kind"] == "integer" else "String"
        return kind

    for cls in WIRE_TYPES:
        members = [
            node for node in classes[cls.__name__].children if node.kind == "attr_def"
        ]
        actual = [
            (
                next(
                    child.text for child in node.children if child.field_name == "name"
                ),
                next(
                    child.text for child in node.children if child.field_name == "type"
                ),
            )
            for node in members
        ]
        assert actual == [
            (name, spelling(kind)) for name, kind in v.REVIEW_FIELD_TYPES[cls]
        ]
        for member, (_, kind) in zip(members, v.REVIEW_FIELD_TYPES[cls], strict=True):
            presence = [
                child.text
                for child in member.children
                if child.field_name == "presence"
            ]
            assert presence == (["required"] if kind.startswith("Nullable[") else [])


@pytest.mark.parametrize("cls", WIRE_TYPES, ids=lambda cls: cls.__name__)
def test_authored_review_descriptive_lowering_preserves_required_nulls(cls):
    """Original Language/Meta projection, not a generated operation or admission."""
    from aware_meta_type_schema import ScalarKind, ValueShape
    from test_architecture_setup_a1_command_values import WORKSPACE, project

    projection = project(
        WORKSPACE, "architecture_setup_*.aware", [row.__name__ for row in WIRE_TYPES]
    )
    definition = next(
        row.definition
        for row in projection.definitions
        if row.definition.type_ref == "aware_workspace_sdk." + cls.__name__
    )
    assert tuple(field.name for field in definition.fields) == tuple(
        name for name, _ in v.REVIEW_FIELD_TYPES[cls]
    )
    for field, (_, kind) in zip(
        definition.fields, v.REVIEW_FIELD_TYPES[cls], strict=True
    ):
        assert field.required
        assert field.nullable is kind.startswith("Nullable[")
        if kind.startswith("Nullable["):
            kind = kind[9:-1]
        collection = kind.startswith("Array[")
        if collection:
            kind = kind[6:-1].rsplit(",", 1)[0]
        shape = field.shape.element if collection else field.shape
        if kind.startswith("Private"):
            assert shape == ValueShape.named("aware_file_system." + kind)
        elif kind in ("Bool", "False"):
            assert shape == ValueShape.scalar(ScalarKind.BOOLEAN)
        elif kind in v.REVIEW_ENUMS:
            assert shape == ValueShape.named("aware_workspace_sdk.SetupReview" + kind)


def sample(kind):
    if kind.startswith("Nullable["):
        return None
    if kind.startswith("Array["):
        return ()
    if kind == "False":
        return False
    if kind in v.REVIEW_ENUMS:
        return v.REVIEW_ENUMS[kind][0]
    if kind in TYPES:
        return value(TYPES[kind])
    if kind.startswith("Original"):
        return {
            "OriginalArchitectureRequest": lambda: ArchitectureSetupRequest(
                "repository", name="example", license_expression="MIT"
            ),
            "OriginalReviewGuards": lambda: WorkspaceSetupA1ReviewGuards(D, D, D),
            "OriginalReviewRequest": lambda: WorkspaceSetupA1CommandRequest(
                sample("OriginalArchitectureRequest"),
                None,
                "/tmp/repo",
                "aware.protocol.toml",
                "docs/issue.md",
                "codex-proof",
                "intent:proof",
            ),
            "OriginalScopeRequest": lambda: issue.IssueBindScopePathsRequest(
                "fb/proof", D, "intent:proof", "actor", "evidence", ("source.py",)
            ),
            "OriginalIssueReadResult": lambda: issue.IssueReadProjectionResolveResult(
                issue.IssueReadProjectionResolveOutcome.ABSENT,
                "fb/proof",
                "provider",
                "provider-package",
                "1.0",
            ),
        }[kind]()
    spec = v.REVIEW_SCALARS[kind]
    if spec["kind"] == "integer":
        return spec["minimum"]
    if spec["kind"] == "boolean":
        return False
    return {"RootPath": "/tmp/repo", "RelativePath": "source.py", "Digest": D}.get(
        kind, "proof"
    )


def value(cls):
    data = {key: sample(kind) for key, kind in v.REVIEW_FIELD_TYPES[cls]}
    if cls is v.SetupCaptureDescriptor:
        data.update(byte_count=1, chunks=(v.SetupChunkDescriptor(0, "part.bin", 1, D),))
    if cls is v.SetupScopeOutcomeRecord:
        data["capture"] = value(v.SetupCaptureDescriptor)
    if cls is v.SetupRefusalRecord:
        request = data["request"]
        attempt = hashlib.sha256(
            b"aware.setup-review.attempt.v1\0"
            + request.execution_ref.encode()
            + b"\0"
            + request.client_intent_id.encode()
        ).hexdigest()
        data["review_ref"] = dataclasses.replace(
            data["review_ref"],
            target=request.target,
            attempt_ref=attempt,
            record_contract=v.REVIEW_SCHEMA_IDS[v.SetupReviewRecord],
        )
        data["phase"] = "read_review"
    return cls(**data)


@pytest.mark.parametrize("cls", list(v.REVIEW_FIELD_TYPES))
def test_original_contract_fields_and_wire_identifiers(cls):
    if cls is v.SetupRefusalRecord:
        assert (
            v.REVIEW_SCHEMA_IDS[cls]
            == "aware.workspace.setup-review.setup-refusal-record.v1"
        )
        assert [f.name for f in dataclasses.fields(cls)] == [
            "review_ref",
            "request",
            "code",
            "phase",
            "observed_issue",
            "observed_sources",
            "issue_cleanup",
            "reads",
            "scope_decision",
            "apply_decision",
            "inputs_ref",
            "product_dispatch",
            "authorizes_retry",
        ]
        return
    packet = json.loads(PACKET.read_text())["types"][cls.__name__]
    expected = [(r["name"], r["type"]) for r in packet["fields"]]
    if cls is v.SetupReviewFailure:
        expected += [
            ("reads", "Array[PrivateFileReadResult,40]"),
            ("refusal", "Nullable[SetupRefusalRecord]"),
        ]
    assert [f.name for f in dataclasses.fields(cls)] == [r[0] for r in expected]
    assert tuple(v.REVIEW_FIELD_TYPES[cls]) == tuple(expected)
    assert v.REVIEW_SCHEMA_IDS[cls] == packet["wire_id"]


@pytest.mark.parametrize(
    "change",
    [
        "target",
        "attempt",
        "review_type",
        "phase",
        "alternative",
        "retry",
        "dispatch",
        "missing_call",
        "foreign_call",
    ],
)
@pytest.mark.parametrize("direction", ["encode", "decode"])
def test_refusal_record_cannot_claim_a_different_context_or_dispatch(change, direction):
    record = value(v.SetupRefusalRecord)
    if change == "target":
        record = dataclasses.replace(
            record,
            review_ref=dataclasses.replace(
                record.review_ref,
                target=dataclasses.replace(record.request.target, issue_tag="other"),
            ),
        )
    elif change == "attempt":
        record = dataclasses.replace(
            record,
            review_ref=dataclasses.replace(record.review_ref, attempt_ref="other"),
        )
    elif change == "review_type":
        record = dataclasses.replace(
            record,
            review_ref=dataclasses.replace(
                record.review_ref,
                record_contract=v.REVIEW_SCHEMA_IDS[v.SetupRefusalRecord],
            ),
        )
    elif change == "phase":
        record = dataclasses.replace(record, phase="driver_return")
    elif change == "alternative":
        record = dataclasses.replace(record, code="review_authority_sources_changed")
    elif change == "retry":
        record = dataclasses.replace(record, authorizes_retry=True)
    elif change == "missing_call":
        record = dataclasses.replace(record, phase="record_review_decision")
    elif change == "foreign_call":
        record = dataclasses.replace(
            record,
            phase="record_review_decision",
            scope_decision=v.SetupScopeDecision(
                dataclasses.replace(record.review_ref, attempt_ref="other"),
                "accept_reviewed_effect_scope",
                "caller",
                "intent",
            ),
        )
    else:
        record = dataclasses.replace(record, product_dispatch="attempted")
    if direction == "encode":
        with pytest.raises(c.SetupReviewValueError):
            c.review_value_to_payload(record)
    else:
        # Encode the malformed dataclass fields individually without applying
        # the new enclosing invariant; the receiving codec must reject it too.
        budget = c._Budget()
        raw = {
            name: c._convert(kind, getattr(record, name), False, budget, 1)
            for name, kind in v.REVIEW_FIELD_TYPES[v.SetupRefusalRecord]
            if name not in ("authorizes_retry", "product_dispatch")
        }
        raw["authorizes_retry"] = record.authorizes_retry
        raw["product_dispatch"] = record.product_dispatch
        with pytest.raises(c.SetupReviewValueError):
            c.review_value_from_payload(
                v.SetupRefusalRecord,
                {"contract": v.REVIEW_SCHEMA_IDS[v.SetupRefusalRecord], "value": raw},
            )


@pytest.mark.parametrize("cls", WIRE_TYPES)
def test_all_wire_roots_roundtrip_through_original_owner_codecs(cls):
    original = value(cls)
    payload = c.review_value_to_payload(original)
    assert set(payload) == {"contract", "value"}
    assert c.review_value_from_payload(cls, payload) == original
    text = c.review_value_to_json(original)
    assert c.review_value_from_json(cls, text) == original
    assert (
        c.review_value_digest(original)
        == "sha256:" + hashlib.sha256(text.encode()).hexdigest()
    )


@pytest.mark.parametrize("cls", WIRE_TYPES)
@pytest.mark.parametrize(
    "poison", ["missing", "extra", "wrong_version", "foreign_wrapper"]
)
def test_every_wire_root_is_closed(cls, poison):
    payload = c.review_value_to_payload(value(cls))
    if poison == "missing":
        payload["value"].pop(next(iter(payload["value"])))
    elif poison == "extra":
        payload["value"]["authority"] = True
    elif poison == "wrong_version":
        payload["contract"] = str(payload["contract"]).replace(".v1", ".v2")
    else:

        class Foreign(dict):
            pass

        payload = Foreign(payload)
    with pytest.raises(ValueError):
        c.review_value_from_payload(cls, payload)


@pytest.mark.parametrize("cls", VIEW_TYPES)
def test_in_process_views_have_no_wire_or_decode_entrance(cls):
    with pytest.raises(c.SetupReviewValueError, match="serializable_original"):
        c.review_value_from_payload(cls, {})
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_to_payload(object.__new__(cls))


@pytest.mark.parametrize("cls", WIRE_TYPES)
def test_required_nullable_fields_cannot_disappear(cls):
    payload = c.review_value_to_payload(value(cls))
    for field, kind in v.REVIEW_FIELD_TYPES[cls]:
        if kind.startswith("Nullable["):
            changed = dict(payload["value"])
            assert changed.pop(field) is None or cls is v.SetupScopeOutcomeRecord
            with pytest.raises(c.SetupReviewValueError):
                c.review_value_from_payload(cls, {**payload, "value": changed})


@pytest.mark.parametrize("bad", [True, -1, 2**64, 0.5, "1"])
def test_identity_rejects_foreign_or_out_of_range_integer(bad):
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_to_payload(v.DirectoryIdentity(bad, 1))


@pytest.mark.parametrize(
    "path",
    ["../a", "a//b", "a/./b", "/absolute", "a\\b", "a/", "a\0b", "/".join(["a"] * 65)],
)
def test_canonical_relative_paths(path):
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_to_payload(
            dataclasses.replace(value(v.SetupTarget), issue_path=path)
        )


@pytest.mark.parametrize(
    "text",
    [
        '{"contract":0,"contract":1}',
        '{"x":NaN}',
        '{"x":1.2}',
        "\ufeff{}",
        '{"x":"\ud800"}',
        "[" * 1000 + "]" * 1000,
    ],
)
def test_raw_json_refuses_ambiguous_nonfinite_invalid_and_deep_values(text):
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_from_json(v.SetupTarget, text)


def test_incremental_byte_node_and_depth_budgets():
    for source in ["x" * (c.MAX_RECORD_BYTES + 1), "é" * (c.MAX_RECORD_BYTES // 2 + 1)]:
        with pytest.raises(c.SetupReviewValueError, match="byte_limit"):
            c.review_value_from_json(v.SetupTarget, source)
    budget = c._Budget()
    with pytest.raises(c.SetupReviewValueError, match="structure_limit"):
        c._tree([[None] * 16384, [None] * 16384], budget, 0)
    with pytest.raises(c.SetupReviewValueError, match="structure_limit"):
        c._tree([], c._Budget(), 33)
    budget = c._Budget()
    budget.charge(c.MAX_RECORD_BYTES)
    with pytest.raises(c.SetupReviewValueError, match="byte_limit"):
        budget.charge(1)


@pytest.mark.parametrize("which", ["ordinal", "count", "duplicate_leaf", "empty"])
def test_capture_requires_complete_ordered_chunk_accounting(which):
    original = value(v.SetupCaptureDescriptor)
    if which == "ordinal":
        changed = dataclasses.replace(
            original, chunks=(dataclasses.replace(original.chunks[0], ordinal=1),)
        )
    elif which == "count":
        changed = dataclasses.replace(original, byte_count=2)
    elif which == "duplicate_leaf":
        changed = dataclasses.replace(
            original,
            byte_count=2,
            chunks=original.chunks
            + (dataclasses.replace(original.chunks[0], ordinal=1),),
        )
    else:
        changed = dataclasses.replace(original, chunks=())
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_to_payload(changed)


def test_unknown_and_captured_scope_alternatives_cannot_be_confused():
    record = value(v.SetupScopeOutcomeRecord)
    unknown = dataclasses.replace(
        record,
        outcome_kind="unknown",
        capture=None,
        unknown=value(v.SetupUnknownScopeOutcome),
    )
    assert (
        c.review_value_from_json(type(unknown), c.review_value_to_json(unknown))
        == unknown
    )
    for changed in [
        dataclasses.replace(record, capture=None),
        dataclasses.replace(unknown, capture=record.capture),
        dataclasses.replace(unknown, unknown=None),
    ]:
        with pytest.raises(c.SetupReviewValueError):
            c.review_value_to_payload(changed)


def test_original_slots_are_checked_without_invoking_a_foreign_descriptor(monkeypatch):
    calls = []
    original = value(v.SetupTarget)
    monkeypatch.setattr(
        v.SetupTarget, "issue_path", property(lambda _: calls.append("called"))
    )
    with pytest.raises(c.SetupReviewValueError, match="slot_changed"):
        c.review_value_to_payload(original)
    assert calls == []


def test_false_retry_and_no_private_import_for_empty_descriptive_evidence(monkeypatch):
    original = value(v.RetentionEvidence)
    imported = []

    def forbidden(name):
        imported.append(name)
        raise AssertionError("no physical module needed")

    monkeypatch.setattr(importlib, "import_module", forbidden)
    assert (
        c.review_value_from_json(type(original), c.review_value_to_json(original))
        == original
    )
    with pytest.raises(c.SetupReviewValueError):
        c.review_value_to_payload(
            dataclasses.replace(value(v.SetupDispatchIntent), authorizes_retry=True)
        )
    assert imported == []


def test_portable_values_and_scalar_codecs_import_without_physical_or_issue_packages():
    import subprocess
    import sys

    sdk = (
        ROOT
        / "workspaces/aware_workspace/modules/workspace/sdks/workspace/python/public"
    )
    script = """import sys
sys.path.insert(0, sys.argv[1])
from aware_workspace_sdk.architecture_setup_review_values import DirectoryIdentity
from aware_workspace_sdk.architecture_setup_review_codec import review_value_to_json
assert review_value_to_json(DirectoryIdentity(1,2))
assert not any(n.startswith(('aware_file_system','aware_issue_sdk','aware_workspace_fs_adapter','aware_workspace_runtime')) for n in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", script, str(sdk)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
