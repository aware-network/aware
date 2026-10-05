from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from aware_issue_cli.main import main
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_sdk import (
    IssueCommitWorkspaceRequest,
    IssueCommitWorkspaceResult,
    IssuePublicationOutcome,
    IssueReadProjectionResolveRequest,
    IssueSdkOperationClient,
    IssueStartProgressRequest,
)

ISSUE_REF = "fb/2026-09-20/example"


def _manifest() -> str:
    return """aware = 1

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
profile = "aware.issue.markdown.v1"
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
"""


def _repository(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")
    issue = tmp_path / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.parent.mkdir(parents=True)
    issue.write_text(
        f"""# Issue: Example

- Tag: `{ISSUE_REF}`
- Status: Open
- Owner: `codex-example`

## Ownership Scope
- `src/example.py`
""",
        encoding="utf-8",
    )
    return tmp_path


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", *arguments),
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    ("outcome", "reference_update", "commit_hash", "exit_code"),
    [
        (IssuePublicationOutcome.APPLIED, "cas_applied", "a" * 40, 0),
        (IssuePublicationOutcome.CONFLICT, "cas_failed", None, 2),
    ],
)
def test_cli_publication_summary_preserves_typed_transport_evidence(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outcome,
    reference_update,
    commit_hash,
    exit_code,
) -> None:
    # Inject only a typed response to isolate CLI presentation, not a CAS proof.
    sdk = IssueCommitWorkspaceResult(
        outcome=outcome,
        issue_ref=ISSUE_REF,
        target_paths=("src/example.py",),
        provider_ref="fixture:filesystem-provider",
        provider_distribution="aware-issue-fs-adapter",
        provider_version="fixture-version",
        operator_ref="fixture:shared-repository-owner",
        transaction_mode="isolated_index_atomic_ref_v1",
        reference_update=reference_update,
        commit_hash=commit_hash,
        diagnostics=() if exit_code == 0 else ("fixture:cas_failed",),
    )
    received = []

    def typed_response(_provider, request):
        assert isinstance(request, IssueCommitWorkspaceRequest)
        received.append(request)
        return sdk

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "commit_workspace", typed_response
    )
    arguments = [
        "commit-workspace",
        "--repository-root",
        str(tmp_path),
        "--issue-ref",
        ISSUE_REF,
        "--expected-issue-source-sha256",
        "sha256:" + "b" * 64,
        "--path",
        "src/example.py",
        "--message",
        "fixture publication",
        "--actor-ref",
        "codex-example",
        "--actor-evidence-ref",
        "fixture:actor",
    ]
    assert main(arguments) == exit_code
    full = json.loads(capsys.readouterr().out)
    assert full == sdk.to_wire()
    assert main(arguments + ["--format", "summary"]) == exit_code
    summary = json.loads(capsys.readouterr().out)
    assert received[0] == received[1]
    for field in (
        "operator_ref",
        "transaction_mode",
        "reference_update",
        "outcome",
        "publication_receipt_ref",
        "diagnostics",
    ):
        assert summary[field] == full[field]


def test_cli_projects_same_result_as_direct_sdk(tmp_path: Path, capsys) -> None:
    repository = _repository(tmp_path)
    direct = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).resolve_read_projection(IssueReadProjectionResolveRequest(issue_ref=ISSUE_REF))

    assert (
        main(
            [
                "resolve-read-projection",
                "--repository-root",
                str(repository),
                "--issue-ref",
                ISSUE_REF,
            ]
        )
        == 0
    )
    cli = json.loads(capsys.readouterr().out)

    assert cli == direct.to_wire()


