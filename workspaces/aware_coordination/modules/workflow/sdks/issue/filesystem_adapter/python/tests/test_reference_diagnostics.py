"""Owner-issued reference guidance; SDKs transport it without interpreting it."""

from __future__ import annotations

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueSdkOperationClient,
    IssueStartProgressRequest,
)
from test_provider import _repository

GUIDANCE = (
    "issue_ref_invalid",
    "Expected fb/YYYY-MM-DD/<slug>; use lowercase letters or digits separated by single hyphens.",
    "Example: fb/2026-10-11/json-checker-draft. Supply the Issue reference, not a Markdown path.",
)
INVALID_REFS = (
    "docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md",
    "/docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md",
    "fb/2026/10/11/json-checker-draft",
    "fb/2026-10-11/JSON-checker",
    "fb/2026-10-11/json_checker",
    "fb/2026-10-11/json--checker",
    "fb/2026-10-11/-json-checker",
    "fb/2026-10-11/json-checker/extra",
)


@pytest.mark.parametrize("issue_ref", INVALID_REFS)
@pytest.mark.parametrize("operation", ["read", "ensure", "start"])
def test_invalid_reference_guidance_survives_sdk_without_target_access(
    tmp_path, monkeypatch, issue_ref, operation
):
    # The target need not exist: syntax refusal precedes manifest admission/IO.
    repository = tmp_path / "uncreated-repository"
    provider = FilesystemIssueOperationProvider(repository_root=repository)

    def forbidden():
        raise AssertionError("Invalid references must not admit or inspect a target")

    monkeypatch.setattr(provider, "_admit_manifest", forbidden)
    client = IssueSdkOperationClient(provider=provider)
    if operation == "read":
        result = client.resolve_read_projection(
            IssueReadProjectionResolveRequest(issue_ref=issue_ref)
        )
        assert result.outcome is IssueReadProjectionResolveOutcome.MALFORMED
    elif operation == "ensure":
        result = client.ensure_issue_snapshot(
            IssueEnsureSnapshotRequest(
                issue_ref=issue_ref,
                title="JSON checker",
                priority="P1",
                client_intent_id="test:reference-guidance",
                actor_ref="codex-reference-test",
                actor_evidence_ref="test:synthetic-harness",
            )
        )
        assert result.outcome is IssueMutationOutcome.MALFORMED
    else:
        result = client.start_issue_progress(
            IssueStartProgressRequest(
                issue_ref=issue_ref,
                expected_source_sha256="sha256:" + "0" * 64,
                client_intent_id="test:reference-guidance",
                actor_ref="codex-reference-test",
                actor_evidence_ref="test:synthetic-harness",
            )
        )
        assert result.outcome is IssueMutationOutcome.MALFORMED
    assert result.issue_ref == issue_ref
    assert result.diagnostics == GUIDANCE
    assert result.to_wire()["diagnostics"] == list(GUIDANCE)
    assert not repository.exists()


@pytest.mark.parametrize("slug", ["json-checker-draft", "v2-checker", "123"])
def test_help_example_and_existing_alphanumeric_slugs_remain_accepted(tmp_path, slug):
    repository = _repository(tmp_path)
    reference = f"fb/2026-10-11/{slug}"
    result = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).resolve_read_projection(IssueReadProjectionResolveRequest(issue_ref=reference))
    assert result.outcome is IssueReadProjectionResolveOutcome.ABSENT
    assert "issue_ref_invalid" not in result.diagnostics
