"""The CLI preserves SDK failure meaning instead of relabeling it request-invalid."""

import json

import pytest
from aware_issue_cli.main import main
from aware_issue_sdk import IssueCommitWorkspaceResult, IssuePublicationOutcome


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("mode", ["foreign", "untyped", "raised"])
def test_late_failure_preserves_unvalidated_publication_report(
    monkeypatch, capsys, format_name, mode
):
    calls = []
    reported = IssueCommitWorkspaceResult(
        outcome=IssuePublicationOutcome.APPLIED,
        issue_ref="fb/2026-10-08/foreign"
        if mode == "foreign"
        else "fb/2026-10-08/current",
        target_paths=("src/a.py",),
        provider_ref="test.provider",
        provider_distribution="test-provider",
        provider_version="1.0.0",
        operator_ref="test.operator",
        transaction_mode="isolated_index_atomic_ref_v1",
        commit_hash="a" * 40,
        reference_update="cas_applied",
        shared_index_projection="failed",
        shared_index_projection_error="pending-proof",
        index_reconciliation_pending=True,
        evidence=("publication:retained",),
    )

    class Provider:
        def commit_workspace(self, operation_request):
            calls.append(operation_request)
            if mode == "raised":
                error = ValueError("failure after publication")
                error.provider_result = reported
                raise error
            return reported.to_wire() if mode == "untyped" else reported

    monkeypatch.setattr(
        "aware_issue_cli.main.FilesystemIssueOperationProvider",
        lambda **kwargs: Provider(),
    )
    assert (
        main(
            [
                "commit-workspace",
                "--repository-root",
                "/unused",
                "--issue-ref",
                "fb/2026-10-08/current",
                "--expected-issue-source-sha256",
                "sha256:" + "b" * 64,
                "--path",
                "src/a.py",
                "--message",
                "test",
                "--actor-ref",
                "codex-test",
                "--actor-evidence-ref",
                "evidence:test",
                "--format",
                format_name,
            ]
        )
        == 2
    )
    assert len(calls) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == (
        "provider_invocation_failed" if mode == "raised" else "provider_result_invalid"
    )
    assert payload["phase"] == ("provider" if mode == "raised" else "result")
    assert payload["effect"] == "unknown"
    assert payload["provider_invoked"] is True
    assert payload["authorizes_retry"] is False
    assert payload["issue_ref"] == "fb/2026-10-08/current"
    assert payload["provider_report_grade"] == "unvalidated_provider_report"
    report = payload["provider_result"]
    assert report["publication_receipt_ref"] == "git:" + "a" * 40
    assert report["operator_ref"] == "test.operator"
    assert report["reference_update"] == "cas_applied"
    assert report["transaction_mode"] == "isolated_index_atomic_ref_v1"
    assert report["shared_index_projection_error"] == "pending-proof"
    assert report["index_reconciliation_pending"] is True
    assert report["evidence"] == ["publication:retained"]
    assert report["issue_ref"] == reported.issue_ref
    assert "projection" not in report
    if format_name == "summary":
        assert payload["publication_receipt_ref"] is None
        assert payload["next_action"]["authorizes_retry"] is False
