"""Genuine one-lifetime consumer loop; source proof, not installed acceptance."""

import importlib
import json
import subprocess
from types import SimpleNamespace

import pytest
from aware_issue_sdk import IssueSdkOperationClient
from aware_issue_sdk.repository_publication import (
    IssueRepositoryOperationResult,
    IssueRepositoryPublicationRefusal,
)
from test_repository_runtime_orchestration import _close_request, composed_loop
from test_sdk_return_failure import ReturnedFailure

cli = importlib.import_module("aware_issue_cli.main")
composed = composed_loop


def _malformed_presentation(payload, kind):
    if kind == "header_only":
        return {
            key: payload[key]
            for key in ("contract", "operation_ref", "issue_ref", "outcome")
        }
    if kind == "unknown_completed":
        payload["workspace_result"]["publication_state"] = "unknown"
        payload["ledger_complete"] = False
    elif kind == "missing_workspace_field":
        del payload["workspace_result"]["lock_release"]
    elif kind == "malformed_writer":
        del payload["workspace_result"]["original_writer_report"]["reference_update"]
    elif kind == "wrong_nested_type":
        payload["workspace_result"]["ledger_complete"] = 1
    elif kind == "missing_issue_field":
        del payload["issue_observation"]["completion_state"]
    elif kind == "null_cleanup":
        payload["cleanup_observations"] = [None]
    elif kind == "malformed_workspace_observation":
        payload["workspace_observation"] = {"ledger_complete": True}
    elif kind == "retry_permission":
        payload["authorizes_retry"] = True
    elif kind == "missing_commit":
        payload["workspace_result"]["commit_hash"] = None
    elif kind == "missing_result":
        payload["workspace_result"] = None
    elif kind == "missing_observation":
        payload["issue_observation"] = None
    elif kind == "malformed_source":
        payload["issue_observation"]["source_observation"]["source_change_state"] = (
            "invented"
        )
    else:
        raise AssertionError(kind)
    return payload


@pytest.mark.parametrize("command", ["commit-workspace", "publish-close"])
@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize(
    "kind",
    [
        "header_only",
        "unknown_completed",
        "missing_workspace_field",
        "malformed_writer",
        "wrong_nested_type",
        "missing_issue_field",
        "null_cleanup",
        "malformed_workspace_observation",
        "retry_permission",
        "missing_commit",
        "missing_result",
        "missing_observation",
    ],
)
def test_malformed_nested_return_refuses_after_one_real_publication(
    composed, monkeypatch, capsys, command, format_name, kind
):
    root, source, _, runtime, repository_client, _ = composed
    original = runtime.commit_workspace_result
    returned = []

    def malformed(request):
        payload = _malformed_presentation(original(request).to_wire(), kind)
        returned.append(payload)
        return IssueRepositoryOperationResult(json.dumps(payload))

    def forbidden(*args, **kwargs):
        pytest.fail("Rejected evidence cannot sequence closeout or recapture authority")

    monkeypatch.setattr(runtime, "commit_workspace_result", malformed)
    monkeypatch.setattr(runtime, "close_issue_result", forbidden)
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    assert cli.main(_argv(composed, command, format_name)) == 2
    refusal = json.loads(capsys.readouterr().out)
    assert refusal["code"] == "issue_repository_result_validation_failed"
    assert refusal["consumer_result"] == returned[0]
    assert refusal["consumer_result_validation"] == "unvalidated"
    assert refusal["result_validation_complete"] is False
    assert refusal["authorizes_retry"] is False
    assert refusal["authority_restored"] is False
    assert len(returned) == 1
    assert b"- Status: In Progress" in source.read_bytes()
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"1"
    )
    # The real owner, not the rejected presentation, retains spent authority.
    assert (
        runtime._repository_operations[0].issue_observation.consumption_state
        == "consumed"
    )


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize(
    "kind", ["header_only", "unknown_completed", "malformed_source"]
)
def test_malformed_close_return_keeps_first_receipt_and_unvalidated_second(
    composed, monkeypatch, capsys, format_name, kind
):
    root, source, _, runtime, repository_client, _ = composed
    original = runtime.close_issue_result
    returned = []

    def malformed(request):
        payload = _malformed_presentation(original(request).to_wire(), kind)
        returned.append(payload)
        return IssueRepositoryOperationResult(json.dumps(payload))

    monkeypatch.setattr(runtime, "close_issue_result", malformed)
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    assert cli.main(_argv(composed, format_name=format_name)) == 2
    implementation, refusal = json.loads(capsys.readouterr().out)["receipts"]
    assert implementation["workspace_result"]["publication_state"] == "published"
    assert len(implementation["workspace_result"]["original_writer_report"]) == 32
    assert refusal["consumer_result"] == returned[0]
    assert refusal["consumer_result_validation"] == "unvalidated"
    assert refusal["code"] == "issue_repository_result_validation_failed"
    assert len(returned) == 1
    assert b"- Status: Closed" in source.read_bytes()
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"2"
    )


