from __future__ import annotations

import pytest
from aware_issue_runtime import parse_issue_projection
from aware_issue_sdk import (
    ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF,
    IssueCommitWorkspaceRequest,
    IssueCommitWorkspaceResult,
    IssueOperationContractError,
    IssuePublicationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveResult,
    IssueSdkOperationClient,
    IssueSetOwnerRequest,
)

ISSUE_REF = "fb/2026-09-20/example"


class _Provider:
    def resolve_read_projection(
        self, request: IssueReadProjectionResolveRequest
    ) -> IssueReadProjectionResolveResult:
        projection = parse_issue_projection(
            text=f"# Issue: Example\n\n- Tag: `{request.issue_ref}`\n",
            source_path="docs/issues/2026/09/20/fb-2026-09-20-example.md",
        )
        return IssueReadProjectionResolveResult(
            outcome=IssueReadProjectionResolveOutcome.FOUND,
            issue_ref=request.issue_ref,
            projection=projection,
            provider_ref="test.issue.provider",
            provider_distribution="test-issue-provider",
            provider_version="1.0.0",
        )


def test_client_delegates_canonical_issue_read() -> None:
    result = IssueSdkOperationClient(provider=_Provider()).resolve_read_projection(
        IssueReadProjectionResolveRequest(issue_ref=ISSUE_REF)
    )

    assert result.outcome is IssueReadProjectionResolveOutcome.FOUND
    assert result.operation_ref == ISSUE_RESOLVE_READ_PROJECTION_OPERATION_REF
    assert result.projection is not None
    assert result.to_wire()["projection"]["source"]["raw_markdown"] is None  # type: ignore[index]


def test_result_rejects_projection_identity_mismatch() -> None:
    projection = parse_issue_projection(
        text="# Issue: Other\n\n- Tag: `fb/2026-09-20/other`\n",
        source_path="docs/issues/2026/09/20/fb-2026-09-20-other.md",
    )

    with pytest.raises(IssueOperationContractError):
        IssueReadProjectionResolveResult(
            outcome=IssueReadProjectionResolveOutcome.FOUND,
            issue_ref=ISSUE_REF,
            projection=projection,
            provider_ref="test.issue.provider",
            provider_distribution="test-issue-provider",
            provider_version="1.0.0",
        )


def test_non_found_result_cannot_carry_projection() -> None:
    projection = parse_issue_projection(
        text=f"# Issue: Example\n\n- Tag: `{ISSUE_REF}`\n",
        source_path="docs/issues/2026/09/20/fb-2026-09-20-example.md",
    )

    with pytest.raises(IssueOperationContractError):
        IssueReadProjectionResolveResult(
            outcome=IssueReadProjectionResolveOutcome.ABSENT,
            issue_ref=ISSUE_REF,
            projection=projection,
            provider_ref="test.issue.provider",
            provider_distribution="test-issue-provider",
            provider_version="1.0.0",
        )


def test_publication_contract_requires_exact_paths_and_emits_git_receipt() -> None:
    with pytest.raises(IssueOperationContractError):
        IssueCommitWorkspaceRequest(
            issue_ref=ISSUE_REF,
            expected_issue_source_sha256="sha256:" + "a" * 64,
            target_paths=(),
            message="publish",
            actor_ref="codex-example",
            actor_evidence_ref="evidence:one",
            dry_run=True,
        )

    result = IssueCommitWorkspaceResult(
        outcome=IssuePublicationOutcome.APPLIED,
        issue_ref=ISSUE_REF,
        target_paths=("src/example.py",),
        provider_ref="test.issue.provider",
        provider_distribution="test-issue-provider",
        provider_version="1.0.0",
        operator_ref="test.workspace.operator",
        transaction_mode="isolated_index_atomic_ref_v1",
        commit_hash="a" * 40,
        reference_update="cas_applied",
    )

    assert result.publication_receipt_ref == f"git:{'a' * 40}"
    assert result.to_wire()["publication_receipt_ref"] == f"git:{'a' * 40}"


def test_owner_handoff_contract_requires_explicit_replacement() -> None:
    with pytest.raises(IssueOperationContractError, match="new_owner_ref"):
        IssueSetOwnerRequest(
            issue_ref=ISSUE_REF,
            expected_source_sha256="sha256:" + "a" * 64,
            client_intent_id="handoff",
            actor_ref="codex-current",
            actor_evidence_ref="evidence:handoff",
            new_owner_ref="",
        )
