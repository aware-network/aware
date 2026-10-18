"""Original SDK flow plus explicit byte transport; no simulated owner schema."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import os
import select
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_agent_cli import _review_input as transport
from aware_agent_cli import workspace_review as module
from aware_agent_cli.main import main
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient

SPEC = importlib.util.spec_from_file_location(
    "original_reference_fixture", Path(__file__).with_name("test_workspace_review.py")
)
assert SPEC is not None and SPEC.loader is not None
original = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(original)
repository = original.repository
BASE = "56b18497e86edb717928eb1941a004fbde966e73"
PACKAGE = "workspaces/aware_agent/modules/agent/libs/agent_cli/python"
ROOT = Path(__file__).resolve().parents[8]


def frame(reference=None, **extra):
    return {
        "contract": "aware.agent.workspace-review.v1",
        "reference": {"unit": "framing only, not an owner reference"}
        if reference is None
        else reference,
        **extra,
    }


def read(body):
    observation = transport.input_observation()
    buffer = io.BytesIO(body)
    stream = SimpleNamespace(isatty=lambda: False, buffer=buffer)
    selected = transport.read_result_reference(stream, observation)
    assert not buffer.closed
    return selected, observation


@pytest.mark.parametrize(
    "body,code",
    [
        (b"", "invalid_json"),
        (b"[]", "frame_required"),
        (b'{"contract":"wrong","reference":{}}', "frame_required"),
        (b'{"contract":"aware.agent.workspace-review.v1"}', "reference_required"),
        (
            b'{"contract":"aware.agent.workspace-review.v1","reference":null}',
            "reference_required",
        ),
        (
            b'{"contract":"aware.agent.workspace-review.v1","nested":{"reference":{}}}',
            "reference_required",
        ),
        (b'{"contract":0,"contract":1}', "duplicate_key"),
        (
            json.dumps(frame(extra={"a": 1}))
            .replace('"a": 1', '"a": 1, "a": 2')
            .encode(),
            "duplicate_key",
        ),
        (b"\xff", "invalid_utf8"),
        (
            b'{"contract":"aware.agent.workspace-review.v1","reference":{},"extra":"\\ud800"}',
            "invalid_utf8",
        ),
        (
            b'{"contract":"aware.agent.workspace-review.v1","reference":{},"\\ud800":0}',
            "invalid_utf8",
        ),
        (b"{}{}", "invalid_json"),
        (b"\xef\xbb\xbf{}", "invalid_json"),
        (b'{"extra":NaN}', "non_finite"),
        (b'{"extra":Infinity}', "non_finite"),
        (b'{"extra":1e999}', "non_finite"),
    ],
)
def test_framing_refuses_with_fixed_codes(body, code):
    with pytest.raises(
        transport.ReferenceInputError, match="^reference_input_" + code + "$"
    ):
        read(body)


def test_top_level_only_exact_metadata_and_no_status_authority():
    body = json.dumps(
        frame(
            {"chosen": 1},
            nested={"reference": {"chosen": 2}},
            status="completed",
            ready_for_decision=True,
        )
    ).encode()
    selected, metadata = read(body)
    assert selected == {"chosen": 1}
    assert metadata == {
        "source": "stdin_agent_result_v1",
        "selector": "/reference",
        "byte_count": len(body),
        "eof": True,
        "source_sha256": "sha256:" + hashlib.sha256(body).hexdigest(),
    }


def test_exact_byte_ceiling_and_over_limit_prefix():
    body = json.dumps(frame()).encode()
    exact = body + b" " * (transport.MAX_FRAME_BYTES - len(body))
    assert read(exact)[1]["eof"]
    metadata = transport.input_observation()
    with pytest.raises(
        transport.ReferenceInputError, match="reference_input_byte_limit"
    ):
        transport.read_result_reference(
            SimpleNamespace(
                isatty=lambda: False, buffer=io.BytesIO(exact + b"trailing")
            ),
            metadata,
        )
    assert metadata["byte_count"] == transport.MAX_FRAME_BYTES + 1
    assert not metadata["eof"] and metadata["source_sha256"] is None


@pytest.mark.parametrize("kind", ["depth", "nodes"])
def test_structural_limits(kind):
    if kind == "depth":
        value = 0
        for _ in range(65):
            value = [value]
    else:
        value = [0] * 65_536
    with pytest.raises(
        transport.ReferenceInputError,
        match="reference_input_" + ("depth_limit" if kind == "depth" else "node_limit"),
    ):
        read(json.dumps(frame(extra=value)).encode())


@pytest.mark.parametrize(
    "reason", ["tty", "missing", "none", "text", "error", "interrupt"]
)
def test_input_failures_keep_prefix_cause_and_caller_ownership(reason):
    metadata = transport.input_observation()
    failure = (
        KeyboardInterrupt("fixture cancellation")
        if reason == "interrupt"
        else OSError("fixture I/O")
    )

    class Buffer:
        calls = 0

        def read(self, count):
            self.calls += 1
            if self.calls == 1:
                return b"prefix"
            if reason == "none":
                return None
            if reason == "text":
                return "not bytes"
            raise failure

        def close(self):
            pytest.fail("caller input was closed")

    buffer = Buffer()
    stream = SimpleNamespace(isatty=lambda: reason == "tty")
    if reason != "missing":
        stream.buffer = buffer
    with pytest.raises(BaseException) as result:
        transport.read_result_reference(stream, metadata)
    error = result.value
    if reason == "interrupt":
        assert (
            error is failure
            and error.reference_input_code == "reference_input_interrupted"
        )
    else:
        expected = (
            "interactive"
            if reason == "tty"
            else "unavailable"
            if reason == "missing"
            else "read_failed"
        )
        assert (
            type(error) is transport.ReferenceInputError
            and str(error) == "reference_input_" + expected
        )
        if reason == "error":
            assert error.__cause__ is failure
    assert not metadata["eof"] and metadata["source_sha256"] is None
    assert metadata["byte_count"] == (0 if reason in ("tty", "missing") else 6)


def arguments(repository, action, *, json_mode=True):
    root, evidence = repository
    result = [
        "workspace",
        "review",
        action,
        "--repository-root",
        str(root),
        "--evidence-root",
        str(evidence),
        "--reference-from-stdin",
    ]
    if json_mode:
        result.append("--json")
    return result


def receive(repository, capsys, monkeypatch, action, payload, *extra, json_mode=True):
    stream = io.TextIOWrapper(
        io.BytesIO(json.dumps(payload).encode()), encoding="utf-8"
    )
    monkeypatch.setattr(sys, "stdin", stream)
    code = main([*arguments(repository, action, json_mode=json_mode), *extra])
    assert not stream.closed
    captured = capsys.readouterr()
    return code, json.loads(captured.out) if json_mode else captured.out, captured.err


def test_genuine_stdin_two_reviews_and_explicit_apply(repository, capsys, monkeypatch):
    root, _ = repository
    foreign = (root / "foreign.py").read_bytes(), (root / "foreign.py").stat().st_mode
    first = original.prepare(repository, capsys)
    code, history, _ = receive(repository, capsys, monkeypatch, "show", first)
    assert code == 0 and history["purpose"] == "history"
    assert history["reference"] == first["reference"]
    code, second, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "scope",
        first,
        "--client-intent-id",
        "stdin-scope",
        "--accept-reviewed-effect-scope",
    )
    assert code == 0 and not (root / "aware.repo.toml").exists()
    assert second["result"]["value"]["decision_required"] == "apply_review"
    code, applied, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "apply",
        second,
        "--client-intent-id",
        "stdin-apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0 and applied["outcome"]["product_status"] == "apply_completed"
    assert (root / "aware.repo.toml").is_file()
    assert (
        applied["outcome"]["original_evidence"]["workspace_result"]["value"]["release"]
        == "unknown"
    )
    assert foreign == (
        (root / "foreign.py").read_bytes(),
        (root / "foreign.py").stat().st_mode,
    )


@pytest.mark.parametrize("focus", ["overview", "scope", "files", "guards"])
def test_focused_history_retains_context_uncertainty_and_complete_selected_lists(
    repository, capsys, monkeypatch, focus
):
    root, _ = repository
    issue = root / original.ISSUE
    issue.write_text(
        issue.read_text() + "".join(f"- `preserved-{n}.py`\n" for n in range(12))
    )
    first = original.prepare(repository, capsys)
    code, human, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "show",
        first,
        "--focus",
        focus,
        json_mode=False,
    )
    assert code == 0
    assert "Historical review only" in human and "no current-use authority" in human
    assert (
        "Original Workspace release:" in human and "Client cleanup complete:" in human
    )
    record = first["review"]["value"]
    if focus == "scope":
        for path in record["existing_scope"] + record["physical_scope"]:
            assert json.dumps(path, ensure_ascii=True) in human
        assert "Additional paths omitted" not in human
    if focus == "files":
        for path in record["final_files"]:
            assert json.dumps(path) in human
    if focus == "guards":
        assert (
            "Original Issue byte guard:" in human
            and "Original authority-manifest byte guard:" in human
        )
        for guard in record["review_guards"]["value"].values():
            assert json.dumps(guard) in human


def test_omitted_focus_is_byte_identical_to_predecessor_summary(repository, capsys):
    first, second = original.scoped(repository, capsys)
    source = subprocess.check_output(
        ["git", "show", BASE + ":" + PACKAGE + "/aware_agent_cli/workspace_review.py"],
        cwd=ROOT,
    )
    old_function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "_summary"
    )
    namespace = dict(vars(module))
    exec(  # noqa: S102 -- replay one hash-bound committed summary, not input code
        compile(
            ast.Module(body=[old_function], type_ignores=[]), "accepted_summary", "exec"
        ),
        namespace,
    )
    for payload in (first, second):
        assert module._summary(payload) == namespace["_summary"](payload)


def test_focused_scope_escapes_untrusted_paths_without_changing_owner_value(
    repository, capsys, monkeypatch
):
    issue = repository[0] / original.ISSUE
    path = "foreign\u202efile.py"
    issue.write_text(issue.read_text() + "- `" + path + "`\n")
    first = original.prepare(repository, capsys)
    assert path in first["review"]["value"]["existing_scope"]
    code, human, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "show",
        first,
        "--focus",
        "scope",
        json_mode=False,
    )
    assert code == 0 and "\u202e" not in human and r"\u202e" in human


@pytest.mark.parametrize("drift", ["issue", "manifest"])
def test_unchanged_stdin_reference_stale_refuses_without_refresh(
    repository, capsys, monkeypatch, drift
):
    _, second = original.scoped(repository, capsys)
    root, _ = repository
    path = root / (original.ISSUE if drift == "issue" else "aware.protocol.toml")
    changed = path.read_bytes() + b"\n# explicit fixture drift\n"
    path.write_bytes(changed)
    code, refusal, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "apply",
        second,
        "--client-intent-id",
        "stale-stdin",
        "--accept-reviewed-final-files",
    )
    assert code == 2 and refusal["error"]["code"] == (
        "review_issue_changed"
        if drift == "issue"
        else "review_authority_sources_changed"
    )
    assert path.read_bytes() == changed and not (root / "aware.repo.toml").exists()
    assert not refusal["authorizes_retry"]


def test_deliberate_spent_reuse_keeps_incompleteness_and_bytes(
    repository, capsys, monkeypatch
):
    _, second = original.scoped(repository, capsys)
    code, _applied, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "apply",
        second,
        "--client-intent-id",
        "first-apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0
    root, _ = repository
    paths = (root / "aware.repo.toml", root / original.ISSUE, root / "foreign.py")
    before = [(p.read_bytes(), p.stat().st_mode) for p in paths]
    code, refused, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "apply",
        second,
        "--client-intent-id",
        "deliberate-reuse",
        "--accept-reviewed-final-files",
    )
    assert code == 3 and refused["status"] == "incomplete"
    assert not refused["authorizes_retry"]
    assert before == [(p.read_bytes(), p.stat().st_mode) for p in paths]


@pytest.mark.parametrize("action", ["scope", "apply"])
def test_missing_consent_never_reads_stdin_or_acquires_client(
    repository, capsys, monkeypatch, action
):
    def unexpected(*a, **kw):
        pytest.fail("missing consent reached acquisition/input")

    monkeypatch.setattr(WorkspaceSetupReviewClient, "filesystem", unexpected)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=unexpected))
    with pytest.raises(SystemExit) as result:
        main([*arguments(repository, action), "--client-intent-id", "missing-consent"])
    assert result.value.code == 2
    capsys.readouterr()


def test_focus_json_conflict_precedes_input_and_sdk(repository, capsys, monkeypatch):
    def unexpected(*a, **kw):
        pytest.fail("incompatible flags reached input/client")

    monkeypatch.setattr(WorkspaceSetupReviewClient, "filesystem", unexpected)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=unexpected))
    assert main([*arguments(repository, "show"), "--focus", "guards"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error"]["code"] == "review_focus_json_incompatible"


@pytest.mark.parametrize(
    "payload", [b"private secret body", json.dumps(frame()).encode()]
)
def test_invalid_transport_or_original_wire_precedes_sdk_acquisition(
    repository, capsys, monkeypatch, payload
):
    monkeypatch.setattr(
        WorkspaceSetupReviewClient,
        "filesystem",
        lambda **kw: pytest.fail("bad input acquired client"),
    )
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(payload)))
    assert main(arguments(repository, "show")) == 2
    output = capsys.readouterr().out
    assert "private secret body" not in output
    result = json.loads(output)
    assert "reference" not in result and result["reference_input"]["eof"]
    if payload.startswith(b"private"):
        assert result["error"]["code"] == "reference_input_invalid_json"
    else:
        assert not result["error"]["code"].startswith("reference_input_")


def test_depth_and_node_exact_boundaries():
    value = 0
    for _ in range(63):
        value = [value]
    assert read(json.dumps(frame(extra=value)).encode())[0]
    with pytest.raises(
        transport.ReferenceInputError, match="reference_input_depth_limit"
    ):
        read(json.dumps(frame(extra=[value])).encode())
    assert read(json.dumps(frame(extra=[0] * (65_536 - 9))).encode())[0]
    with pytest.raises(
        transport.ReferenceInputError, match="reference_input_node_limit"
    ):
        read(json.dumps(frame(extra=[0] * (65_536 - 8))).encode())


def test_decoder_recursion_failure_preserves_cause():
    with pytest.raises(
        transport.ReferenceInputError, match="reference_input_depth_limit"
    ) as result:
        read(b"[" * 20_000 + b"0" + b"]" * 20_000)
    assert isinstance(result.value.__cause__, RecursionError)


def test_wrong_kind_stays_owner_refusal_and_raw_evidence_stays_exact(
    repository, capsys, monkeypatch
):
    _, second = original.scoped(repository, capsys)
    code, applied, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "apply",
        second,
        "--client-intent-id",
        "kind-apply",
        "--accept-reviewed-final-files",
    )
    assert code == 0
    code, refusal, _ = receive(repository, capsys, monkeypatch, "show", applied)
    (repository[0].parent / "wrong-kind-result.json").write_text(
        json.dumps(refusal, indent=2)
    )
    assert code == 3 and refusal["status"] == "incomplete"
    assert not refusal["error"]["code"].startswith("reference_input_")
    root, evidence = repository
    assert (
        main(
            [
                "workspace",
                "review",
                "evidence",
                "--repository-root",
                str(root),
                "--evidence-root",
                str(evidence),
                "--reference",
                original.reference(applied),
            ]
        )
        == 0
    )
    old = capsys.readouterr()
    stream = io.TextIOWrapper(io.BytesIO(json.dumps(applied).encode()))
    monkeypatch.setattr(sys, "stdin", stream)
    assert main(arguments(repository, "evidence", json_mode=False)) == 0
    new = capsys.readouterr()
    assert old.out == new.out
    assert json.loads(new.err)["reference_input"]["eof"] and not stream.closed


@pytest.mark.parametrize("change", ["digest", "target", "root"])
def test_original_reader_rejects_wrong_reference_bindings(
    repository, capsys, monkeypatch, change
):
    first = original.prepare(repository, capsys)
    root, _ = repository
    supplied = json.loads(json.dumps(first))
    value = supplied["reference"]["value"]
    if change == "digest":
        value["record_sha256"] = "sha256:" + "0" * 64
    elif change == "target":
        value["target"]["value"]["issue_path"] = "wrong-issue.md"
    else:
        value["root_identity"]["value"]["inode"] += 1
    before = (root / original.ISSUE).read_bytes(), (root / "foreign.py").read_bytes()
    code, refusal, _ = receive(
        repository,
        capsys,
        monkeypatch,
        "scope",
        supplied,
        "--client-intent-id",
        "wrong-binding",
        "--accept-reviewed-effect-scope",
    )
    (root.parent / ("wrong-binding-" + change + ".json")).write_text(
        json.dumps(refusal, indent=2)
    )
    assert code == 3 and refusal["status"] == "incomplete" and "error" in refusal
    assert not refusal["error"].get("code", "").startswith("reference_input_")
    assert not (root / "aware.repo.toml").exists()
    assert before == (
        (root / original.ISSUE).read_bytes(),
        (root / "foreign.py").read_bytes(),
    )


@pytest.mark.parametrize("action", ["show", "evidence"])
def test_real_stdin_eof_through_source_command(repository, capsys, action):
    first = original.prepare(repository, capsys)
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from aware_agent_cli.main import main; raise SystemExit(main())",
            *arguments(repository, action),
        ],
        input=json.dumps(first).encode(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0
    if action == "show":
        payload = json.loads(completed.stdout)
        assert payload["purpose"] == "history" and payload["reference_input"]["eof"]
        assert payload["reference"] == first["reference"]
    else:
        assert json.loads(completed.stderr)["reference_input"]["eof"]
        assert (
            json.loads(completed.stdout).get("contract")
            != "aware.agent.workspace-review.v1"
        )


def test_real_stdin_process_scope_then_apply_after_both_reviews(repository, capsys):
    root, _ = repository
    first = original.prepare(repository, capsys)
    foreign = (root / "foreign.py").read_bytes(), (root / "foreign.py").stat().st_mode
    assert first["result"]["value"]["decision_required"] == "scope_review"
    scope = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from aware_agent_cli.main import main; raise SystemExit(main())",
            *arguments(repository, "scope"),
            "--client-intent-id",
            "process-scope",
            "--accept-reviewed-effect-scope",
        ],
        input=json.dumps(first).encode(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert scope.returncode == 0, scope.stdout + scope.stderr
    second = json.loads(scope.stdout)
    assert second["result"]["value"]["decision_required"] == "apply_review"
    assert second["scope_completion"]["original_outcome"]["outcome"] == "applied"
    assert not (root / "aware.repo.toml").exists()
    # Separate explicit decision, after inspecting the actual second result.
    apply = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "from aware_agent_cli.main import main; raise SystemExit(main())",
            *arguments(repository, "apply"),
            "--client-intent-id",
            "process-apply",
            "--accept-reviewed-final-files",
        ],
        input=json.dumps(second).encode(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert apply.returncode == 0, apply.stdout + apply.stderr
    outcome = json.loads(apply.stdout)
    assert outcome["outcome"]["product_status"] == "apply_completed"
    assert (
        outcome["reference_input"]["source_sha256"]
        == "sha256:" + hashlib.sha256(json.dumps(second).encode()).hexdigest()
    )
    assert (root / "aware.repo.toml").is_file()
    assert foreign == (
        (root / "foreign.py").read_bytes(),
        (root / "foreign.py").stat().st_mode,
    )


def test_legacy_inline_never_reads_stdin_or_adds_metadata(
    repository, capsys, monkeypatch
):
    first = original.prepare(repository, capsys)

    def unexpected():
        pytest.fail("legacy input read stdin")

    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=unexpected))
    code, history = original.invoke(
        repository, capsys, "show", "--reference", original.reference(first)
    )
    assert code == 0 and "reference_input" not in history


def test_real_sigint_during_partial_stdin_preserves_130_without_acquisition(tmp_path):
    ready_read, ready_write = os.pipe()
    script = f"""
