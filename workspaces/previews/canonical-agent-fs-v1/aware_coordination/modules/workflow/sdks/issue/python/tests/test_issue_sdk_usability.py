from dataclasses import replace

import pytest
from aware_issue_runtime import parse_issue_projection
from aware_issue_sdk import (
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssueMutationResult,
    IssueOperationContractError,
)

REF = "fb/2026-10-05/usability"


def request(**changes):
    return IssueEnsureSnapshotRequest(
        issue_ref=REF,
        title="Usability",
        priority="P1",
        actor_ref="codex-fixture",
        actor_evidence_ref="fixture:actor",
        client_intent_id="fixture:ensure",
        **changes,
    )


def result(**changes):
    return IssueMutationResult(
        operation_ref="issue_sdk.close_issue",
        outcome=IssueMutationOutcome.APPLIED,
        issue_ref=REF,
        provider_ref="fixture",
        provider_distribution="fixture",
        provider_version="1.0",
        projection=parse_issue_projection(
            text=f"# Issue: Usability\n\n- Tag: `{REF}`\n",
            source_path="docs/issues/2026/10/05/fb-2026-10-05-usability.md",
        ),
        **changes,
    )


def test_authored_content_is_defensively_frozen():
    items = ["The approved check"]
    value = request(problem_items=items, objective_items=items, acceptance_items=items)
    items.append("Caller changed its input")
    assert (
        value.problem_items
        == value.objective_items
        == value.acceptance_items
        == ("The approved check",)
    )


@pytest.mark.parametrize(
    "field", ["problem_items", "objective_items", "acceptance_items"]
)
@pytest.mark.parametrize(
    "value",
    [
        "not-a-list",
        [None],
        [""],
        [" padded "],
        ["line\n## Status"],
        ["nul\x00"],
        ["tab\t"],
        ["del\x7f"],
        ["unicode\u2028break"],
    ],
)
def test_authored_content_refuses_malformed_or_section_injection(field, value):
    with pytest.raises(IssueOperationContractError):
        request(**{field: value})


def test_legacy_omitted_content_is_explicitly_supported():
    value = request()
    assert value.problem_items == value.objective_items == value.acceptance_items == ()


def test_legacy_closeout_index_evidence_is_unknown_not_false():
    wire = result(closeout_publication_receipt_ref="git:" + "a" * 40).to_wire()
    assert wire["shared_index_projection"] is None
    assert wire["index_reconciliation_pending"] is None


def test_ordinary_mutation_keeps_previous_json_shape():
    assert "shared_index_projection" not in result().to_wire()


def test_closeout_index_fields_require_actual_publication_coordinate():
    with pytest.raises(
        IssueOperationContractError, match="closeout publication receipt"
    ):
        result(index_reconciliation_pending=False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("shared_index_projection", "clean"),
        ("shared_index_projection", []),
        ("index_reconciliation_pending", "false"),
        ("index_reconciliation_pending", 0),
        ("shared_index_projection_error", ""),
    ],
)
def test_closeout_index_types_are_checked(field, value):
    with pytest.raises(IssueOperationContractError):
        result(closeout_publication_receipt_ref="git:" + "a" * 40, **{field: value})


def test_pending_closeout_preserves_typed_owner_result():
    value = result(
        closeout_publication_receipt_ref="git:" + "a" * 40,
        shared_index_projection="failed",
        shared_index_projection_error="shared_index_lock_busy",
        index_reconciliation_pending=True,
    )
    assert value.to_wire()["index_reconciliation_pending"] is True
    with pytest.raises(IssueOperationContractError):
        replace(value, outcome=IssueMutationOutcome.INVALID)
