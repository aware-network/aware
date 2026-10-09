import hashlib
import json
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


@pytest.mark.parametrize(
    "payload",
    [
        {"receipts": [None]},
        {"receipts": [{"observation": {"receipts": [None]}}]},
        {"unused": {"nested": [float("inf")]}},
        {"unused": float("-inf")},
        {"unused": float("nan")},
    ],
)
def test_direct_summary_refuses_malformed_data_with_value_error(payload):
    with pytest.raises(ValueError):
        summarize_result(payload)


@pytest.mark.parametrize("count", [1, 1000])
def test_history_omission_is_explicit_digest_bound_and_does_not_modify_full_result(
    count,
):
    history = [
        {"path": f"evidence/{i}.json", "description": "historical " + "x" * 256}
        for i in range(count)
    ]
    payload = {
        "operation_ref": "issue_sdk.resolve_issue_read_projection",
        "outcome": "found",
        "issue_ref": "fixture:issue",
        "evidence": ["current:unchanged"],
        "projection": {
            "evidence": history,
            "source": {"path": "docs/issues/issue.md", "digest": "sha256:source"},
        },
    }
    original = deepcopy(payload)
    summary = summarize_result(payload)
    omitted = summary["recorded_evidence"]
    encoded = json.dumps(
        history, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    assert omitted["sha256"] == "sha256:" + hashlib.sha256(encoded).hexdigest()
    assert omitted["size_bytes"] == len(encoded)
    assert omitted["omitted"] is True and omitted["count"] == count
    assert omitted["source"] == payload["projection"]["source"]
    assert omitted["availability"] == "not_retained_by_this_renderer"
    assert summary["evidence"] == payload["evidence"]
    assert payload == original
    full_bytes, summary_bytes = (
        len(json.dumps(payload, sort_keys=True).encode()),
        len(json.dumps(summary, sort_keys=True).encode()),
    )
    print(f"MEASURE count={count} full={full_bytes} summary={summary_bytes}")
    if count == 1000:
        assert (
            summary_bytes < full_bytes / 20
        )  # Fixture proof, not a universal output budget.


@pytest.mark.parametrize(
    "outcome,reference,pending",
    [
        ("applied", "cas_applied", False),
        ("conflict", "cas_failed", None),
        ("incomplete", "cas_applied", True),
        ("unknown", "unknown", None),
    ],
)
def test_concise_view_preserves_publication_failure_and_cleanup_uncertainty(
    outcome, reference, pending
):
    payload = {
        "operation_ref": "issue_sdk.commit_workspace",
        "outcome": outcome,
        "operator_ref": "original:operator",
        "transaction_mode": "isolated_index_atomic_ref_v1",
        "reference_update": reference,
        "index_reconciliation_pending": pending,
        "publication_outcome": "unknown" if outcome == "unknown" else outcome,
        "diagnostics": ["primary_failure", "cleanup_unknown"],
        "effects": [{"path": "owned", "state": "applied"}],
        "cleanup": {"outcome": "unknown", "attempted": None},
        "evidence": ["large current operation evidence:" + "e" * 10000],
    }
    summary = summarize_result(payload)
    for field in (
        "outcome",
        "operator_ref",
        "transaction_mode",
        "reference_update",
        "publication_outcome",
        "diagnostics",
        "effects",
        "cleanup",
        "evidence",
    ):
        assert summary[field] == payload[field]
    assert summary["currentness"] is None
    assert summary["next_action"]["authorizes_retry"] is False
    assert summary["next_action"]["restores_custody"] is False
    assert summary["index_result"]["index_reconciliation_pending"] == (
        "unknown" if pending is None else pending
    )