import json, os, sys
from pathlib import Path
from types import SimpleNamespace
from aware_agent_cli.main import main
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
calls = []
def unexpected(**kw):
    calls.append('client')
    raise AssertionError('partial transport reached SDK')
WorkspaceSetupReviewClient.filesystem = unexpected
real = sys.stdin.buffer
class ObservedInput:
    calls = 0
    def read(self, count):
        self.calls += 1
        # On the second read the caller has already recorded the first prefix.
        if self.calls == 2: os.write({ready_write}, b'R')
        return real.read(count)
sys.stdin = SimpleNamespace(isatty=lambda: False, buffer=ObservedInput())
code = main(['workspace','review','show','--repository-root',{str(tmp_path / "customer")!r},
             '--evidence-root',{str(tmp_path / "evidence")!r},'--reference-from-stdin','--json'])
Path({str(tmp_path / "trace.json")!r}).write_text(json.dumps(calls))
raise SystemExit(code)
"""
    env = dict(os.environ, CODEX_THREAD_ID="agent-reference-process")
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pass_fds=(ready_write,),
        env=env,
    )
    os.close(ready_write)
    try:
        process.stdin.write(b" " * 65_536)
        process.stdin.flush()
        assert select.select([ready_read], [], [], 10)[0]
        assert os.read(ready_read, 1) == b"R"
        process.send_signal(signal.SIGINT)
        assert process.wait(timeout=10) == 130
        output, error = process.communicate(timeout=10)
    finally:
        os.close(ready_read)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)
    assert not error
    payload = json.loads(output)
    assert payload["error"]["code"] == "reference_input_interrupted"
    assert payload["reference_input"]["byte_count"] == 65_536
    assert (
        not payload["reference_input"]["eof"]
        and payload["reference_input"]["source_sha256"] is None
    )
    assert json.loads((tmp_path / "trace.json").read_bytes()) == []
    assert not (tmp_path / "customer").exists()


@pytest.mark.parametrize("mode", ["complete", "failed", "interrupted"])
@pytest.mark.parametrize("channel", ["stdout", "stderr", "both"])
def test_real_refusal_closed_pipes_preserve_owner_reason_cleanup_and_exit(
    repository, capsys, monkeypatch, tmp_path, mode, channel
):
    first, argv = original.stale_refusal_arguments(
        repository, capsys, monkeypatch, "issue", "read"
    )
    index = argv.index("--reference")
    argv[index : index + 2] = ["--reference-from-stdin"]
    script = f"""
