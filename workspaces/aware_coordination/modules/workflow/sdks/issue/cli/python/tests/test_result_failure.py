"""Genuine publication followed by lossless consumer-return refusal."""

import importlib
import json

import pytest
from test_repository_runtime_orchestration import composed_loop
from test_sdk_return_failure import ReturnedFailure

composed = composed_loop
cli = importlib.import_module("aware_issue_cli.main")


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("mode", ["foreign", "untyped", "raised"])
def test_late_failure_preserves_unvalidated_publication_report(
    composed, monkeypatch, capsys, format_name, mode
):
    root, _, _, runtime, repository_client, request = composed
    wrapped = ReturnedFailure(
        runtime, "commit_workspace_result", "raise" if mode == "raised" else mode
    )
    monkeypatch.setattr(
        runtime, "commit_workspace_result", wrapped.commit_workspace_result
    )
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    assert (
        cli.main(
            [
                "commit-workspace",
                "--repository-root",
                str(root),
                "--issue-ref",
                request.issue_ref,
                "--expected-issue-source-sha256",
                request.expected_issue_source_sha256,
                "--path",
                "src/example.py",
                "--message",
                request.message,
                "--actor-ref",
                request.actor_ref,
                "--actor-evidence-ref",
                request.actor_evidence_ref,
                "--format",
                format_name,
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)
    assert wrapped.calls == 1
    assert payload["phase"] == "consumer_return"
    assert payload["effect"] == "unknown" and payload["authorizes_retry"] is False
    assert payload["issue_ref"] == request.issue_ref
    retained = payload["consumer_result"]
    assert retained["workspace_result"]["publication_state"] == "published"
    assert retained["workspace_result"]["reference_update"] == "cas_applied"
    assert len(retained["workspace_result"]["original_writer_report"]) == 32
    assert retained["issue_observation"]["consumption_state"] == "consumed"
    assert retained["issue_ref"] == (
        "fb/2026-10-08/foreign" if mode == "foreign" else request.issue_ref
    )
    assert (
        payload["code"]
        == {
            "foreign": "issue_repository_result_correlation_mismatch",
            "untyped": "issue_repository_result_type_invalid",
            "raised": "issue_repository_result_return_unavailable",
        }[mode]
    )
