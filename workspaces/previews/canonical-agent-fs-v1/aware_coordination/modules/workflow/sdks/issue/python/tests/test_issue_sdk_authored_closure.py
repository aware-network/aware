"""Ordinary Issue source contract parity, not installed or authority admission."""

import hashlib
from dataclasses import MISSING, fields, replace
from pathlib import Path

import pytest
from aware_issue_runtime import IssueTimeAuthority, parse_issue_projection
from aware_issue_sdk import (
    ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF,
    IssueMutationOutcome,
    IssueMutationResult,
    IssuePublicationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveResult,
)
from aware_meta_type_schema import TypeSchemaBundle, validate_typed_value
from aware_sdk_contract_runtime_provider import (
    SdkDefinitionRequest,
    lower_parsed_sdk_definition,
)
from aware_sdk_contract_runtime_source import materialize_sdk_source_contract
from test_issue_sdk_result_boundary import CASES, ISSUE, result_for
from tree_sitter_aware.parsed_document import (
    AwarePortableParseInput,
    parse_aware_document_batch,
)

SOURCE = Path(__file__).resolve().parents[2] / "aware"
OPERATIONS = tuple(
    sorted(
        ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF
        if method == "resolve_read_projection"
        else operation_request.operation_ref
        for method, operation_request in CASES
    )
)


def source_contract(sources=None, operations=OPERATIONS):
    return materialize_sdk_source_contract(
        sdk_toml_text=(SOURCE / "aware.sdk.toml").read_text(),
        source_text_by_path=sources
        if sources is not None
        else {path.name: path.read_text() for path in sorted(SOURCE.glob("*.aware"))},
        selected_operation_refs=operations,
    )


@pytest.fixture(scope="module")
def materialized():
    return source_contract()


@pytest.fixture(scope="module")
def bundle(materialized):
    definitions = {
        definition.type_ref: definition
        for schema in materialized.manifest.schema_slices
        for definition in schema.types
    }
    return TypeSchemaBundle.create(
        namespace="aware_issue_sdk",
        semantic_version="1",
        types=tuple(definitions.values()),
    )


def test_real_oracle_and_parsed_provider_agree_without_identity_or_target_substitution(
    materialized,
):
    sources = {path.name: path.read_text() for path in sorted(SOURCE.glob("*.aware"))}
    inputs = tuple(
        AwarePortableParseInput(
            "package:issue-sdk@1",
            "issue-sdk",
            "sdk/sources/" + name,
            "cas://sdk-source/" + hashlib.sha256(text.encode()).hexdigest(),
            "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
            len(text.encode()),
            text,
        )
        for name, text in sources.items()
    )
    batch = parse_aware_document_batch(inputs).batch
    request = SdkDefinitionRequest.create(
        sdk_ref="issue_sdk",
        semantic_version="1",
        targets=materialized.manifest.targets,
        selected_operation_refs=OPERATIONS,
    )
    assert (
        lower_parsed_sdk_definition(request, batch, materialized.manifest.schema_slices)
        == materialized.definition_state
    )
    assert materialized.manifest.sdk_ref == "issue_sdk"
    assert (
        tuple(operation.operation_ref for operation in materialized.manifest.operations)
        == OPERATIONS
    )
    # Inventory describes all authored operations, not installed capability.
    assert len(materialized.inventory.operation_refs) == 19
    assert set(OPERATIONS) < set(materialized.inventory.operation_refs)
    assert len(materialized.manifest.operations) == len(CASES) == 11
    assert len(materialized.manifest.schema_slices) == 17
    assert all(
        schema.namespace == "aware_issue_sdk"
        for schema in materialized.manifest.schema_slices
    )
    assert tuple(target.language for target in materialized.manifest.targets) == (
        "python",
    )
    assert materialized.authority_grade == "portable_input"
    assert (
        source_contract(
            dict(reversed(tuple(sources.items()))), tuple(reversed(OPERATIONS))
        )
        == materialized
    )


