from __future__ import annotations

import hashlib
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueAppendEvidenceRequest,
    IssueAppendUpdateRequest,
    IssueBindScopePathsRequest,
    IssueBlockRequest,
    IssueCloseRequest,
    IssueCommitWorkspaceRequest,
    IssueEnsureSnapshotRequest,
    IssueMutationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueResumeRequest,
    IssueSdkOperationClient,
    IssueSetOwnerRequest,
    IssueStartProgressRequest,
)

ISSUE_REF = "fb/2026-09-20/example"


@pytest.fixture(autouse=True)
def harness_identity(monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)


def _publication_client(repository):
    from aware_issue_fs_adapter.repository_publication import (
        FilesystemIssueRepositorySourcePort,
    )
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )
    from aware_issue_sdk.repository_publication import IssueRepositoryPublicationClient
    from aware_workspace_fs_adapter.repository_publication import (
        FilesystemRepositoryCandidatePort,
    )
    from aware_workspace_runtime.repository_publication import (
        WorkspaceRepositoryPublicationRuntime,
    )
    from aware_workspace_sdk.repository_publication.authority import (
        WorkspaceRepositoryPublicationClient,
    )

    provider = FilesystemIssueOperationProvider(repository_root=repository)
    workspace = WorkspaceRepositoryPublicationClient(
        WorkspaceRepositoryPublicationRuntime(
            FilesystemRepositoryCandidatePort(repository_root=repository)
        )
    )
    return IssueSdkOperationClient(
        provider=provider,
        repository_client=IssueRepositoryPublicationClient(
            IssueRepositoryPublicationRuntime(
                source_port=FilesystemIssueRepositorySourcePort(provider),
                workspace_client=workspace,
            )
        ),
    )


def _manifest(*, issue_profile: str = "aware.issue.markdown.v1") -> str:
    return f'''aware = 1

[protocol]
name = "aware.collaboration"
profile = "aware.collaboration.fs_v1"
semantic_version = 1

[target]
kind = "repository"
authority_mode = "filesystem"

[bootstrap]
agent_contract = "AGENTS.md"

[records.goal]
profile = "aware.goal.markdown.v1"
root = "docs/goals"
role = "authority"
path_template = "YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md"

[records.issue]
profile = "{issue_profile}"
root = "docs/issues"
role = "authority"
path_template = "YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md"

[records.feed]
profile = "aware.feed.projection.v1"
role = "unavailable"

[records.specification]
profile = "specification_fs_v1"
root = "docs/specs"
role = "authority"
path_template = "<spec-key>/aware.spec.toml"

[records.evidence]
profile = "aware.protocol.evidence.v1"
root = "docs/coordination/evidence"
role = "authority"
path_template = "<kind>/<stable-id>.json"
'''


def _issue(
    *,
    issue_ref: str = ISSUE_REF,
    status: str = "In Progress",
) -> str:
    return f"""# Issue: Example

- Slug: `example`
- Tag: `{issue_ref}`
- Status: {status}
- Owner: `codex-example`
- Priority: P1
- Goal: `goal/2026-09-20/example`
- Captured: 2026-09-20
- Recorder: `codex-example`
- Source: Test fixture

## Ownership Scope
- `src/example.py`

## Updates (append-only)
- 2026-09-20T00:00:00Z — Started. (recorder: `codex-example`)
"""


def _repository(tmp_path: Path) -> Path:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agent contract\n", encoding="utf-8")
    issue = tmp_path / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.parent.mkdir(parents=True)
    issue.write_text(_issue(), encoding="utf-8")
    return tmp_path


def _resolve(repository: Path):
    return IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).resolve_read_projection(IssueReadProjectionResolveRequest(issue_ref=ISSUE_REF))


