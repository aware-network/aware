from copy import deepcopy

import pytest
from aware_issue_cli.summary import summarize_result
from aware_issue_sdk import IssueCommitWorkspaceResult, IssuePublicationOutcome


@pytest.mark.parametrize(
    ("outcome", "reference_update", "commit_hash", "diagnostics"),
    [
        (IssuePublicationOutcome.APPLIED, "cas_applied", "a" * 40, ()),
        (IssuePublicationOutcome.CONFLICT, "cas_failed", None, ("fixture:cas_failed",)),
    ],
)
def test_publication_summary_preserves_success_and_refusal_evidence(
    outcome, reference_update, commit_hash, diagnostics
):
    # Typed transport fixtures test presentation, not repository admission.
    sdk = IssueCommitWorkspaceResult(
        outcome=outcome,
        issue_ref="fixture:issue",
        target_paths=("owned.txt",),
        provider_ref="fixture:filesystem-provider",
        provider_distribution="aware-issue-fs-adapter",
        provider_version="fixture-version",
        operator_ref="fixture:shared-repository-owner",
        transaction_mode="isolated_index_atomic_ref_v1",
        reference_update=reference_update,
        commit_hash=commit_hash,
        diagnostics=diagnostics,
    )
    wire = sdk.to_wire()
    before = deepcopy(wire)
    summary = summarize_result(wire)
    for field in (
        "operator_ref",
        "transaction_mode",
        "reference_update",
        "outcome",
        "publication_receipt_ref",
        "diagnostics",
    ):
        assert summary[field] == wire[field]
    assert wire == before
    nested = summarize_result({"atomic": False, "receipts": [wire]})
    assert nested["receipts"][0]["reference_update"] == reference_update
    assert nested["receipts"][0]["operator_ref"] == sdk.operator_ref
    assert nested["receipts"][0]["transaction_mode"] == sdk.transaction_mode


def test_summary_is_read_only_and_preserves_exact_fields():
    payload = {
        "outcome": "applied",
        "operation_ref": "issue_sdk.close_issue",
        "issue_ref": "fixture:issue",
        "diagnostics": ["fixture:warning"],
        "evidence": ["projection_effect:issue_day_index:pending"],
        "closeout_publication_receipt_ref": "git:exact-receipt",
        "index_reconciliation_pending": True,
        "shared_index_projection": "failed",
        "shared_index_projection_error": "shared_index_lock_busy",
        "projection": {
            "identity": {"owner_ref": "codex-fixture", "status": "closed"},
            "content": {
                "goal_items": ["Approved objective"],
                "problem_items": ["Known problem"],
                "ownership_scope": ["owned.txt"],
                "acceptance_items": [{"text": "Explicit check", "checked": False}],
            },
            "source": {"digest": "sha256:exact-source"},
            "activity": [{"text": "first"}, {"text": "latest"}],
        },
    }
    before = deepcopy(payload)
    result = summarize_result(payload)
    assert payload == before
    assert result["objective"] == ["Approved objective"]
    assert result["acceptance"] == [{"text": "Explicit check", "checked": False}]
    assert result["identity"]["status"] == "closed"
    assert result["closeout_publication_receipt_ref"] == "git:exact-receipt"
    assert result["index_result"]["index_reconciliation_pending"] is True
    assert (
        result["index_result"]["shared_index_projection_error"]
        == "shared_index_lock_busy"
    )
    assert result["evidence"] == payload["evidence"]


def test_missing_historical_index_evidence_is_unknown():
    result = summarize_result(
        {"outcome": "applied", "closeout_publication_receipt_ref": "git:old"}
    )
    assert result["index_result"]["index_reconciliation_pending"] == "unknown"
    assert result["index_result"]["shared_index_projection"] == "unknown"
    for field in ("operator_ref", "transaction_mode", "reference_update"):
        assert result[field] is None


def test_day_index_evidence_is_not_git_index_evidence():
    result = summarize_result(
        {"evidence": ["projection_effect:issue_day_index:applied"]}
    )
    assert result["index_result"]["shared_index_projection"] == "unknown"


def test_partial_composition_preserves_each_constituent_receipt():
    result = summarize_result(
        {
            "outcome": "incomplete",
            "atomic": False,
            "receipts": [
                {"outcome": "applied", "source_sha256_after": "sha256:one"},
                {
                    "outcome": "stale",
                    "diagnostics": ["expected_source_sha256_mismatch"],
                },
            ],
        }
    )
    assert result["atomic"] is False
    assert [r["outcome"] for r in result["receipts"]] == ["applied", "stale"]
    assert result["receipts"][0]["source_sha256_after"] == "sha256:one"
    assert result["receipts"][1]["diagnostics"] == ["expected_source_sha256_mismatch"]


def test_explicit_false_is_not_unknown_or_truthiness_coerced():
    result = summarize_result(
        {"shared_index_projection": "applied", "index_reconciliation_pending": False}
    )
    assert result["index_result"]["index_reconciliation_pending"] is False