@pytest.mark.parametrize("method,operation_request", CASES)
def test_public_request_serialization_matches_genuine_root(
    bundle, method, operation_request
):
    type_ref = "aware_issue_sdk." + type(operation_request).__name__
    payload = operation_request.to_wire()
    definition = next(item for item in bundle.types if item.type_ref == type_ref)
    names = {field.name for field in definition.fields}
    assert names == set(payload)
    expected = {field.name for field in fields(operation_request)}
    expected.add("contract" if method == "resolve_read_projection" else "operation_ref")
    assert names == expected
    assert validate_typed_value(bundle, type_ref, payload).is_valid
    assert not validate_typed_value(
        bundle, type_ref, {**payload, "issue_ref": 42}
    ).is_valid
    assert not validate_typed_value(
        bundle, type_ref, {**payload, "extra": "unrecognized"}
    ).is_valid


@pytest.mark.parametrize("method,operation_request", CASES)
def test_existing_refusal_or_publication_result_wire_matches_root(
    bundle, method, operation_request
):
    result = result_for(method, operation_request)
    type_ref = "aware_issue_sdk." + type(result).__name__
    payload = result.to_wire()
    assert validate_typed_value(bundle, type_ref, payload).is_valid
    assert not validate_typed_value(
        bundle, type_ref, {**payload, "outcome": "invented"}
    ).is_valid
    definition = next(item for item in bundle.types if item.type_ref == type_ref)
    omitted = {field.name for field in definition.fields} - set(payload)
    assert omitted <= {
        "shared_index_projection",
        "shared_index_projection_error",
        "index_reconciliation_pending",
    }
    assert all(field.nullable for field in definition.fields if field.name in omitted)


def rich_projection():
    return parse_issue_projection(
        text=f"""# Issue: Genuine structural fixture

- Slug: `fixture`
- Tag: `{ISSUE}`
- Status: In Progress
- Owner: `codex-test`

## Problem
1. Exercise nested payload.

## Goal
1. Preserve structure.

## Ownership Scope
- `src/a.py`

## Acceptance Checklist
- [ ] Verify exact evidence.

## Updates (append-only)
- 2026-10-08T00:00:00Z — Observation fixture. (recorder: `codex-test`)

## Verified-by
- test:fixture

## Additional fixture
Preserved text.
""",
        source_path="docs/issues/2026/10/08/fixture.md",
    )


@pytest.mark.parametrize("family", ["read", "mutation", "closeout"])
def test_successful_wire_reuses_real_projection_payload(bundle, family):
    projection = rich_projection()
    assert (
        projection.acceptance_items
        and projection.activities
        and projection.additional_sections
    )
    if family == "read":
        result = IssueReadProjectionResolveResult(
            IssueReadProjectionResolveOutcome.FOUND,
            ISSUE,
            "test.provider",
            "test-provider",
            "1.0.0",
            projection,
        )
    else:
        result = IssueMutationResult(
            operation_ref="issue_sdk.close_issue"
            if family == "closeout"
            else "issue_sdk.append_issue_update",
            outcome=IssueMutationOutcome.APPLIED,
            issue_ref=ISSUE,
            provider_ref="test.provider",
            provider_distribution="test-provider",
            provider_version="1.0.0",
            projection=projection,
            closeout_publication_receipt_ref="git:" + "a" * 40
            if family == "closeout"
            else None,
            shared_index_projection="failed" if family == "closeout" else None,
            shared_index_projection_error="retained" if family == "closeout" else None,
            index_reconciliation_pending=True if family == "closeout" else None,
        )
    payload = result.to_wire()
    type_ref = "aware_issue_sdk." + type(result).__name__
    assert payload["projection"] == projection.to_payload(include_raw_markdown=False)
    assert payload["projection"]["source"]["raw_markdown"] is None
    assert validate_typed_value(bundle, type_ref, payload).is_valid
    payload["projection"]["content"]["acceptance_items"][0]["checked"] = "true"
    assert not validate_typed_value(bundle, type_ref, payload).is_valid


@pytest.mark.parametrize(
    "enum_type",
    [
        IssueMutationOutcome,
        IssuePublicationOutcome,
        IssueReadProjectionResolveOutcome,
        IssueTimeAuthority,
    ],
)
def test_authored_enum_matches_original_owner_vocabulary(bundle, enum_type):
    definition = next(
        item
        for item in bundle.types
        if item.type_ref == "aware_issue_sdk." + enum_type.__name__
    )
    assert set(definition.enum_values) == {item.value for item in enum_type}