import json
from pathlib import Path
from aware_agent_cli import workspace_review as module
from aware_agent_cli.main import main
from aware_workspace_sdk.architecture_setup_review import WorkspaceSetupReviewClient
from aware_workspace_fs_adapter.architecture_setup_review import FilesystemSetupReview
from aware_workspace_runtime.architecture_setup_review import WorkspaceSetupReviewRuntime
calls = {{'payload':0, 'capture':0, 'release':0, 'product':0}}
payload, capture, release = module.review_payload, FilesystemSetupReview.write_metadata, WorkspaceSetupReviewClient.release_client
def observe(args):
    calls['payload'] += 1
    return payload(args)
def record(*a, **kw):
    calls['capture'] += 1
    if {mode!r} == 'failed': raise OSError('capture unavailable')
    if {mode!r} == 'interrupted': raise KeyboardInterrupt('capture interrupted')
    return capture(*a, **kw)
def cleanup(owner):
    calls['release'] += 1
    return release(owner)
def no_product(*a, **kw):
    calls['product'] += 1
    raise AssertionError('stale refusal dispatched product')
module.review_payload = observe
FilesystemSetupReview.write_metadata = record
WorkspaceSetupReviewClient.release_client = cleanup
WorkspaceSetupReviewRuntime._run_driver = no_product
code = main({argv!r})
Path({str(tmp_path / "process-trace.json")!r}).write_text(json.dumps({{'code':code,'calls':calls}}))
raise SystemExit(code)
"""
    reader, writer = os.pipe()
    os.close(reader)
    try:
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script],
            input=json.dumps(first).encode(),
            stdout=writer if channel in ("stdout", "both") else subprocess.PIPE,
            stderr=writer if channel in ("stderr", "both") else subprocess.PIPE,
            check=False,
            timeout=30,
        )
    finally:
        os.close(writer)
    expected = (
        130
        if mode == "interrupted"
        else 2
        if mode == "complete" and channel == "stderr"
        else 3
    )
    assert completed.returncode == expected
    trace = json.loads((tmp_path / "process-trace.json").read_bytes())
    assert trace == {
        "code": expected,
        "calls": {"payload": 1, "capture": 1, "release": 1, "product": 0},
    }
    if channel == "stdout":
        assert b"review_issue_changed" in completed.stderr
        assert b"Exception ignored" not in completed.stderr
    if channel == "stderr":
        assert b"review_issue_changed" in completed.stdout
        if mode != "complete":
            result = json.loads(completed.stdout)
            assert result["status"] == "incomplete"
            assert result["reference_input"]["eof"]
    assert not (repository[0] / "aware.repo.toml").exists()