def _digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _mutation_kwargs(issue: Path, *, intent: str) -> dict[str, str]:
    return {
        "issue_ref": ISSUE_REF,
        "expected_source_sha256": _digest(issue),
        "client_intent_id": intent,
        "actor_ref": "codex-example",
        "actor_evidence_ref": f"evidence:{intent}",
    }


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _publication_repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = _repository(tmp_path)
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.name", "Aware Test")
    _git(repository, "config", "user.email", "aware-test@example.invalid")
    target = repository / "src/example.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "seed")
    target.write_text("after\n", encoding="utf-8")
    return repository, target


def _publish_implementation(
    *, repository: Path, issue: Path, client: IssueSdkOperationClient
) -> str:
    _git(repository, "add", issue.relative_to(repository).as_posix())
    _git(repository, "commit", "-m", "admit closeout scope")
    publication = client.commit_workspace(
        IssueCommitWorkspaceRequest(
            issue_ref=ISSUE_REF,
            expected_issue_source_sha256=_digest(issue),
            target_paths=("src/example.py",),
            message="publish implementation",
            actor_ref="codex-example",
            actor_evidence_ref="evidence:implementation",
            dry_run=False,
        )
    )
    assert publication.outcome == "completed"
    return "git:" + publication.to_wire()["workspace_result"]["commit_hash"]


def test_filesystem_provider_resolves_strict_issue(tmp_path: Path) -> None:
    result = _resolve(_repository(tmp_path))

    assert result.outcome is IssueReadProjectionResolveOutcome.FOUND
    assert result.projection is not None
    assert result.projection.issue_ref == ISSUE_REF
    assert result.projection.owner_ref == "codex-example"
    assert result.projection.ownership_scope == ("src/example.py",)
    assert any(item.startswith("source_sha256:sha256:") for item in result.evidence)


def test_absent_issue_does_not_create_or_select_work(tmp_path: Path) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")

    result = _resolve(tmp_path)

    assert result.outcome is IssueReadProjectionResolveOutcome.ABSENT
    assert result.projection is None
    assert not (tmp_path / "docs/issues").exists()


def test_identity_mismatch_is_malformed(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(_issue(issue_ref="fb/2026-09-20/other"), encoding="utf-8")

    result = _resolve(repository)

    assert result.outcome is IssueReadProjectionResolveOutcome.MALFORMED
    assert result.diagnostics == ("issue_identity_mismatch:fb/2026-09-20/other",)


def test_duplicate_issue_identity_is_malformed(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    duplicate = repository / "docs/issues/2026/09/19/fb-2026-09-19-copy.md"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text(_issue(), encoding="utf-8")

    result = _resolve(repository)

    assert result.outcome is IssueReadProjectionResolveOutcome.MALFORMED
    assert result.diagnostics == ("issue_identity_duplicate_matches:2",)


def test_unknown_issue_profile_is_refused_by_protocol_admission(
    tmp_path: Path,
) -> None:
    (tmp_path / "aware.protocol.toml").write_text(
        _manifest(issue_profile="aware.issue.markdown.v999"),
        encoding="utf-8",
    )

    result = _resolve(tmp_path)

    assert result.outcome is IssueReadProjectionResolveOutcome.UNSUPPORTED_PROFILE
    assert result.diagnostics == (
        "record_profile_mismatch:issue:aware.issue.markdown.v999",
    )


def test_ensure_creates_then_idempotently_observes_issue(tmp_path: Path) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agent contract\n", encoding="utf-8")
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=tmp_path)
    )
    request = IssueEnsureSnapshotRequest(
        issue_ref=ISSUE_REF,
        title="Example",
        priority="P1",
        owner_ref="codex-example",
        goal_ref="goal/2026-09-20/example",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:ensure",
        client_intent_id="ensure-1",
    )

    created = client.ensure_issue_snapshot(request)
    observed = client.ensure_issue_snapshot(request)

    assert created.outcome is IssueMutationOutcome.APPLIED
    assert observed.outcome is IssueMutationOutcome.IDEMPOTENT
    assert created.source_sha256_after == observed.source_sha256_after