@pytest.mark.parametrize("method,operation_request", CASES[1:])
def test_serialized_requests_are_detached_data_not_original_values(
    method, operation_request
):
    payload = operation_request.to_wire()
    original = operation_request.to_wire()
    for value in payload.values():
        if isinstance(value, list):
            value.append("foreign")
    payload["actor_ref"] = "foreign"
    assert operation_request.to_wire() == original


@pytest.mark.parametrize("method,operation_request", CASES)
def test_declared_defaults_match_valid_python_request_defaults(
    bundle, method, operation_request
):
    definition = next(
        item
        for item in bundle.types
        if item.type_ref == "aware_issue_sdk." + type(operation_request).__name__
    )
    declared = {
        field.name: field.default_value.to_wire()
        for field in definition.fields
        if field.default_value is not None
    }
    for field in fields(operation_request):
        if field.name not in declared or field.default is MISSING:
            continue
        expected = (
            list(field.default) if isinstance(field.default, tuple) else field.default
        )
        assert declared[field.name] == expected
    for name in ("contract", "operation_ref"):
        if name in declared:
            assert declared[name] == operation_request.to_wire()[name]


def test_authored_content_inputs_use_sdk_serialization(bundle):
    original = CASES[1][1]
    operation_request = replace(
        original,
        owner_ref="codex-test",
        expected_source_sha256="sha256:" + "a" * 64,
        problem_items=("Concrete problem",),
        objective_items=("Expected outcome",),
        acceptance_items=("Verify evidence",),
    )
    wire = operation_request.to_wire()
    assert wire["problem_items"] == ["Concrete problem"]
    assert wire["objective_items"] == ["Expected outcome"]
    assert wire["acceptance_items"] == ["Verify evidence"]
    assert validate_typed_value(
        bundle, "aware_issue_sdk.IssueEnsureSnapshotRequest", wire
    ).is_valid
    assert not validate_typed_value(
        bundle,
        "aware_issue_sdk.IssueEnsureSnapshotRequest",
        {**wire, "acceptance_items": [True]},
    ).is_valid


def test_structural_defaults_and_digests_do_not_substitute_for_sdk_checks(bundle):
    wire = CASES[-1][1].to_wire()
    # The transport schema describes strings, not operation admission or CAS.
    # Constructors and the SDK/provider retain those stronger validations.
    changed = {
        **wire,
        "operation_ref": "foreign.operation",
        "expected_issue_source_sha256": "not-a-source-digest",
    }
    assert validate_typed_value(
        bundle, "aware_issue_sdk.IssueCommitWorkspaceRequest", changed
    ).is_valid


@pytest.mark.parametrize("outcome", tuple(IssuePublicationOutcome))
def test_existing_publication_outcomes_remain_data_not_write_authority(bundle, outcome):
    result = result_for(*CASES[-1])
    if outcome is not IssuePublicationOutcome.APPLIED:
        result = replace(result, outcome=outcome, commit_hash=None)
    wire = result.to_wire()
    assert validate_typed_value(
        bundle, "aware_issue_sdk.IssueCommitWorkspaceResult", wire
    ).is_valid
    assert wire["index_reconciliation_pending"] is True
    assert wire["shared_index_projection"] == "failed"


@pytest.mark.parametrize(
    "missing",
    [
        "issue_operation_values.aware",
        "issue_read_projection_values.aware",
        "issue_operation_errors.aware",
    ],
)
def test_missing_real_type_source_refuses_without_placeholder(missing):
    sources = {
        path.name: path.read_text()
        for path in SOURCE.glob("*.aware")
        if path.name != missing
    }
    with pytest.raises(ValueError, match="type"):
        source_contract(sources)


@pytest.mark.parametrize(
    "operation",
    [
        "issue_sdk.reopen_issue",
        "issue_sdk.observe_specification_iteration_binding",
        "issue_sdk.unknown",
    ],
)
def test_separate_or_incomplete_operations_are_not_silently_admitted(operation):
    with pytest.raises(ValueError):
        source_contract(operations=(operation,))
