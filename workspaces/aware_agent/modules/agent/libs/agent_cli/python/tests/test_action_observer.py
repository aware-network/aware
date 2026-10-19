"""Thin Agent observation against genuine retained original-owner records."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_agent_cli import workspace_review as module
from aware_agent_cli.main import main
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
from aware_workspace_sdk.architecture_setup_review_codec import (
    SetupReviewValueError,
    review_value_from_payload,
    review_value_to_json,
    review_value_to_payload,
)
from aware_workspace_sdk.architecture_setup_review_values import SetupEvidenceRef

SPEC = importlib.util.spec_from_file_location(
    "original_action_agent_fixture",
    Path(__file__).with_name("test_workspace_review.py"),
)
assert SPEC and SPEC.loader
original = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(original)
repository = original.repository


def inventory(root):
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode)
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def ready(repository, capsys):
    _, second = original.scoped(repository, capsys)
    code, applied = original.invoke(
        repository,
        capsys,
        "apply",
        "--reference",
        original.reference(second),
        "--client-intent-id",
        "observer-original-apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0, applied
    intent = review_value_to_json(
        review_value_from_payload(
            SetupEvidenceRef, applied["outcome"]["retention"]["value"]["intent_ref"]
        )
    )
    return repository, original.reference(second), intent, applied


def arguments(ready, *, human=False, stdin=False):
    (root, evidence), reference, intent, _ = ready
    return [
        "workspace",
        "review",
        "observe-admission",
        "--repository-root",
        str(root),
        "--evidence-root",
        str(evidence),
        *(["--reference-from-stdin"] if stdin else ["--reference", reference]),
        "--intent-reference",
        intent,
        *([] if human else ["--json"]),
    ]


def observed(ready, capsys):
    code = main(arguments(ready))
    capture = capsys.readouterr()
    assert capture.err == ""
    return code, json.loads(capture.out)


@pytest.mark.parametrize("changed_issue", [False, True])
def test_genuine_observation_is_historical_read_only(
    ready, capsys, monkeypatch, changed_issue
):
    (root, evidence), _, _, applied = ready
    if changed_issue:
        path = root / original.ISSUE
        path.write_bytes(path.read_bytes() + b"\n# later unrelated revision\n")
    before = inventory(root), inventory(evidence)
    original_observe = WorkspaceSetupReviewClient.observe_action_admission
    calls = []
    returned = []

    def observe(client, request):
        def forbidden(*args, **kwargs):
            pytest.fail(
                "Observation attempted a write, driver call or currentness refresh"
            )

        for name in ("_run_driver", "_intent", "_reference_for", "_current_issue"):
            monkeypatch.setattr(client._runtime, name, forbidden)
        monkeypatch.setattr(client._runtime.store, "write_metadata", forbidden)
        monkeypatch.setattr(client._runtime.store, "write_capture", forbidden)
        calls.append(request)
        value = original_observe(client, request)
        returned.append(value)
        return value

    monkeypatch.setattr(WorkspaceSetupReviewClient, "observe_action_admission", observe)
    monkeypatch.setenv("CODEX_THREAD_ID", "different-observer-execution")
    code, payload = observed(ready, capsys)
    assert code == 0, payload
    view = payload["action_observation"]
    assert view["observation"] == "validated_retained_intent"
    assert view["historical_driver_outcome"] == "not_established"
    assert view["product_dispatch_this_observation"] == "not_invoked"
    assert view["authorizes_retry"] is False and view["portable_admission"] is False
    assert "reference" not in payload and "commands" not in payload
    assert view["reads"] and view["private_observation"]
    assert payload["client_cleanup"]["value"]["ledger_complete"]
    assert len(calls) == 1
    for name in (
        "target",
        "review_ref",
        "intent_ref",
        "inputs_ref",
        "review",
        "intent",
        "inputs",
    ):
        assert view[name] == review_value_to_payload(getattr(returned[0], name))
    from aware_file_system.private_directory import private_directory_value_to_payload

    assert view["private_observation"] == private_directory_value_to_payload(
        returned[0].private_observation
    )
    assert view["reads"] == [
        private_directory_value_to_payload(row) for row in returned[0].reads
    ]
    with pytest.raises(SetupReviewValueError, match="serializable_original"):
        review_value_to_payload(returned[0])
    assert before == (inventory(root), inventory(evidence))
    assert (
        applied["outcome"]["original_evidence"]["workspace_result"]["value"]["release"]
        == "unknown"
    )


def test_human_summary_separates_history_and_observer_cleanup(ready, capsys):
    assert main(arguments(ready, human=True)) == 0
    output = capsys.readouterr()
    assert output.err == ""
    for text in (
        "validated_retained_intent",
        "not_established",
        "not_invoked",
        "Original Workspace release: unknown",
        "Observer client cleanup complete: true",
        "Authorizes retry: false",
        "not a portable SDK grant",
        "Do not repeat apply",
    ):
        assert text in output.out


@pytest.mark.parametrize("bad_intent", ["{}", "not-json", "review"])
def test_invalid_request_refuses_before_acquisition(
    ready, capsys, monkeypatch, bad_intent
):
    argv = arguments(ready)
    argv[argv.index("--intent-reference") + 1] = (
        ready[1] if bad_intent == "review" else bad_intent
    )

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid request acquired a client")

    monkeypatch.setattr(WorkspaceSetupReviewClient, "filesystem", forbidden)
    assert main(argv) == 2
    assert json.loads(capsys.readouterr().out)["error"]


def test_missing_qualified_port_has_no_fallback(ready, capsys, monkeypatch):
    monkeypatch.delattr(WorkspaceSetupReviewClient, "observe_action_admission")

    def forbidden(*args, **kwargs):
        pytest.fail("Missing observer acquired a replacement client")

    monkeypatch.setattr(WorkspaceSetupReviewClient, "filesystem", forbidden)
    code, payload = observed(ready, capsys)
    assert code == 2
    assert payload["error"]["error_type"] == "RuntimeError"
    assert payload["stage"] == "preflight" and "client_cleanup" not in payload


@pytest.mark.parametrize(
    "extra", [[], ["--client-intent-id", "new"], ["--accept-reviewed-final-files"]]
)
def test_parser_requires_intent_and_rejects_mutating_options(tmp_path, extra, capsys):
    argv = [
        "workspace",
        "review",
        "observe-admission",
        "--repository-root",
        str(tmp_path),
        "--evidence-root",
        str(tmp_path),
        "--reference",
        "{}",
    ]
    if extra:
        argv += ["--intent-reference", "{}", *extra]
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    assert not tuple(tmp_path.iterdir())
    capsys.readouterr()


@pytest.mark.parametrize(
    "failure,expected", [(ValueError("projection"), 3), (KeyboardInterrupt(), 130)]
)
def test_projection_failure_preserves_known_view_and_once_only_cleanup(
    ready, capsys, monkeypatch, failure, expected
):
    original_projection = module._action_observation_payload
    original_observe = WorkspaceSetupReviewClient.observe_action_admission
    original_release = WorkspaceSetupReviewClient.release_client
    calls = []

    def observe(client, request):
        calls.append("observe")
        return original_observe(client, request)

    def release(client):
        calls.append("release")
        return original_release(client)

    def project(value, result):
        original_projection(value, result)
        raise failure

    monkeypatch.setattr(WorkspaceSetupReviewClient, "observe_action_admission", observe)
    monkeypatch.setattr(WorkspaceSetupReviewClient, "release_client", release)
    monkeypatch.setattr(module, "_action_observation_payload", project)
    code, payload = observed(ready, capsys)
    assert code == expected and payload["status"] == "incomplete"
    assert payload["action_observation"]["observation"] == "validated_retained_intent"
    assert payload["client_cleanup"]["value"]["ledger_complete"]
    assert calls == ["observe", "release"]


def test_real_process_stdin_transport_and_no_top_level_grant(ready):
    argv = arguments(ready, stdin=True)
    frame = {
        "contract": "aware.agent.workspace-review.v1",
        "reference": json.loads(ready[1]),
    }
    before = tuple(inventory(root) for root in ready[0])
    child = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from aware_agent_cli.main import main; raise SystemExit(main())",
            *argv,
        ],
        input=json.dumps(frame),
        text=True,
        capture_output=True,
        env=os.environ.copy(),
        timeout=30,
        check=False,
    )
    assert child.returncode == 0, child.stderr + child.stdout
    payload = json.loads(child.stdout)
    assert payload["reference_input"]["selector"] == "/reference"
    assert "reference" not in payload
    assert before == tuple(inventory(root) for root in ready[0])


def test_human_display_escapes_untrusted_coordinates():
    payload = {
        "status": "completed",
        "action_observation": {
            "target": {
                "value": {
                    "issue_tag": "tag\u202e",
                    "issue_path": "path\nforged",
                }
            }
        },
    }
    output = module._action_observation_summary(payload)
    assert "\u202e" not in output and "\\u202e" in output
    assert "path\\nforged" in output
    assert "unknown/not returned" in output


@pytest.mark.parametrize("fault,expected", [("changed", 3), ("cancel", 130)])
def test_real_owner_read_failure_preserves_incomplete_evidence(
    ready, capsys, monkeypatch, fault, expected
):
    (root, evidence), _, intent, _ = ready
    reference = review_value_from_payload(SetupEvidenceRef, json.loads(intent))
    original_observe = WorkspaceSetupReviewClient.observe_action_admission
    original_release = WorkspaceSetupReviewClient.release_client
    calls = []
    if fault == "changed":
        (evidence / reference.locator).write_bytes(b"changed retained bytes")
    before = inventory(root), inventory(evidence)

    def observe(client, request):
        calls.append("observe")
        read = client._runtime.store.read

        def injected(name, **kwargs):
            if name == reference.locator and fault == "cancel":
                calls.append("interruption")
                raise KeyboardInterrupt("original read interrupted")
            return read(name, **kwargs)

        monkeypatch.setattr(client._runtime.store, "read", injected)
        return original_observe(client, request)

    def release(client):
        calls.append("release")
        return original_release(client)

    monkeypatch.setattr(WorkspaceSetupReviewClient, "observe_action_admission", observe)
    monkeypatch.setattr(WorkspaceSetupReviewClient, "release_client", release)
    code, payload = observed(ready, capsys)
    assert code == expected and payload["status"] == "incomplete"
    assert payload["error"]["retention"]["value"]["status"] == "incomplete"
    assert payload["error"]["outcome"] is None
    assert "action_observation" not in payload
    assert calls.count("observe") == calls.count("release") == 1
    assert before == (inventory(root), inventory(evidence))
    assert "does not establish" in module._summary(payload)


@pytest.mark.parametrize("fault", ["incomplete", "raised"])
def test_independent_cleanup_never_erases_validated_intent(
    ready, capsys, monkeypatch, fault
):
    release = WorkspaceSetupReviewClient.release_client
    calls = []

    def injected(client):
        calls.append("release")
        result = release(client)
        if fault == "raised":
            raise RuntimeError("cleanup return unavailable")
        return replace(result, ledger_complete=False)

    monkeypatch.setattr(WorkspaceSetupReviewClient, "release_client", injected)
    code, payload = observed(ready, capsys)
    assert code == 3 and payload["status"] == "incomplete"
    assert (
        payload["action_observation"]["historical_driver_outcome"] == "not_established"
    )
    assert payload["action_observation"]["authorizes_retry"] is False
    assert calls == ["release"]


@pytest.mark.parametrize("channel", ["stdout", "stderr"])
def test_real_process_closed_pipe_preserves_exit_and_surviving_channel(ready, channel):
    # Real owner reads and release; only the terminal endpoint fails.
    script = """
import os,sys
from aware_agent_cli.main import main
read_fd,write_fd=os.pipe()
os.close(read_fd)
setattr(sys,sys.argv[1],os.fdopen(write_fd,'w'))
if sys.argv[1]=='stderr':
    from aware_agent_cli import workspace_review as m
    original=m.review_payload
    def interrupted(args):
        payload,code,raw=original(args)
        payload['error']={'error_type':'KeyboardInterrupt','authorizes_retry':False,'presentation_errors':{'injected':{'error_type':'KeyboardInterrupt','interruption':True}}}
        payload['status']='incomplete'
        return payload,130,raw
    m.review_payload=interrupted
raise SystemExit(main(sys.argv[2:]))
"""
    argv = arguments(ready, human=True)
    child = subprocess.run(
        [sys.executable, "-B", "-c", script, channel, *argv],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert child.returncode == (3 if channel == "stdout" else 130), child
    assert "validated_retained_intent" in (
        child.stderr if channel == "stdout" else child.stdout
    )
