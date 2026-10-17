"""Real original-owner joins in disposable source fixtures, not installed proof."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
from aware_workspace_sdk.architecture_setup_review_codec import (
    review_value_from_payload,
    review_value_to_json,
)
from aware_workspace_sdk.architecture_setup_review_values import SetupEvidenceRef

client = importlib.import_module("aware_agent_cli.main")
ROOT = Path(__file__).resolve().parents[8]
ISSUE = "docs/issues/2026/10/17/fb-2026-10-17-review-proof.md"
TAG = "fb/2026-10-17/review-proof"
EXECUTION = "codex-agent-review-proof"


@pytest.fixture
def repository(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_THREAD_ID", "agent-review-proof")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root, evidence = tmp_path / "repository", tmp_path / "evidence"
    root.mkdir()
    evidence.mkdir(mode=0o700)
    (root / ISSUE).parent.mkdir(parents=True)
    (root / "docs/goals").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Disposable original-owner fixture\n")
    (root / "aware.protocol.toml").write_bytes(
        (ROOT / "aware.protocol.toml").read_bytes()
    )
    (root / ISSUE).write_text(
        "# Issue: review proof\n\n- Slug: review-proof\n- Tag: "
        + TAG
        + "\n- Status: In Progress\n- Owner: "
        + EXECUTION
        + "\n- Priority: P1\n- Captured: 2026-10-17\n- Recorder: "
        + EXECUTION
        + "\n- Source: disposable proof\n\n## Ownership Scope\n- `foreign.py`\n"
    )
    (root / "foreign.py").write_bytes(b"# unrelated customer work\n")
    (root / "foreign.py").chmod(0o751)
    return root, evidence


def invoke(repository, capsys, action, *arguments):
    root, evidence = repository
    code = client.main(
        [
            "workspace",
            "review",
            action,
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--json",
            *arguments,
        ]
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


def prepare(repository, capsys, intent="preview-first"):
    code, result = invoke(
        repository,
        capsys,
        "prepare",
        "--issue-ref",
        TAG,
        "--issue-path",
        ISSUE,
        "--name",
        "example",
        "--license-expression",
        "MIT",
        "--actor-ref",
        EXECUTION,
        "--actor-evidence-ref",
        "evidence:declared",
        "--include-issue-lifecycle",
        "--client-intent-id",
        intent,
    )
    assert code == 0, result
    return result


def reference(payload):
    # Use the original public codec, not a test implementation of its schema.
    return review_value_to_json(
        review_value_from_payload(SetupEvidenceRef, payload["reference"])
    )


def scoped(repository, capsys):
    first = prepare(repository, capsys)
    code, second = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "scope-and-second-preview",
        "--accept-reviewed-effect-scope",
    )
    assert code == 0, json.dumps(second, indent=2)
    return first, second


def test_complete_two_review_flow_and_exact_full_evidence(repository, capsys):
    root, evidence = repository
    before = (root / "foreign.py").read_bytes(), (root / "foreign.py").stat().st_mode
    first = prepare(repository, capsys)
    assert not (root / "aware.repo.toml").exists()
    assert first["result"]["value"]["decision_required"] == "scope_review"
    first_record = first["review"]["value"]
    assert "foreign.py" in first_record["existing_scope"]
    assert len(first_record["physical_scope"]) > len(first_record["final_files"])
    code, second = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "scope",
        "--accept-reviewed-effect-scope",
    )
    assert code == 0, json.dumps(second, indent=2)
    assert not (root / "aware.repo.toml").exists()
    assert second["result"]["value"]["decision_required"] == "apply_review"
    assert second["scope_completion"]["status"] == "continuation_ready"
    original = second["scope_completion"]["original_outcome"]
    assert original["source_sha256_before"] != original["source_sha256_after"]
    assert "foreign.py" in original["projection"]["content"]["ownership_scope"]
    code, result = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(second),
        "--client-intent-id",
        "apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0, result
    assert result["outcome"]["original_evidence"]["completion_verified"]
    assert result["client_cleanup"]["value"]["ledger_complete"]
    assert (root / "aware.repo.toml").is_file()
    assert (
        (root / "foreign.py").read_bytes(),
        (root / "foreign.py").stat().st_mode,
    ) == before
    outcome_ref = review_value_from_payload(
        SetupEvidenceRef, result["result"]["value"]["reference"]
    )
    with WorkspaceSetupReviewClient.filesystem(
        repository_root=root,
        evidence_root=evidence,
        execution_id=EXECUTION,
        authority_manifest_locator="aware.protocol.toml",
    ) as sdk:
        original_raw = sdk.read_evidence(
            outcome_ref, expected_target=outcome_ref.target
        ).raw_bytes
    code = client.main(
        [
            "workspace",
            "review",
            "evidence",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            review_value_to_json(outcome_ref),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert output.out.encode() == original_raw
    assert json.loads(output.err)["client_cleanup"]["value"]["ledger_complete"]


@pytest.mark.parametrize(
    "action,flag",
    [
        ("scope", "--accept-reviewed-effect-scope"),
        ("apply", "--accept-reviewed-final-files"),
    ],
)
def test_missing_explicit_choice_refuses_before_any_provider(
    repository, capsys, monkeypatch, action, flag
):
    first = prepare(repository, capsys)

    def forbidden(**kwargs):
        pytest.fail("missing choice reached owner acquisition")

    monkeypatch.setattr(WorkspaceSetupReviewClient, "filesystem", forbidden)
    with pytest.raises(SystemExit) as caught:
        invoke(
            repository,
            capsys,
            action,
            "--reference",
            reference(first),
            "--client-intent-id",
            "missing-choice",
        )
    assert caught.value.code == 2
    assert flag in capsys.readouterr().err


def test_first_review_cannot_be_applied(repository, capsys):
    first = prepare(repository, capsys)
    code, result = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(first),
        "--client-intent-id",
        "premature",
        "--accept-reviewed-final-files",
    )
    assert code != 0 and "error" in result
    assert not (repository[0] / "aware.repo.toml").exists()


@pytest.mark.parametrize("drift", ["issue", "manifest", "input"])
def test_reviewed_guards_are_not_refreshed(repository, capsys, drift):
    _, second = scoped(repository, capsys)
    root, evidence = repository
    if drift == "input":
        from aware_workspace_sdk.architecture_setup_command_values import (
            WorkspaceSetupA1CommandEvidence,
            command_value_from_json,
        )

        ref = review_value_from_payload(SetupEvidenceRef, second["reference"])
        with WorkspaceSetupReviewClient.filesystem(
            repository_root=root,
            evidence_root=evidence,
            execution_id=EXECUTION,
            authority_manifest_locator="aware.protocol.toml",
        ) as owner:
            raw = owner.read_evidence(ref, expected_target=ref.target).raw_bytes
        capture = command_value_from_json(WorkspaceSetupA1CommandEvidence, raw.decode())
        path = root / capture.workspace_observation.binding.input_bindings[0].path
    else:
        path = root / {"issue": ISSUE, "manifest": "aware.protocol.toml"}[drift]
    path.write_bytes(
        (path.read_bytes() if path.exists() else b"") + b"\n# intervening work\n"
    )
    before = path.read_bytes()
    code, result = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(second),
        "--client-intent-id",
        "stale-apply",
        "--accept-reviewed-final-files",
    )
    assert code != 0, result
    assert path.read_bytes() == before
    if path.name != "aware.repo.toml":
        assert not (root / "aware.repo.toml").exists()


def test_lost_scope_return_is_retained_without_second_preview(
    repository, capsys, monkeypatch
):
    from aware_issue_sdk.operation import IssueSdkOperationClient

    first = prepare(repository, capsys)
    original = IssueSdkOperationClient.bind_issue_scope_paths
    calls = []

    def lost(issuer, request):
        calls.append(request)
        original(issuer, request)
        raise KeyboardInterrupt("lost original return")

    monkeypatch.setattr(IssueSdkOperationClient, "bind_issue_scope_paths", lost)
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "cancelled-scope",
        "--accept-reviewed-effect-scope",
    )
    assert code == 130 and len(calls) == 1
    completed = result["error"]["scope_completion"]
    assert completed["status"] == "refused"
    assert completed["original_outcome"]["value"]["dispatch"] == "unknown"
    assert completed["reference"] is not None
    assert "review" not in result and not (repository[0] / "aware.repo.toml").exists()
    again, _ = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "different-intent",
        "--accept-reviewed-effect-scope",
    )
    assert again != 0 and len(calls) == 1


def test_scope_success_survives_second_preview_failure(repository, capsys, monkeypatch):
    first = prepare(repository, capsys)
    original = WorkspaceSetupReviewClient.preview_review

    def fail_second(owner, request, **kwargs):
        if kwargs.get("scope_continuation") is not None:
            raise OSError("second preview unavailable")
        return original(owner, request, **kwargs)

    monkeypatch.setattr(WorkspaceSetupReviewClient, "preview_review", fail_second)
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "scope",
        "--accept-reviewed-effect-scope",
    )
    assert code != 0
    assert result["scope_completion"]["original_outcome"]["outcome"] == "applied"
    assert result["stage"] == "second_preview"
    assert not (repository[0] / "aware.repo.toml").exists()


def test_incomplete_cleanup_does_not_erase_known_apply(repository, capsys, monkeypatch):
    _, second = scoped(repository, capsys)
    original = WorkspaceSetupReviewClient.release_client

    def unknown(owner):
        actual = original(owner)
        return replace(actual, ledger_complete=False, diagnostics=("injected_unknown",))

    monkeypatch.setattr(WorkspaceSetupReviewClient, "release_client", unknown)
    code, result = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(second),
        "--client-intent-id",
        "apply",
        "--accept-reviewed-final-files",
    )
    assert code == 3 and result["status"] == "incomplete"
    assert result["outcome"]["original_evidence"]["completion_verified"]
    assert not result["client_cleanup"]["value"]["ledger_complete"]
    assert (repository[0] / "aware.repo.toml").exists()


@pytest.mark.parametrize("identity", ["missing", "ambiguous"])
def test_harness_identity_refuses_before_acquisition(
    repository, capsys, monkeypatch, identity
):
    first = prepare(repository, capsys)
    if identity == "missing":
        monkeypatch.delenv("CODEX_THREAD_ID")
    else:
        monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "another-provider")
    code, result = invoke(repository, capsys, "show", "--reference", reference(first))
    assert code == 2 and result["stage"] == "preflight"


def test_concise_summary_omits_full_json_and_show_is_readonly(repository, capsys):
    first = prepare(repository, capsys)
    before = (repository[0] / ISSUE).read_bytes()
    root, evidence = repository
    code = client.main(
        [
            "workspace",
            "review",
            "show",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            reference(first),
        ]
    )
    output = capsys.readouterr()
    assert code == 0
    assert "Issue physical scope" in output.out and "Apply final files" in output.out
    assert "Complete owner evidence JSON" not in output.out
    assert len(output.out.encode()) < 16_384
    assert (root / ISSUE).read_bytes() == before


def test_foreign_execution_can_read_history_not_invoke(repository, capsys, monkeypatch):
    first = prepare(repository, capsys)
    monkeypatch.setenv("CODEX_THREAD_ID", "different-agent")
    code, historical = invoke(
        repository, capsys, "show", "--reference", reference(first)
    )
    assert code == 0 and historical["purpose"] == "history"
    code, refused = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "foreign-scope",
        "--accept-reviewed-effect-scope",
    )
    assert code != 0 and refused["stage"] == "review_read"
    assert not (repository[0] / "aware.repo.toml").exists()


@pytest.mark.parametrize("change", ["digest", "missing", "root", "surrogate"])
def test_bad_reference_refuses_without_reconstructing_or_writing(
    repository, capsys, change
):
    first = prepare(repository, capsys)
    ref = review_value_from_payload(SetupEvidenceRef, first["reference"])
    changed = {
        "digest": replace(ref, record_sha256="sha256:" + "f" * 64),
        "missing": replace(ref, locator="a1-absent-review.json"),
        "root": replace(ref, evidence_root=str(repository[0])),
    }.get(change)
    supplied = '"\ud800"' if change == "surrogate" else review_value_to_json(changed)
    before = (repository[0] / ISSUE).read_bytes()
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        supplied,
        "--client-intent-id",
        "bad-reference",
        "--accept-reviewed-effect-scope",
    )
    assert code != 0, result
    assert (repository[0] / ISSUE).read_bytes() == before
    assert not (repository[0] / "aware.repo.toml").exists()


def test_stale_first_review_refuses_before_issue_scope_dispatch(
    repository, capsys, monkeypatch
):
    from aware_issue_sdk.operation import IssueSdkOperationClient

    first = prepare(repository, capsys)
    path = repository[0] / ISSUE
    path.write_bytes(path.read_bytes() + b"\n# new owner work\n")
    before = path.read_bytes()

    def forbidden(*args, **kwargs):
        pytest.fail("stale review dispatched Issue scope")

    monkeypatch.setattr(IssueSdkOperationClient, "bind_issue_scope_paths", forbidden)
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "stale",
        "--accept-reviewed-effect-scope",
    )
    assert code != 0 and result["stage"] == "review_read"
    assert path.read_bytes() == before


def test_second_preview_intent_budget_refuses_before_scope_mutation(
    repository, capsys, monkeypatch
):
    from aware_issue_sdk.operation import IssueSdkOperationClient

    first = prepare(repository, capsys)

    def forbidden(*args, **kwargs):
        pytest.fail("invalid intent dispatched Issue")

    monkeypatch.setattr(IssueSdkOperationClient, "bind_issue_scope_paths", forbidden)
    before = (repository[0] / ISSUE).read_bytes()
    code, _ = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "x" * 1024,
        "--accept-reviewed-effect-scope",
    )
    assert code != 0 and (repository[0] / ISSUE).read_bytes() == before


def test_apply_cannot_be_replayed_with_new_intent(repository, capsys):
    _, second = scoped(repository, capsys)
    code, _ = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(second),
        "--client-intent-id",
        "original-apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0
    path = repository[0] / "aware.repo.toml"
    before = path.read_bytes(), path.stat().st_mode
    code, _ = invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        reference(second),
        "--client-intent-id",
        "new-intent-not-new-authority",
        "--accept-reviewed-final-files",
    )
    assert code != 0 and (path.read_bytes(), path.stat().st_mode) == before


def test_genuine_stale_scope_return_has_no_second_preview(
    repository, capsys, monkeypatch
):
    from aware_issue_sdk.operation import IssueSdkOperationClient

    first = prepare(repository, capsys)
    original = IssueSdkOperationClient.bind_issue_scope_paths
    calls = []

    def stale(issuer, request):
        calls.append(request)
        path = repository[0] / ISSUE
        path.write_bytes(path.read_bytes() + b"\n# concurrent task update\n")
        return original(issuer, request)

    monkeypatch.setattr(IssueSdkOperationClient, "bind_issue_scope_paths", stale)
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "scope",
        "--accept-reviewed-effect-scope",
    )
    assert code == 2 and len(calls) == 1
    assert result["scope_completion"]["original_outcome"]["outcome"] == "stale"
    assert result["scope_completion"]["status"] == "refused"
    assert "review" not in result and not (repository[0] / "aware.repo.toml").exists()


def test_original_issue_exception_keeps_typed_failure_and_cause(
    repository, capsys, monkeypatch
):
    from aware_issue_fs_adapter.provider import FilesystemIssueOperationProvider

    first = prepare(repository, capsys)
    original = FilesystemIssueOperationProvider.bind_issue_scope_paths

    def lost(provider, request):
        original(provider, request)
        raise OSError("original provider return unavailable")

    monkeypatch.setattr(
        FilesystemIssueOperationProvider, "bind_issue_scope_paths", lost
    )
    code, result = invoke(
        repository,
        capsys,
        "scope",
        "--reference",
        reference(first),
        "--client-intent-id",
        "scope",
        "--accept-reviewed-effect-scope",
    )
    assert code == 2
    failure = result["error"]["scope_completion"]["original_outcome"]
    assert failure["provider_invoked"] and failure["effect"] == "unknown"
    assert failure["operation_ref"] == "issue_sdk.bind_issue_scope_paths"
    assert result["error"]["cause_type"] == "OSError"
    assert not (repository[0] / "aware.repo.toml").exists()


def test_stdout_failure_after_apply_never_redispatches(repository, capsys, monkeypatch):
    import builtins

    _, second = scoped(repository, capsys)
    original = WorkspaceSetupReviewClient.apply_reviewed
    calls = []

    def apply(owner, inputs, **kwargs):
        outcome = original(owner, inputs, **kwargs)
        calls.append(outcome)
        return outcome

    monkeypatch.setattr(WorkspaceSetupReviewClient, "apply_reviewed", apply)
    printer = builtins.print

    def broken(*args, **kwargs):
        if (
            args
            and isinstance(args[0], str)
            and '"contract": "aware.agent.workspace-review.v1"' in args[0]
        ):
            raise BrokenPipeError("output unavailable after actual apply")
        return printer(*args, **kwargs)

    monkeypatch.setattr(builtins, "print", broken)
    root, evidence = repository
    code = client.main(
        [
            "workspace",
            "review",
            "apply",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            reference(second),
            "--client-intent-id",
            "apply",
            "--accept-reviewed-final-files",
            "--json",
        ]
    )
    assert code == 3 and len(calls) == 1
    assert calls[0].original_evidence.completion_verified
    assert calls[0].reference is not None and (root / "aware.repo.toml").is_file()


def test_incomplete_retention_falls_back_to_full_evidence(
    repository, capsys, monkeypatch
):
    _, second = scoped(repository, capsys)
    original = WorkspaceSetupReviewClient.apply_reviewed

    def unavailable(owner, inputs, **kwargs):
        outcome = original(owner, inputs, **kwargs)
        return replace(
            outcome,
            reference=None,
            retention=replace(
                outcome.retention, status="incomplete", ledger_complete=False
            ),
        )

    monkeypatch.setattr(WorkspaceSetupReviewClient, "apply_reviewed", unavailable)
    root, evidence = repository
    code = client.main(
        [
            "workspace",
            "review",
            "apply",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--reference",
            reference(second),
            "--client-intent-id",
            "apply",
            "--accept-reviewed-final-files",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert code == 3 and output["status"] == "incomplete"
    assert output["outcome"]["reference"] is None
    assert output["outcome"]["original_evidence"]["completion_verified"]
    assert not output["outcome"]["retention"]["value"]["ledger_complete"]
    assert (root / "aware.repo.toml").is_file()


@pytest.mark.parametrize("action", ["scope", "apply"])
@pytest.mark.parametrize("interruption", [False, True])
def test_capture_failure_preserves_completed_effects_and_incomplete_status(
    repository, capsys, monkeypatch, action, interruption
):
    from aware_issue_sdk.operation import IssueSdkOperationClient
    from aware_workspace_fs_adapter.architecture_setup_review import (
        FilesystemSetupReview,
    )
    from aware_workspace_runtime.architecture_setup_review import (
        WorkspaceSetupReviewRuntime,
    )

    review = (
        prepare(repository, capsys)
        if action == "scope"
        else scoped(repository, capsys)[1]
    )
    calls = []
    owner_type, method = (
        (IssueSdkOperationClient, "bind_issue_scope_paths")
        if action == "scope"
        else (WorkspaceSetupReviewRuntime, "_run_driver")
    )
    original = getattr(owner_type, method)

    def dispatch(owner, inputs, **kwargs):
        calls.append(inputs)
        return original(owner, inputs, **kwargs)

    monkeypatch.setattr(owner_type, method, dispatch)
    write = FilesystemSetupReview.write_capture
    kind = "issue_result_v1" if action == "scope" else "command_v1"

    def fail_capture(owner, raw, **kwargs):
        if kwargs.get("kind") == kind:
            if interruption:
                raise KeyboardInterrupt("capture interrupted after original effects")
            raise OSError("capture failed after original effects")
        return write(owner, raw, **kwargs)

    monkeypatch.setattr(FilesystemSetupReview, "write_capture", fail_capture)
    flag = (
        "--accept-reviewed-effect-scope"
        if action == "scope"
        else "--accept-reviewed-final-files"
    )
    code, result = invoke(
        repository,
        capsys,
        action,
        "--reference",
        reference(review),
        "--client-intent-id",
        "capture-failure",
        flag,
    )
    assert code == (130 if interruption else 3)
    assert result["status"] == "incomplete" and len(calls) == 1
    assert result["client_cleanup"]["value"]["ledger_complete"]
    assert not result["authorizes_retry"]
    if action == "scope":
        completion = (
            result.get("scope_completion") or result["error"]["scope_completion"]
        )
        assert completion["status"] == "incomplete"
        assert completion["original_outcome"]["outcome"] == "applied"
        assert not (repository[0] / "aware.repo.toml").exists()
    else:
        assert result["error"]["outcome"]["original_evidence"]["completion_verified"]
        assert (repository[0] / "aware.repo.toml").is_file()
    before = (repository[0] / ISSUE).read_bytes()
    again, _ = invoke(
        repository,
        capsys,
        action,
        "--reference",
        reference(review),
        "--client-intent-id",
        "capture-failure",
        flag,
    )
    assert again != 0 and len(calls) == 1
    assert (repository[0] / ISSUE).read_bytes() == before


def test_human_apply_keeps_original_release_separate_from_later_cleanup(
    repository, capsys, monkeypatch
):
    from aware_agent_cli import workspace_review

    _, second = scoped(repository, capsys)
    render = workspace_review._summary
    seen = []

    def summary(payload):
        seen.append(payload)
        return render(payload)

    monkeypatch.setattr(workspace_review, "_summary", summary)
    code = client.main(
        [
            "workspace",
            "review",
            "apply",
            "--repository-root",
            str(repository[0]),
            "--evidence-root",
            str(repository[1]),
            "--reference",
            reference(second),
            "--client-intent-id",
            "human-apply",
            "--accept-reviewed-final-files",
        ]
    )
    output = capsys.readouterr().out
    assert code == 0 and seen[0]["status"] == "completed"
    original = seen[0]["outcome"]["original_evidence"]["workspace_result"]["value"]
    assert original["release"] == "unknown"
    assert 'Original Workspace release: "unknown"' in output
    assert "Original physical effect states:" in output
    assert "Original Workspace durability:" in output
    assert "Client cleanup complete: true" in output
    assert (
        "Later client cleanup does not change these original qualifications" in output
    )
    assert seen[0]["outcome"]["original_evidence"]["completion_verified"]


@pytest.mark.parametrize("control", ["\u202e", "\u2066"])
def test_human_review_escapes_original_paths_without_changing_sdk_values(
    repository, capsys, control
):
    path = "foreign" + control + "-not-approved.py"
    issue = repository[0] / ISSUE
    issue.write_text(issue.read_text().replace("foreign.py", path))
    first = prepare(repository, capsys)
    assert path in first["review"]["value"]["existing_scope"]
    before = issue.read_bytes()
    code = client.main(
        [
            "workspace",
            "review",
            "show",
            "--repository-root",
            str(repository[0]),
            "--evidence-root",
            str(repository[1]),
            "--reference",
            reference(first),
        ]
    )
    output = capsys.readouterr().out
    assert code == 0 and control not in output
    assert json.dumps(path, ensure_ascii=True) in output
    assert issue.read_bytes() == before


@pytest.mark.parametrize(
    "text", ["\x1b[31m", "\r\nforged", "\b", "\u202e", "\u2066", '"quoted"', "café"]
)
def test_terminal_display_is_quoted_ascii_and_lossless(text):
    from aware_agent_cli.workspace_review import _terminal_text

    display = _terminal_text(text)
    assert display.isascii()
    assert all(ord(character) >= 32 for character in display)
    assert json.loads(display) == text


def test_fresh_process_help_does_not_import_sdk_or_providers():
    program = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_issue', 'aware_protocol', 'aware_specification',
                                'aware_file_system', 'aware_ontology')):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Refuse())
from aware_agent_cli.main import main
main(['workspace', 'review', '--help'])
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "prepare,show,scope,apply,evidence" in result.stdout


def test_real_source_subprocess_two_review_flow(repository):
    root, evidence = repository
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from aware_agent_cli.main import main; raise SystemExit(main())",
            "workspace",
            "review",
            "prepare",
            "--repository-root",
            str(root),
            "--evidence-root",
            str(evidence),
            "--issue-ref",
            TAG,
            "--issue-path",
            ISSUE,
            "--name",
            "example",
            "--license-expression",
            "MIT",
            "--actor-ref",
            EXECUTION,
            "--actor-evidence-ref",
            "evidence:declared",
            "--client-intent-id",
            "subprocess",
            "--json",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"]["value"]["decision_required"] == "scope_review"
    for action, intent, flag in (
        ("scope", "subprocess-scope", "--accept-reviewed-effect-scope"),
        ("apply", "subprocess-apply", "--accept-reviewed-final-files"),
    ):
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                "from aware_agent_cli.main import main; raise SystemExit(main())",
                "workspace",
                "review",
                action,
                "--repository-root",
                str(root),
                "--evidence-root",
                str(evidence),
                "--reference",
                reference(payload),
                "--client-intent-id",
                intent,
                flag,
                "--json",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        payload = json.loads(result.stdout)
        assert payload["client_cleanup"]["value"]["ledger_complete"]
    assert payload["outcome"]["original_evidence"]["completion_verified"]
    assert (root / "aware.repo.toml").is_file()