def test_start_progress_uses_state_machine_and_source_cas(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(_issue(status="Open"), encoding="utf-8")
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    )
    request = IssueStartProgressRequest(**_mutation_kwargs(issue, intent="start-1"))

    result = client.start_issue_progress(request)

    assert result.outcome is IssueMutationOutcome.APPLIED
    assert result.projection is not None
    assert result.projection.status == "in_progress"
    assert "issue_sdk.start_issue_progress" in issue.read_text(encoding="utf-8")

    stale = client.start_issue_progress(request)
    assert stale.outcome is IssueMutationOutcome.STALE


def test_resume_rejects_non_blocked_issue_without_mutation(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    before = issue.read_bytes()
    request = IssueResumeRequest(**_mutation_kwargs(issue, intent="resume-1"))

    result = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).resume_issue(request)

    assert result.outcome is IssueMutationOutcome.INVALID
    assert result.diagnostics == ("invalid_lifecycle_transition",)
    assert issue.read_bytes() == before


def test_block_transfer_and_replacement_resume_are_digest_bound(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    )

    blocked = client.block_issue(
        IssueBlockRequest(**_mutation_kwargs(issue, intent="block-handoff"))
    )
    assert blocked.outcome is IssueMutationOutcome.APPLIED
    assert blocked.projection is not None
    assert blocked.projection.status == "blocked"

    before_foreign = issue.read_bytes()
    foreign = client.set_issue_owner(
        IssueSetOwnerRequest(
            **{
                **_mutation_kwargs(issue, intent="foreign-handoff"),
                "actor_ref": "codex-foreign",
            },
            new_owner_ref="codex-replacement",
        )
    )
    assert foreign.outcome is IssueMutationOutcome.UNAUTHORIZED
    assert foreign.diagnostics == ("issue_owner_transfer_actor_mismatch",)
    assert issue.read_bytes() == before_foreign

    transferred = client.set_issue_owner(
        IssueSetOwnerRequest(
            **_mutation_kwargs(issue, intent="owner-handoff"),
            new_owner_ref="codex-replacement",
        )
    )
    assert transferred.outcome is IssueMutationOutcome.APPLIED
    assert transferred.projection is not None
    assert transferred.projection.status == "blocked"
    assert transferred.projection.owner_ref == "codex-replacement"

    former_owner = client.resume_issue(
        IssueResumeRequest(
            **{
                **_mutation_kwargs(issue, intent="former-owner-resume"),
                "actor_ref": "codex-example",
            }
        )
    )
    assert former_owner.outcome is IssueMutationOutcome.UNAUTHORIZED
    assert former_owner.diagnostics == ("issue_owner_mismatch",)

    replacement = client.resume_issue(
        IssueResumeRequest(
            **{
                **_mutation_kwargs(issue, intent="replacement-resume"),
                "actor_ref": "codex-replacement",
                "actor_evidence_ref": "evidence:replacement-resume",
            }
        )
    )
    assert replacement.outcome is IssueMutationOutcome.APPLIED
    assert replacement.projection is not None
    assert replacement.projection.status == "in_progress"
    assert replacement.projection.owner_ref == "codex-replacement"


def test_mutation_rejects_actor_that_is_not_authored_owner(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    before = issue.read_bytes()
    request = IssueAppendUpdateRequest(
        **{
            **_mutation_kwargs(issue, intent="wrong-owner-1"),
            "actor_ref": "codex-other",
        },
        message="Must not be appended.",
    )

    result = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).append_issue_update(request)

    assert result.outcome is IssueMutationOutcome.UNAUTHORIZED
    assert result.diagnostics == ("issue_owner_mismatch",)
    assert issue.read_bytes() == before