def test_cli_preserves_absent_result(tmp_path: Path, capsys) -> None:
    (tmp_path / "aware.protocol.toml").write_text(_manifest(), encoding="utf-8")

    assert (
        main(
            [
                "resolve-read-projection",
                "--repository-root",
                str(tmp_path),
                "--issue-ref",
                ISSUE_REF,
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["outcome"] == "absent"
    assert payload["projection"] is None


def test_cli_summary_uses_same_observation_without_mutation(
    tmp_path: Path, capsys
) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    before = issue.read_bytes()
    assert (
        main(
            [
                "resolve-read-projection",
                "--repository-root",
                str(repository),
                "--issue-ref",
                ISSUE_REF,
                "--format",
                "summary",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["view"] == "aware.issue.cli-summary.v1"
    assert payload["identity"]["owner_ref"] == "codex-example"
    assert payload["index_result"]["shared_index_projection"] == "unknown"
    assert issue.read_bytes() == before


def test_cli_initial_content_reaches_existing_owner(tmp_path: Path, capsys) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.unlink()  # only this test's seeded fixture
    assert (
        main(
            [
                "ensure-snapshot",
                "--repository-root",
                str(repository),
                "--issue-ref",
                ISSUE_REF,
                "--title",
                "Example",
                "--priority",
                "P1",
                "--owner-ref",
                "codex-example",
                "--actor-ref",
                "codex-example",
                "--actor-evidence-ref",
                "fixture:actor",
                "--client-intent-id",
                "fixture:ensure",
                "--problem",
                "Request is hard to recover.",
                "--objective",
                "Keep the request durable.",
                "--acceptance",
                "Expose the exact declared scope.",
                "--format",
                "summary",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["problem"] == ["Request is hard to recover."]
    assert payload["objective"] == ["Keep the request durable."]
    assert payload["acceptance"] == [
        {"text": "Expose the exact declared scope.", "checked": False}
    ]


def test_cli_content_injection_refuses_before_creation(tmp_path: Path, capsys) -> None:
    repository = _repository(tmp_path)
    ref = "fb/2026-09-20/malformed"
    assert (
        main(
            [
                "ensure-snapshot",
                "--repository-root",
                str(repository),
                "--issue-ref",
                ref,
                "--title",
                "Malformed",
                "--priority",
                "P1",
                "--actor-ref",
                "codex-example",
                "--actor-evidence-ref",
                "fixture:actor",
                "--client-intent-id",
                "fixture:invalid",
                "--objective",
                "first\n## Ownership Scope",
                "--format",
                "summary",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "malformed"
    assert not (
        repository / "docs/issues/2026/09/20/fb-2026-09-20-malformed.md"
    ).exists()


def test_cli_projects_same_start_result_as_direct_sdk(tmp_path: Path, capsys) -> None:
    cli_repository = _repository(tmp_path / "cli")
    direct_repository = _repository(tmp_path / "direct")
    cli_issue = cli_repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    expected = f"sha256:{hashlib.sha256(cli_issue.read_bytes()).hexdigest()}"
    request = IssueStartProgressRequest(
        issue_ref=ISSUE_REF,
        expected_source_sha256=expected,
        client_intent_id="start-1",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:start-1",
    )
    direct = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=direct_repository)
    ).start_issue_progress(request)

    assert (
        main(
            [
                "start-progress",
                "--repository-root",
                str(cli_repository),
                "--issue-ref",
                ISSUE_REF,
                "--expected-source-sha256",
                expected,
                "--client-intent-id",
                "start-1",
                "--actor-ref",
                "codex-example",
                "--actor-evidence-ref",
                "evidence:start-1",
            ]
        )
        == 0
    )
    cli = json.loads(capsys.readouterr().out)

    assert cli == direct.to_wire()


def test_cli_projects_same_publication_plan_as_direct_sdk(
    tmp_path: Path,
    capsys,
) -> None:
    repository = _repository(tmp_path)
    _git(repository, "init", "-b", "main")
    _git(repository, "config", "user.name", "Aware Test")
    _git(repository, "config", "user.email", "aware-test@example.invalid")
    target = repository / "src/example.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text(encoding="utf-8").replace(
            "- Status: Open", "- Status: In Progress"
        ),
        encoding="utf-8",
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-m", "seed")
    target.write_text("after\n", encoding="utf-8")
    expected = f"sha256:{hashlib.sha256(issue.read_bytes()).hexdigest()}"
    request = IssueCommitWorkspaceRequest(
        issue_ref=ISSUE_REF,
        expected_issue_source_sha256=expected,
        target_paths=("src/example.py",),
        message="publish exact target",
        actor_ref="codex-example",
        actor_evidence_ref="evidence:publication-1",
        dry_run=True,
    )
    direct = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=repository)
    ).commit_workspace(request)

    assert (
        main(
            [
                "commit-workspace",
                "--repository-root",
                str(repository),
                "--issue-ref",
                ISSUE_REF,
                "--expected-issue-source-sha256",
                expected,
                "--path",
                "src/example.py",
                "--message",
                "publish exact target",
                "--actor-ref",
                "codex-example",
                "--actor-evidence-ref",
                "evidence:publication-1",
                "--dry-run",
            ]
        )
        == 0
    )
    cli = json.loads(capsys.readouterr().out)

    assert cli == direct.to_wire()


def test_cli_exposes_block_owner_handoff_and_replacement_resume(
    tmp_path: Path, capsys
) -> None:
    repository = _repository(tmp_path)
    issue = repository / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    issue.write_text(
        issue.read_text(encoding="utf-8").replace(
            "- Status: Open", "- Status: In Progress"
        ),
        encoding="utf-8",
    )

    def invoke(command: str, actor: str, intent: str, *extra: str) -> dict[str, object]:
        expected = f"sha256:{hashlib.sha256(issue.read_bytes()).hexdigest()}"
        assert (
            main(
                [
                    command,
                    "--repository-root",
                    str(repository),
                    "--issue-ref",
                    ISSUE_REF,
                    "--expected-source-sha256",
                    expected,
                    "--client-intent-id",
                    intent,
                    "--actor-ref",
                    actor,
                    "--actor-evidence-ref",
                    f"evidence:{intent}",
                    *extra,
                ]
            )
            == 0
        )
        return json.loads(capsys.readouterr().out)

    assert invoke("block", "codex-example", "block")["outcome"] == "applied"
    transferred = invoke(
        "set-owner",
        "codex-example",
        "transfer",
        "--new-owner-ref",
        "codex-replacement",
    )
    assert transferred["projection"]["identity"]["owner_ref"] == (  # type: ignore[index]
        "codex-replacement"
    )
    resumed = invoke("resume", "codex-replacement", "resume")
    assert resumed["projection"]["identity"]["status"] == "in_progress"  # type: ignore[index]