@pytest.mark.parametrize("kind", ["unknown_completed", "header_only"])
def test_disabling_return_validation_reproduces_original_review_probes(
    composed, monkeypatch, capsys, kind
):
    from aware_issue_operational_runtime import repository_publication as owner

    _, _, _, runtime, repository_client, _ = composed
    original = runtime.commit_workspace_result

    def malformed(request):
        return IssueRepositoryOperationResult(
            json.dumps(_malformed_presentation(original(request).to_wire(), kind))
        )

    # Counterfactual only: demonstrate that the SDK validation gate closes the
    # exact reported gap, without editing or replacing production source bytes.
    monkeypatch.setattr(
        owner, "validate_repository_operation_result", lambda *args: None
    )
    monkeypatch.setattr(runtime, "commit_workspace_result", malformed)
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    if kind == "header_only":
        with pytest.raises(KeyError, match="workspace_result"):
            cli.main(_argv(composed))
    else:
        assert cli.main(_argv(composed, command="commit-workspace")) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["outcome"] == "completed" and payload["ledger_complete"] is False
        assert payload["workspace_result"]["publication_state"] == "unknown"


def test_return_validation_only_decodes_without_owner_calls_or_input_mutation(
    composed, monkeypatch
):
    from aware_issue_operational_runtime import repository_publication as owner

    _, _, workspace, runtime, repository_client, request = composed
    snapshot = repository_client.commit_workspace_result(request)
    before = snapshot.payload_json

    def forbidden(*args, **kwargs):
        pytest.fail("Presentation validation must not recapture or operate an owner")

    monkeypatch.setattr(owner, "_execution", forbidden)
    monkeypatch.setattr(runtime, "_current", forbidden)
    monkeypatch.setattr(runtime, "_operation_workspace_observation", forbidden)
    monkeypatch.setattr(workspace._provider, "observe_repository_attempt", forbidden)
    monkeypatch.setattr(workspace._provider, "publish_repository_commit", forbidden)
    payload = snapshot.to_wire()
    owner.validate_repository_operation_result(request, payload)
    assert payload == snapshot.to_wire() and snapshot.payload_json == before
    payload["workspace_result"]["publication_state"] = "unknown"
    with pytest.raises(ValueError, match="outcome_inconsistent"):
        owner.validate_repository_operation_result(request, payload)
    assert snapshot.payload_json == before


@pytest.mark.parametrize("kind", ["header_only", "unknown_completed"])
def test_sdk_marks_rejected_snapshot_unvalidated_without_replaying_publication(
    composed, monkeypatch, kind
):
    root, _, _, runtime, repository_client, request = composed
    original = runtime.commit_workspace_result
    returned = []

    def malformed(request):
        snapshot = IssueRepositoryOperationResult(
            json.dumps(_malformed_presentation(original(request).to_wire(), kind))
        )
        returned.append(snapshot)
        return snapshot

    monkeypatch.setattr(runtime, "commit_workspace_result", malformed)
    with pytest.raises(IssueRepositoryPublicationRefusal) as failed:
        repository_client.commit_workspace_result(request)
    assert failed.value.consumer_result is returned[0]
    assert failed.value.consumer_result_validation == "unvalidated"
    assert failed.value.result_validation_complete is False
    assert len(returned) == 1
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"1"
    )