def test_scope_update_and_evidence_preserve_one_cas_chain(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    )
    scope = client.bind_issue_scope_paths(
        IssueBindScopePathsRequest(
            **_mutation_kwargs(issue, intent="scope-1"),
            scope_paths=("src/a.py", "src/b.py"),
        )
    )
    assert scope.outcome is IssueMutationOutcome.APPLIED
    update = client.append_issue_update(
        IssueAppendUpdateRequest(
            **_mutation_kwargs(issue, intent="update-1"),
            message="Implemented bounded behavior.",
            outcome="passed",
        )
    )
    assert update.outcome is IssueMutationOutcome.APPLIED
    evidence = client.append_issue_evidence(
        IssueAppendEvidenceRequest(
            **_mutation_kwargs(issue, intent="evidence-1"),
            path="reports/proof.json",
            description="Installed proof",
        )
    )

    assert evidence.outcome is IssueMutationOutcome.APPLIED
    assert evidence.projection is not None
    assert evidence.projection.ownership_scope == ("src/a.py", "src/b.py")
    assert evidence.projection.activities[-1].outcome == "passed"
    assert evidence.projection.evidence[-1].reference.startswith("reports/proof.json")


def test_close_requires_evidence_and_publication_receipt(tmp_path: Path) -> None:
    repository, _target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text().replace(
            "- `src/example.py`",
            "- `src/example.py`\n- `" + issue.relative_to(repository).as_posix() + "`",
        )
    )
    client = _publication_client(repository)
    receipt = _publish_implementation(repository=repository, issue=issue, client=client)
    result = client.close_issue(
        IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-1"),
            resolution="Completed bounded work.",
            verified_by=("reports/review.md",),
            publication_receipt_ref=receipt,
        )
    )
    assert result.outcome == "completed"
    payload = result.to_wire()
    assert (
        payload["issue_observation"]["implementation_publication_receipt_ref"]
        == receipt
    )
    assert (
        payload["issue_observation"]["source_observation"]["source_change_state"]
        == "applied"
    )
    assert payload["workspace_result"]["reference_update"] == "cas_applied"
    projection = client.resolve_read_projection(
        IssueReadProjectionResolveRequest(issue_ref=ISSUE_REF)
    ).projection
    assert (
        projection.status == "closed"
        and projection.resolution == "Completed bounded work."
    )
    assert (
        _git(repository, "show", "HEAD:" + issue.relative_to(repository).as_posix())
        == issue.read_text().rstrip()
    )


def test_initial_authored_content_and_conflicting_ensure(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.unlink()  # remove only this synthetic fixture's seeded Issue
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    )
    request = IssueEnsureSnapshotRequest(
        issue_ref=ISSUE_REF,
        title="Example",
        priority="P1",
        actor_ref="codex-example",
        owner_ref="codex-example",
        actor_evidence_ref="fixture:actor",
        client_intent_id="fixture:content",
        problem_items=("Readers lose the approved request.",),
        objective_items=("Keep the approved work durable.",),
        acceptance_items=(
            "Reject changes outside the approved scope.",
            "Preserve [x] as plain text.",
        ),
    )
    created = client.ensure_issue_snapshot(request)
    assert created.outcome is IssueMutationOutcome.APPLIED
    assert created.projection.problem_items == request.problem_items
    assert created.projection.goal_items == request.objective_items
    assert (
        tuple(item.text for item in created.projection.acceptance_items)
        == request.acceptance_items
    )
    assert all(not item.checked for item in created.projection.acceptance_items)
    before = issue.read_bytes()
    assert (
        client.ensure_issue_snapshot(request).outcome is IssueMutationOutcome.IDEMPOTENT
    )
    for field in ("problem_items", "objective_items", "acceptance_items"):
        refused = client.ensure_issue_snapshot(
            replace(request, **{field: ("Different approved content.",)})
        )
        assert refused.outcome is IssueMutationOutcome.CONFLICT
        assert refused.diagnostics == (
            "issue_authored_content_already_exists_with_other_values",
        )
        assert issue.read_bytes() == before
    legacy = replace(request, problem_items=(), objective_items=(), acceptance_items=())
    assert (
        client.ensure_issue_snapshot(legacy).outcome is IssueMutationOutcome.IDEMPOTENT
    )
    assert issue.read_bytes() == before


def test_authored_content_survives_real_publication_and_closeout(
    tmp_path: Path,
) -> None:
    repository, _target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.unlink()  # replace only the seeded synthetic record through its owner
    client = _publication_client(repository)
    request = IssueEnsureSnapshotRequest(
        issue_ref=ISSUE_REF,
        title="Example",
        priority="P1",
        owner_ref="codex-example",
        actor_ref="codex-example",
        actor_evidence_ref="fixture:actor",
        client_intent_id="fixture:authored-closeout",
        problem_items=("Execution history loses the approved request.",),
        objective_items=("Preserve the approved request in the Issue.",),
        acceptance_items=("Retain evidence without manufacturing acceptance.",),
    )
    assert client.ensure_issue_snapshot(request).outcome is IssueMutationOutcome.APPLIED
    assert (
        client.bind_issue_scope_paths(
            IssueBindScopePathsRequest(
                **_mutation_kwargs(issue, intent="authored-scope"),
                scope_paths=(
                    "src/example.py",
                    issue.relative_to(repository).as_posix(),
                ),
            )
        ).outcome
        is IssueMutationOutcome.APPLIED
    )
    assert (
        client.start_issue_progress(
            IssueStartProgressRequest(
                **_mutation_kwargs(issue, intent="authored-start")
            )
        ).outcome
        is IssueMutationOutcome.APPLIED
    )
    receipt = _publish_implementation(repository=repository, issue=issue, client=client)
    closed = client.close_issue(
        IssueCloseRequest(
            **_mutation_kwargs(issue, intent="authored-close"),
            resolution="Delivered the bounded change; criteria remain authored evidence.",
            verified_by=("fixture:focused-proof",),
            publication_receipt_ref=receipt,
        )
    )
    assert closed.outcome == "completed"
    projection = client.resolve_read_projection(
        IssueReadProjectionResolveRequest(issue_ref=ISSUE_REF)
    ).projection
    assert projection.status == "closed"
    assert projection.problem_items == request.problem_items
    assert projection.goal_items == request.objective_items
    assert tuple(item.text for item in projection.acceptance_items) == (
        request.acceptance_items
    )
    assert all(not item.checked for item in projection.acceptance_items)
    assert _git(
        repository, "show", "HEAD:" + issue.relative_to(repository).as_posix()
    ) == (issue.read_text().rstrip())


def test_closeout_pending_index_is_reported_without_repair(tmp_path: Path) -> None:
    repository, _target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text().replace(
            "- `src/example.py`",
            "- `src/example.py`\n- `" + issue.relative_to(repository).as_posix() + "`",
        )
    )
    client = _publication_client(repository)
    receipt = _publish_implementation(repository=repository, issue=issue, client=client)
    before_index = _git(repository, "ls-files", "--stage")
    lock = repository / ".git/index.lock"
    lock.write_text("foreign closeout lock\n")
    result = client.close_issue(
        IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-pending-index"),
            resolution="Completed bounded work.",
            verified_by=("fixture:checks",),
            publication_receipt_ref=receipt,
        )
    )
    payload = result.to_wire()
    writer = payload["workspace_result"]["original_writer_report"]
    assert result.outcome == "incomplete"
    assert payload["workspace_result"]["publication_state"] == "published"
    assert writer["shared_index_projection"] == "failed"
    assert writer["shared_index_projection_error"] == "shared_index_lock_busy"
    assert writer["index_reconciliation_pending"] is True
    assert lock.read_text() == "foreign closeout lock\n"
    assert _git(repository, "ls-files", "--stage") == before_index
    assert "- Status: Closed" in issue.read_text()