def _argv(composed, command="publish-close", format_name="json"):
    root, _, _, _, _, request = composed
    args = [
        command,
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
    if command == "publish-close":
        args.extend(
            [
                "--resolution",
                "Completed",
                "--verified-by",
                "genuine tests",
                "--client-intent-id",
                "close:consumer",
            ]
        )
    return args


@pytest.mark.parametrize("format_name", ["json", "summary"])
@pytest.mark.parametrize("mode", ["foreign", "raise", "untyped"])
def test_late_close_return_refusal_keeps_both_full_operation_records(
    composed, monkeypatch, capsys, format_name, mode
):
    root, source, _, runtime, repository_client, _ = composed
    wrapped = ReturnedFailure(runtime, "close_issue_result", mode)
    monkeypatch.setattr(runtime, "close_issue_result", wrapped.close_issue_result)
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    assert cli.main(_argv(composed, format_name=format_name)) == 2
    payload = json.loads(capsys.readouterr().out)
    implementation, refused = payload["receipts"]
    assert implementation["workspace_result"]["publication_state"] == "published"
    assert refused["outcome"] == "refused" and refused["authorizes_retry"] is False
    assert (
        refused["consumer_result"]["workspace_result"]["publication_state"]
        == "published"
    )
    assert (
        refused["consumer_result"]["issue_observation"]["source_observation"][
            "source_change_state"
        ]
        == "applied"
    )
    assert wrapped.calls == 1
    assert b"- Status: Closed" in source.read_bytes()
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"2"
    )


def test_saved_compound_receipt_observation_never_restores_original_history(
    composed, monkeypatch, capsys, tmp_path
):
    assert cli.main(_argv(composed)) == 0
    body = capsys.readouterr().out.encode()
    saved = tmp_path / "full.json"
    saved.write_bytes(body)

    def forbidden(**kwargs):
        pytest.fail("Saved evidence must not construct or restore an owner")

    monkeypatch.setattr(cli, "create_repository_client", forbidden)
    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", forbidden)
    assert (
        cli.main(["present-receipt", "--receipt-path", str(saved), "--format", "json"])
        == 0
    )
    observed = json.loads(capsys.readouterr().out)
    assert observed["result"] == json.loads(body)
    assert observed["presentation"]["authority_restored"] is False
    assert observed["presentation"]["operation_invoked"] is False
    assert saved.read_bytes() == body


def test_close_does_not_refresh_original_guard_after_foreign_issue_edit(
    composed, monkeypatch, capsys
):
    _, source, _, runtime, repository_client, _ = composed
    original = runtime.commit_workspace_result

    def changed(request):
        result = original(request)
        source.write_bytes(source.read_bytes() + b"\nforeign Issue update\n")
        return result

    monkeypatch.setattr(runtime, "commit_workspace_result", changed)
    monkeypatch.setattr(cli, "create_repository_client", lambda **_: repository_client)
    assert cli.main(_argv(composed)) == 2
    payload = json.loads(capsys.readouterr().out)
    assert (
        payload["receipts"][0]["workspace_result"]["publication_state"] == "published"
    )
    assert payload["receipts"][1]["outcome"] == "refused"
    assert b"foreign Issue update" in source.read_bytes()
    assert b"- Status: In Progress" in source.read_bytes()


def test_retired_fs_publication_ports_are_no_effect_refusals(composed):
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider

    root, source, _, _, _, request = composed
    provider = FilesystemIssueOperationProvider(repository_root=root)
    before = source.read_bytes()
    refusal = provider.commit_workspace(request)
    assert refusal.diagnostics == ("issue_repository_runtime_required",)
    closed = provider.close_issue(
        _close_request(composed, SimpleNamespace(commit_hash="a" * 40))
    )
    assert closed.diagnostics == ("issue_repository_runtime_required",)
    assert source.read_bytes() == before