def test_close_refuses_unverified_publication_receipt_without_mutation(
    tmp_path: Path,
) -> None:
    repository, _target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    before = issue.read_bytes()
    result = _publication_client(repository).close_issue(
        IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-invalid-receipt"),
            resolution="Must not close.",
            verified_by=("reports/review.md",),
            publication_receipt_ref="git:" + "a" * 40,
        )
    )
    assert result.outcome == "refused"
    assert issue.read_bytes() == before


def test_close_retains_source_effect_when_publication_fails(tmp_path: Path) -> None:
    repository, _target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text().replace(
            "- `src/example.py`",
            "- `src/example.py`\n- `" + issue.relative_to(repository).as_posix() + "`",
        )
    )
    client = _publication_client(repository)
    receipt = _publish_implementation(repository=repository, issue=issue, client=client)
    head_before = _git(repository, "rev-parse", "HEAD")
    hook = repository / ".git/hooks/reference-transaction"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    result = client.close_issue(
        IssueCloseRequest(
            **_mutation_kwargs(issue, intent="close-publication-failure"),
            resolution="Retain known effects.",
            verified_by=("reports/review.md",),
            publication_receipt_ref=receipt,
        )
    )
    payload = result.to_wire()
    assert result.outcome == "incomplete"
    assert payload["workspace_result"]["publication_state"] == "not_published"
    assert (
        payload["issue_observation"]["source_observation"]["source_change_state"]
        == "applied"
    )
    assert "- Status: Closed" in issue.read_text()
    assert _git(repository, "rev-parse", "HEAD") == head_before


@pytest.mark.parametrize("projection_busy", [False, True])
def test_commit_workspace_plans_then_publishes_through_workspace_owner(
    tmp_path: Path, projection_busy: bool
) -> None:
    repository, target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    client = _publication_client(repository)
    request = IssueCommitWorkspaceRequest(
        issue_ref=ISSUE_REF,
        expected_issue_source_sha256=_digest(issue),
        target_paths=("src/example.py",),
        message="publish exact target",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:test",
        dry_run=True,
    )
    planned = client.commit_workspace(request)
    assert (
        planned.outcome == "planned" and planned.to_wire()["workspace_result"] is None
    )
    head_before = _git(repository, "rev-parse", "HEAD")
    index_before = _git(repository, "ls-files", "--stage")
    if projection_busy:
        (repository / ".git/index.lock").write_text("foreign lock\n")
    published = client.commit_workspace(replace(request, dry_run=False))
    payload = published.to_wire()
    assert published.outcome == ("incomplete" if projection_busy else "completed")
    assert payload["workspace_result"]["publication_state"] == "published"
    assert _git(repository, "rev-parse", "HEAD") != head_before
    assert _git(repository, "show", "HEAD:src/example.py") == "after"
    assert target.read_text() == "after\n"
    if projection_busy:
        assert _git(repository, "ls-files", "--stage") == index_before


def test_commit_workspace_refuses_owner_scope_and_stale_issue(tmp_path: Path) -> None:
    repository, target = _publication_repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    client = _publication_client(repository)
    request = IssueCommitWorkspaceRequest(
        issue_ref=ISSUE_REF,
        expected_issue_source_sha256=_digest(issue),
        target_paths=("src/example.py",),
        message="publish exact target",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:test",
        dry_run=False,
    )
    head = _git(repository, "rev-parse", "HEAD")
    for changed in (
        replace(request, actor_ref="codex-other"),
        replace(request, target_paths=("AGENTS.md",)),
        replace(request, expected_issue_source_sha256="sha256:" + "0" * 64),
    ):
        result = client.commit_workspace(changed)
        assert result.outcome == "refused"
        assert result.to_wire()["workspace_result"] is None
    assert _git(repository, "rev-parse", "HEAD") == head
    assert target.read_text() == "after\n"