@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_cli_real_publish_close_two_receipts_full_owner_evidence(
    composed, capsys, format_name
):
    root, source, _, _, _, _ = composed
    assert cli.main(_argv(composed, format_name=format_name)) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["atomic"] is False
    assert len(payload["receipts"]) == 2
    implementation, closeout = payload["receipts"]
    for result in (implementation, closeout):
        assert result["outcome"] == "completed"
        assert result["workspace_result"]["publication_state"] == "published"
        assert len(result["workspace_result"]["original_writer_report"]) == 32
        assert result["issue_observation"]["completion_state"] == "completed"
        assert result["authorizes_retry"] is False
    assert (
        closeout["issue_observation"]["source_observation"]["source_change_state"]
        == "applied"
    )
    assert b"- Status: Closed" in source.read_bytes()
    assert (
        subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "show",
                "HEAD:" + source.relative_to(root).as_posix(),
            ]
        )
        == source.read_bytes()
    )
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"2"
    )


def test_lossless_sdk_same_owner_loop_and_detached_snapshot(composed):
    _, _, _, _, repository_client, request = composed
    client = IssueSdkOperationClient(provider=None, repository_client=repository_client)
    published = client.commit_workspace(request)
    assert type(published) is IssueRepositoryOperationResult
    payload = published.to_wire()
    payload["workspace_result"]["publication_state"] = "unknown"
    assert published.to_wire()["workspace_result"]["publication_state"] == "published"
    closed = client.close_issue(
        _close_request(
            composed,
            type(
                "Receipt",
                (),
                {"commit_hash": published.to_wire()["workspace_result"]["commit_hash"]},
            )(),
        )
    )
    assert closed.outcome == "completed"
    assert (
        closed.to_wire()["issue_observation"]["source_observation"][
            "source_change_state"
        ]
        == "applied"
    )


def test_cli_dry_run_does_not_publish_or_close(composed, capsys):
    root, source, _, _, _, _ = composed
    before = source.read_bytes()
    assert cli.main(_argv(composed) + ["--dry-run"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "planned"
    assert len(payload["receipts"]) == 1
    assert payload["receipts"][0]["workspace_result"] is None
    assert source.read_bytes() == before
    assert (
        subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )


def test_cli_unknown_cas_does_not_close_or_restore_authority(
    composed, monkeypatch, capsys
):
    from aware_workspace_fs_adapter import git_writer

    root, source, _, _, _, _ = composed
    real = git_writer._run_git
    calls = []

    def interrupted(**kwargs):
        value = real(**kwargs)
        if kwargs["args"][:2] == ("git", "update-ref"):
            calls.append("cas")
            raise KeyboardInterrupt("CAS return unavailable")
        return value

    monkeypatch.setattr(git_writer, "_run_git", interrupted)
    assert cli.main(_argv(composed)) == 2
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["receipts"]) == 1 and calls == ["cas"]
    result = payload["receipts"][0]
    assert result["workspace_result"]["publication_state"] == "unknown"
    assert result["issue_observation"]["consumption_state"] == "consumed"
    assert not result["ledger_complete"]
    assert b"- Status: In Progress" in source.read_bytes()
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"1"
    )


def test_standalone_close_fresh_owner_refuses_without_effect(composed, capsys):
    root, source, _, _, _, _ = composed
    assert cli.main(_argv(composed, command="commit-workspace")) == 0
    committed = json.loads(capsys.readouterr().out)
    before = source.read_bytes()
    request = _close_request(
        composed,
        type(
            "Receipt", (), {"commit_hash": committed["workspace_result"]["commit_hash"]}
        )(),
    )
    assert (
        cli.main(
            [
                "close",
                "--repository-root",
                str(root),
                "--issue-ref",
                request.issue_ref,
                "--expected-source-sha256",
                request.expected_source_sha256,
                "--client-intent-id",
                request.client_intent_id,
                "--actor-ref",
                request.actor_ref,
                "--actor-evidence-ref",
                request.actor_evidence_ref,
                "--resolution",
                request.resolution,
                "--verified-by",
                "genuine",
                "--publication-receipt-ref",
                request.publication_receipt_ref,
            ]
        )
        == 2
    )
    refused = json.loads(capsys.readouterr().out)
    assert refused["outcome"] == "refused"
    assert source.read_bytes() == before
    assert (
        subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", "HEAD"]
        ).strip()
        == b"1"
    )
