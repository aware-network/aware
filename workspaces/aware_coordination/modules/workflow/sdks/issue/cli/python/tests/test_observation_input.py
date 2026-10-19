"""Original registrar transport boundary; controlled consumers are not admission."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_runtime import parse_issue_projection
from aware_issue_sdk import (
    IssueMutationOutcome,
    IssueReadProjectionResolveOutcome,
    IssueReadProjectionResolveRequest,
    IssueReadProjectionResolveResult,
    IssueSdkOperationClient,
)
from test_provider import ISSUE_REF as REAL_ISSUE
from test_provider import _repository
from test_repository_e2e import _argv as publication_arguments
from test_repository_runtime_orchestration import composed_loop

composed = composed_loop

cli = importlib.import_module("aware_issue_cli.main")
reader = importlib.import_module("aware_issue_cli.observation_input")
ISSUE = "fb/2026-10-19/input-test"
ACTOR = "codex-input-test"


def frame(*, status="In Progress"):
    projection = parse_issue_projection(
        text=f"# Issue: input fixture\n\n- Tag: {ISSUE}\n- Status: {status}\n- Owner: {ACTOR}\n\n## Ownership Scope\n- `README.md`\n",
        source_path="docs/issues/input-test.md",
    )
    return IssueReadProjectionResolveResult(
        IssueReadProjectionResolveOutcome.FOUND,
        ISSUE,
        "test:provider",
        "test-provider",
        "0.0.0",
        projection,
    ).to_wire()


def arguments(command, *, source=True, format_name="json"):
    argv = [
        command,
        "--repository-root",
        "/explicit/repository",
        "--issue-ref",
        ISSUE,
        "--actor-ref",
        ACTOR,
        "--actor-evidence-ref",
        "harness:test",
        "--client-intent-id",
        "intent:test",
        "--format",
        format_name,
    ]
    if source:
        argv.append("--issue-observation-from-stdin")
    if command == "bind-scope":
        argv += ["--scope-path", "README.md"]
    elif command == "publish-close":
        argv += [
            "--path",
            "README.md",
            "--message",
            "Explicit publication",
            "--resolution",
            "Completed",
            "--verified-by",
            "controlled proof",
            "--dry-run",
        ]
    return argv


def input_stream(body):
    return SimpleNamespace(buffer=io.BytesIO(body), isatty=lambda: False)


@pytest.mark.parametrize("command", ["bind-scope", "start-progress", "publish-close"])
def test_selected_observation_enters_original_typed_request(
    monkeypatch, capsys, command
):
    original = frame()
    stream = input_stream(json.dumps(original).encode())
    seen = []
    monkeypatch.setattr(cli.sys, "stdin", stream)

    class Client:
        def __init__(self, **kwargs):
            pass

        def __getattr__(self, name):
            def consume(request):
                seen.append(request)
                return SimpleNamespace(
                    outcome="planned"
                    if command == "publish-close"
                    else IssueMutationOutcome.APPLIED,
                    to_wire=lambda: {
                        "outcome": "planned"
                        if command == "publish-close"
                        else "applied"
                    },
                )

            return consume

    def provider(**kwargs):
        assert stream.buffer.tell() == len(stream.buffer.getvalue())
        assert kwargs["repository_root"] == "/explicit/repository"
        return object()

    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", provider)
    monkeypatch.setattr(cli, "IssueSdkOperationClient", Client)
    monkeypatch.setattr(cli, "create_repository_client", lambda **kwargs: object())
    assert cli.main(arguments(command)) == 0
    assert len(seen) == 1
    request = seen[0]
    guard = (
        request.expected_issue_source_sha256
        if command == "publish-close"
        else request.expected_source_sha256
    )
    assert guard == original["projection"]["source"]["digest"]
    assert request.actor_ref == ACTOR and request.actor_evidence_ref == "harness:test"
    assert not stream.buffer.closed
    assert "input_observation" not in json.loads(capsys.readouterr().out)


def forbidden(*args, **kwargs):
    raise AssertionError("input refusal must not acquire or dispatch an owner")


@pytest.fixture
def no_provider(monkeypatch):
    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", forbidden)
    monkeypatch.setattr(cli, "IssueSdkOperationClient", forbidden)
    monkeypatch.setattr(cli, "create_repository_client", forbidden)


@pytest.mark.parametrize("command", ["bind-scope", "start-progress", "publish-close"])
@pytest.mark.parametrize("mode", ["missing", "both", "repeated", "wrong_guard"])
def test_source_selection_refuses_without_input_or_provider(
    no_provider, monkeypatch, capsys, command, mode
):
    monkeypatch.setattr(cli.sys, "stdin", SimpleNamespace(isatty=forbidden))
    argv = arguments(command, source=mode != "missing")
    direct = (
        "--expected-issue-source-sha256"
        if command == "publish-close"
        else "--expected-source-sha256"
    )
    if mode == "both":
        argv += [direct, "sha256:" + "a" * 64]
    elif mode == "repeated":
        argv += ["--issue-observation-from-stdin"]
    elif mode == "wrong_guard":
        argv += [
            "--expected-source-sha256"
            if command == "publish-close"
            else "--expected-issue-source-sha256",
            "sha256:" + "a" * 64,
        ]
    if mode == "repeated":
        assert cli.main(argv) == 2
        assert (
            json.loads(capsys.readouterr().out)["code"]
            == "issue_observation_input_conflict"
        )
    else:
        with pytest.raises(SystemExit) as failure:
            cli.main(argv)
        assert failure.value.code == 2


@pytest.mark.parametrize("command", ["bind-scope", "start-progress", "publish-close"])
def test_relative_root_refuses_without_reading_stdin(
    no_provider, monkeypatch, capsys, command
):
    monkeypatch.setattr(cli.sys, "stdin", SimpleNamespace(isatty=forbidden))
    argv = arguments(command)
    argv[argv.index("--repository-root") + 1] = "relative-root"
    assert cli.main(argv) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "issue_observation_input_repository_required"
    assert payload["input_observation"] == reader.input_observation()


@pytest.mark.parametrize("command", ["bind-scope", "start-progress", "publish-close"])
def test_direct_guard_never_reads_stdin(monkeypatch, capsys, command):
    seen = []
    monkeypatch.setattr(cli.sys, "stdin", SimpleNamespace(isatty=forbidden))
    monkeypatch.setattr(
        cli,
        "FilesystemIssueOperationProvider",
        lambda **kw: seen.append(kw) or object(),
    )
    monkeypatch.setattr(cli, "create_repository_client", lambda **kw: object())

    class Client:
        def __init__(self, **kwargs):
            pass

        def __getattr__(self, name):
            def call(request):
                return SimpleNamespace(
                    outcome="planned", to_wire=lambda: {"outcome": "planned"}
                )

            return call

    monkeypatch.setattr(cli, "IssueSdkOperationClient", Client)
    argv = arguments(command, source=False)
    flag = (
        "--expected-issue-source-sha256"
        if command == "publish-close"
        else "--expected-source-sha256"
    )
    argv += [flag, "sha256:" + "a" * 64]
    assert cli.main(argv) == 0
    assert len(seen) == 1


@pytest.mark.parametrize(
    "command",
    [
        "block",
        "resume",
        "close",
        "commit-workspace",
        "resolve-read-projection",
        "ensure-snapshot",
        "append-update",
        "append-evidence",
        "set-owner",
        "present-receipt",
    ],
)
def test_unsupported_commands_do_not_gain_flag(no_provider, command):
    with pytest.raises(SystemExit) as failure:
        cli.main([command, "--issue-observation-from-stdin"])
    assert failure.value.code == 2


@pytest.mark.parametrize(
    "body,code",
    [
        (b"", "invalid_json"),
        (b"{}{}", "invalid_json"),
        (b"[]", "invalid_result"),
        (b'{"a":{"b":1,"b":2}}', "duplicate_key"),
        (b'{"x":NaN}', "invalid_json"),
        (b'{"x":Infinity}', "invalid_json"),
        (b'{"x":1e999}', "invalid_json"),
        (b'{"x":1.0}', "invalid_json"),
        (b"\xff", "invalid_utf8"),
        (b"\xef\xbb\xbf{}", "invalid_utf8"),
        (b'{"x":"\\ud800"}', "invalid_utf8"),
        (b"[" * 34 + b"]" * 34, "structure_limit"),
        (json.dumps({"x": [0] * 4097}).encode(), "structure_limit"),
        (json.dumps({"x": [{"a": 0}] * 3000}).encode(), "structure_limit"),
        (json.dumps({"x": "x" * 262145}).encode(), "structure_limit"),
    ],
)
@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_invalid_frame_refuses_with_complete_private_input_account(
    no_provider, monkeypatch, capsys, body, code, format_name
):
    stream = input_stream(body)
    monkeypatch.setattr(cli.sys, "stdin", stream)
    assert cli.main(arguments("start-progress", format_name=format_name)) == 2
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {
        "contract",
        "code",
        "phase",
        "operation_ref",
        "issue_ref",
        "input_observation",
        "provider_invoked",
        "effect",
        "authorizes_retry",
    }
    assert payload["code"] == "issue_observation_input_" + code
    assert payload["provider_invoked"] is False and payload["effect"] == "none"
    observation = payload["input_observation"]
    assert observation["eof"] and observation["byte_count"] == len(body)
    assert observation["source_sha256"] == "sha256:" + hashlib.sha256(body).hexdigest()
    assert not observation["result_validation_complete"]
    assert observation["selected_issue_guard"] is None
    assert not stream.buffer.closed


@pytest.mark.parametrize(
    "mode,code",
    [
        ("absent", "not_found"),
        ("malformed", "not_found"),
        ("unsupported", "not_found"),
        ("unavailable", "not_found"),
        ("other_issue", "issue_mismatch"),
        ("other_actor", "actor_mismatch"),
        ("traversal", "path_invalid"),
        ("absolute", "path_invalid"),
        ("dot", "path_invalid"),
        ("backslash", "path_invalid"),
        ("digest", "invalid_result"),
        ("revision", "invalid_result"),
        ("contract", "invalid_result"),
        ("summary", "invalid_result"),
    ],
)
def test_original_codec_and_explicit_correlations(
    no_provider, monkeypatch, capsys, mode, code
):
    value = frame()
    if mode in {"absent", "malformed", "unsupported", "unavailable"}:
        value.update(
            outcome={
                "unsupported": "unsupported_profile",
                "unavailable": "authority_unavailable",
            }.get(mode, mode),
            projection=None,
        )
    elif mode == "other_issue":
        value["issue_ref"] = value["projection"]["issue_ref"] = "fb/2026-10-19/other"
    elif mode == "other_actor":
        value["projection"]["identity"]["owner_ref"] = "another-actor"
    elif mode in {"traversal", "absolute", "dot", "backslash"}:
        value["projection"]["source"]["path"] = {
            "traversal": "../outside.md",
            "absolute": "/absolute.md",
            "dot": "a/./b.md",
            "backslash": "a\\b.md",
        }[mode]
    elif mode == "digest":
        value["projection"]["source"]["digest"] = "invalid"
    elif mode == "revision":
        value["projection"]["revision"]["projection_revision"] = "sha256:" + "f" * 64
    elif mode == "contract":
        value["contract"] = "aware.issue.mutation-result.v1"
    else:
        value = {"view": "aware.issue.cli-summary.v2", "result": value}
    seen = []
    original = reader.decode_issue_result

    def decode(operation, wire):
        seen.append(operation)
        return original(operation, wire)

    monkeypatch.setattr(reader, "decode_issue_result", decode)
    stream = input_stream(json.dumps(value).encode())
    monkeypatch.setattr(cli.sys, "stdin", stream)
    assert cli.main(arguments("bind-scope")) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["code"] == "issue_observation_input_" + code
    assert seen == [reader.ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF]
    assert output["input_observation"]["selected_issue_guard"] is None


class BoundedStream:
    def __init__(self, body, *, error=None, partial=False):
        self.buffer = self
        self.body = body
        self.position = 0
        self.requests = []
        self.error = error
        self.partial = partial
        self.closed = False

    def isatty(self):
        return False

    def read(self, size):
        self.requests.append(size)
        if self.error is not None and (not self.partial or self.position):
            raise self.error
        count = min(size, 7 if self.partial else size)
        result = self.body[self.position : self.position + count]
        self.position += len(result)
        return result

    def close(self):
        pytest.fail("Borrowed stdin must never be closed")


@pytest.mark.parametrize("excess", [0, 1, 6000])
def test_raw_whitespace_counts_and_only_one_excess_byte_is_captured(excess):
    body = json.dumps(frame()).encode()
    body += b" " * (reader.MAX_BYTES - len(body) + excess)
    stream = BoundedStream(body)
    if excess:
        with pytest.raises(reader.ObservationInputError) as failure:
            reader.read_issue_guard(stream, issue_ref=ISSUE, actor_ref=ACTOR)
        assert failure.value.code == "issue_observation_input_byte_limit"
        observation = failure.value.observation
        assert observation["byte_count"] == reader.MAX_BYTES + 1
        assert not observation["eof"] and observation["source_sha256"] is None
    else:
        guard, observation = reader.read_issue_guard(
            stream, issue_ref=ISSUE, actor_ref=ACTOR
        )
        assert guard == frame()["projection"]["source"]["digest"]
        assert (
            observation["source_sha256"] == "sha256:" + hashlib.sha256(body).hexdigest()
        )
        assert observation["source_sha256"] != guard
        assert observation["byte_count"] == reader.MAX_BYTES and observation["eof"]
        assert observation["result_validation_complete"]
    assert max(stream.requests) <= reader.MAX_CHUNK
    assert not stream.closed


@pytest.mark.parametrize("cause_type", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("partial", [False, True])
def test_read_failure_preserves_cause_count_and_no_retry(cause_type, partial):
    cause = cause_type("PRIVATE-CAUSE-NOT-FOR-OUTPUT")
    stream = BoundedStream(b"partial-input", error=cause, partial=partial)
    with pytest.raises(reader.ObservationInputError) as caught:
        reader.read_issue_guard(stream, issue_ref=ISSUE, actor_ref=ACTOR)
    error = caught.value
    assert error.original_cause is cause
    assert error.code == "issue_observation_input_" + (
        "read_failed" if cause_type is OSError else "interrupted"
    )
    assert error.observation["byte_count"] == (7 if partial else 0)
    assert error.observation["source_sha256"] is None and not error.observation["eof"]
    assert len(stream.requests) == (2 if partial else 1) and not stream.closed


@pytest.mark.parametrize(
    "kind,code",
    [
        ("interactive", "interactive"),
        ("missing", "unavailable"),
        ("text", "unavailable"),
        ("closed", "unavailable"),
    ],
)
def test_unavailable_stdin_is_not_read(no_provider, monkeypatch, capsys, kind, code):
    stream = {
        "interactive": SimpleNamespace(
            isatty=lambda: True, buffer=SimpleNamespace(read=forbidden)
        ),
        "missing": None,
        "text": io.StringIO("secret"),
        "closed": SimpleNamespace(
            isatty=lambda: False, buffer=SimpleNamespace(read=forbidden, closed=True)
        ),
    }[kind]
    monkeypatch.setattr(cli.sys, "stdin", stream)
    assert cli.main(arguments("start-progress")) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["code"] == "issue_observation_input_" + code
    assert payload["input_observation"] == reader.input_observation()


@pytest.mark.parametrize("cause_type", [KeyboardInterrupt, SystemExit])
def test_codec_interruption_keeps_complete_raw_hash_and_resets_selection(
    monkeypatch, cause_type
):
    cause = cause_type("private-codec-interruption")

    def interrupted(*args):
        raise cause

    monkeypatch.setattr(reader, "decode_issue_result", interrupted)
    body = json.dumps(frame()).encode()
    with pytest.raises(reader.ObservationInputError) as caught:
        reader.read_issue_guard(input_stream(body), issue_ref=ISSUE, actor_ref=ACTOR)
    assert caught.value.original_cause is cause and caught.value.interruption
    assert (
        caught.value.observation["source_sha256"]
        == "sha256:" + hashlib.sha256(body).hexdigest()
    )
    assert caught.value.observation["eof"]
    assert not caught.value.observation["result_validation_complete"]
    assert caught.value.observation["selected_issue_guard"] is None


@pytest.mark.parametrize("interrupted", [False, True])
def test_reporting_failure_does_not_change_interruption_or_retry(
    no_provider, monkeypatch, interrupted
):
    stream = BoundedStream(
        b"", error=KeyboardInterrupt("private") if interrupted else OSError("private")
    )
    monkeypatch.setattr(cli.sys, "stdin", stream)
    writes = []

    def failed_write(body):
        writes.append(body)
        raise OSError("report unavailable")

    monkeypatch.setattr(
        cli.sys, "stdout", SimpleNamespace(write=failed_write, flush=lambda: None)
    )
    assert cli.main(arguments("start-progress")) == (130 if interrupted else 3)
    assert len(writes) == 1 and len(stream.requests) == 1
    assert "private" not in writes[0]


@pytest.mark.parametrize(
    "command,interrupted",
    [
        ("bind-scope", False),
        ("start-progress", False),
        ("publish-close", False),
        ("start-progress", True),
    ],
)
def test_buffered_reporting_failure_preserves_real_process_exit(command, interrupted):
    # Deliberately use the interpreter's buffered stdout, not -u or a mock write.
    program = """
import sys
from types import SimpleNamespace
from aware_issue_cli import main as cli
reads = []
def forbidden(*args, **kwargs):
    raise AssertionError('provider acquisition forbidden')
cli.FilesystemIssueOperationProvider = forbidden
cli.IssueSdkOperationClient = forbidden
cli.create_repository_client = forbidden
def read_once(size):
    reads.append(size)
    assert len(reads) == 1, 'input retried'
    if sys.argv[1] == 'interrupted':
        raise KeyboardInterrupt('private interruption')
    return b''
sys.stdin = SimpleNamespace(isatty=lambda:False, buffer=SimpleNamespace(read=read_once))
result = cli.main(sys.argv[2:])
assert len(reads) == 1
raise SystemExit(result)
"""
    environment = os.environ.copy()
    environment.pop("PYTHONUNBUFFERED", None)
    argv = [
        sys.executable,
        "-B",
        "-c",
        program,
        "interrupted" if interrupted else "ordinary",
        *arguments(command),
    ]
    normal = subprocess.run(
        argv, capture_output=True, env=environment, check=False, timeout=15
    )
    assert normal.returncode == (130 if interrupted else 2), normal.stderr
    payload = json.loads(normal.stdout)
    assert payload["provider_invoked"] is False and payload["effect"] == "none"
    assert not payload["authorizes_retry"] and not normal.stderr
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        failed = subprocess.run(
            argv,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
            timeout=15,
        )
    finally:
        os.close(write_fd)
    assert failed.returncode == (130 if interrupted else 3), failed.stderr
    assert not failed.stderr


@pytest.mark.parametrize("interrupted", [False, True])
@pytest.mark.parametrize("close_interrupted", [False, True])
def test_failed_buffer_is_retired_without_resending_or_hiding_cleanup(
    monkeypatch, interrupted, close_interrupted
):
    writes = []
    closes = []
    output_failure = BrokenPipeError("private output failure")
    close_failure = KeyboardInterrupt("private retirement failure")

    class Raw(io.RawIOBase):
        def writable(self):
            return True

        def write(self, body):
            self._checkClosed()
            writes.append(bytes(body))
            raise output_failure

        def close(self):
            closes.append(True)
            super().close()
            if close_interrupted:
                raise close_failure

    raw = Raw()
    output = io.TextIOWrapper(io.BufferedWriter(raw), encoding="utf-8")
    monkeypatch.setattr(cli.sys, "stdout", output)
    monkeypatch.setattr(cli.sys, "__stdout__", output)
    error = reader.ObservationInputError(
        "issue_observation_input_interrupted" if interrupted else "invalid_json",
        reader.input_observation(),
        None,
    )
    args = SimpleNamespace(issue_ref=ISSUE)
    assert cli._report_observation_error(error, args, "start-progress") == (
        130 if interrupted else 3
    )
    assert cli.sys.stdout is None and cli.sys.__stdout__ is None
    assert raw.closed and len(closes) == 1
    assert len(writes) == 1 and b"private" not in writes[0]
    assert error.output_cause is output_failure
    assert error.output_retirement_cause is (
        close_failure if close_interrupted else None
    )
    with pytest.raises(ValueError):
        output.flush()
    assert len(writes) == len(closes) == 1


@pytest.mark.parametrize(
    "command,flag", [("bind-scope", "--scope-path"), ("publish-close", "--resolution")]
)
def test_typed_request_failure_is_not_relabelled_as_bad_input(
    no_provider, monkeypatch, capsys, command, flag
):
    seen = []
    original = cli.read_issue_guard

    def read(*args, **kwargs):
        selected = original(*args, **kwargs)
        seen.append(selected)
        return selected

    monkeypatch.setattr(cli, "read_issue_guard", read)
    monkeypatch.setattr(cli.sys, "stdin", input_stream(json.dumps(frame()).encode()))
    argv = arguments(command)
    argv[argv.index(flag) + 1] = ""
    assert cli.main(argv) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostics"] == ["request_invalid:IssueOperationContractError"]
    assert "input_observation" not in payload and "contract" not in payload
    assert seen[0][1]["result_validation_complete"]


def test_machine_error_escapes_coordinates_and_never_serializes_raw_body(
    no_provider, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.sys, "stdin", input_stream(b'{"PRIVATE-RAW-BODY":"secret"}')
    )
    argv = arguments("start-progress")
    argv[argv.index("--issue-ref") + 1] = "untrusted\x1b[31m\n$(not-a-command)"
    assert cli.main(argv) == 2
    output = capsys.readouterr()
    assert "PRIVATE-RAW-BODY" not in output.out and "secret" not in output.out
    assert "\x1b" not in output.out and not output.err
    assert json.loads(output.out)["issue_ref"] == argv[argv.index("--issue-ref") + 1]


def original_observation(root):
    client = IssueSdkOperationClient(
        provider=FilesystemIssueOperationProvider(repository_root=root)
    )
    result = client.resolve_read_projection(
        IssueReadProjectionResolveRequest(REAL_ISSUE)
    )
    assert result.outcome is IssueReadProjectionResolveOutcome.FOUND
    return json.dumps(result.to_wire()).encode()


def real_arguments(root, command):
    argv = arguments(command)
    for name, value in (
        ("--repository-root", str(root)),
        ("--issue-ref", REAL_ISSUE),
        ("--actor-ref", "codex-example"),
    ):
        argv[argv.index(name) + 1] = value
    return argv


@pytest.mark.parametrize("command", ["bind-scope", "start-progress"])
@pytest.mark.parametrize("stale", [False, True])
@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_genuine_provider_receives_same_guard_and_retains_stale_refusal(
    tmp_path, monkeypatch, capsys, command, stale, format_name
):
    monkeypatch.setenv("CODEX_THREAD_ID", "example")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = _repository(tmp_path)
    path = root / "docs/issues/2026/09/20/fb-2026-09-20-example.md"
    if command == "start-progress":
        path.write_text(
            path.read_text().replace("- Status: In Progress", "- Status: Open")
        )
    body = original_observation(root)
    if stale:
        path.write_text(path.read_text() + "\n- Explicit later change.\n")
    before = path.read_bytes()
    monkeypatch.setattr(cli.sys, "stdin", input_stream(body))
    argv = real_arguments(root, command)
    argv[argv.index("--format") + 1] = format_name
    assert cli.main(argv) == (2 if stale else 0)
    output = json.loads(capsys.readouterr().out)
    assert output["operation_ref"] == cli._ISSUE_OPERATION_REFS[command]
    assert (
        "input_observation" not in output
        and output.get("contract") != "aware.issue.observation-input-error.v1"
    )
    if stale:
        assert output["outcome"] == "stale"
        assert path.read_bytes() == before
    else:
        assert output["outcome"] in {"applied", "idempotent"}


@pytest.mark.parametrize("format_name", ["json", "summary"])
def test_genuine_preview_then_changed_head_and_bytes_still_plans_afresh(
    composed, monkeypatch, capsys, format_name
):
    import subprocess

    root, source, _, _, repository_client, _ = composed
    monkeypatch.setattr(
        cli, "create_repository_client", lambda **kwargs: repository_client
    )
    body = original_observation(root)
    argv = publication_arguments(composed, format_name=format_name)
    position = argv.index("--expected-issue-source-sha256")
    del argv[position : position + 2]
    argv.append("--issue-observation-from-stdin")
    monkeypatch.setattr(cli.sys, "stdin", input_stream(body))
    before = source.read_bytes()
    assert cli.main([*argv, "--dry-run"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["outcome"] == "planned" and len(preview["receipts"]) == 1
    assert source.read_bytes() == before

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()

    # Controlled fixture commit, not repository governance or automatic retry.
    (root / "independent.txt").write_text("independent intervening HEAD\n")
    git("add", "independent.txt")
    git("commit", "-m", "Independent change after preview")
    changed_head = git("rev-parse", "HEAD")
    (root / "src/example.py").write_text("fresh apply source bytes\n")
    assert source.read_bytes() == before  # Same Issue observation and explicit request.
    monkeypatch.setattr(cli.sys, "stdin", input_stream(body))
    assert cli.main(argv) == 0
    applied = json.loads(capsys.readouterr().out)
    assert len(applied["receipts"]) == 2 and applied["outcome"] == "completed"
    assert git("rev-list", "--count", changed_head + "..HEAD") == "2"
    assert git("show", "HEAD:src/example.py") == "fresh apply source bytes"
    assert "- Status: Closed" in source.read_text()


@pytest.mark.parametrize("command", ["bind-scope", "start-progress", "publish-close"])
def test_original_registrar_mount_uses_same_input_without_context_authority(
    monkeypatch, capsys, command
):
    from test_registrars import invoke_mounted

    monkeypatch.setattr(cli.sys, "stdin", input_stream(b"{}"))
    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", forbidden)
    assert (
        invoke_mounted(
            arguments(command), context={"actor_ref": ACTOR, "authorizes_retry": True}
        )
        == 2
    )
    mounted = capsys.readouterr().out
    monkeypatch.setattr(cli.sys, "stdin", input_stream(b"{}"))
    assert cli.main(arguments(command)) == 2
    assert capsys.readouterr().out == mounted


@pytest.mark.parametrize("cause_type", [OSError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("partial", [False, True])
def test_cli_read_failures_keep_exit_and_partial_observation(
    no_provider, monkeypatch, capsys, cause_type, partial
):
    stream = BoundedStream(
        b"private input", error=cause_type("PRIVATE"), partial=partial
    )
    monkeypatch.setattr(cli.sys, "stdin", stream)
    assert cli.main(arguments("start-progress")) == (
        2 if cause_type is OSError else 130
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["input_observation"]["byte_count"] == (7 if partial else 0)
    assert payload["input_observation"]["source_sha256"] is None
    assert not payload["provider_invoked"] and not payload["authorizes_retry"]


@pytest.mark.parametrize("kind", ["array", "nodes", "string", "depth"])
def test_generic_structure_boundaries_match_accepted_limits(kind):
    if kind == "array":
        good, bad = [None] * 4096, [None] * 4097
    elif kind == "nodes":
        good = {str(i): None for i in range(4095)}
        good["0"] = [None]  # root + 4095 keys/values + one child = 8192
        bad = dict(good, **{"0": [None, None]})
    elif kind == "string":
        good, bad = "é" * 131072, "é" * 131072 + "x"
    else:
        good = 0
        for _ in range(32):
            good = [good]
        bad = [good]
    reader._structure(good)
    with pytest.raises(ValueError, match="structure_limit"):
        reader._structure(bad)


def test_codec_refusal_keeps_original_exception_private(monkeypatch):
    cause = ValueError("PRIVATE-CODEC-DETAIL")

    def refuse(*args):
        raise cause

    monkeypatch.setattr(reader, "decode_issue_result", refuse)
    with pytest.raises(reader.ObservationInputError) as caught:
        reader.read_issue_guard(
            input_stream(json.dumps(frame()).encode()), issue_ref=ISSUE, actor_ref=ACTOR
        )
    assert caught.value.original_cause is cause
    assert caught.value.code == "issue_observation_input_invalid_result"
    assert (
        caught.value.observation["eof"]
        and not caught.value.observation["result_validation_complete"]
    )


def test_postdispatch_exception_cannot_be_mislabelled_as_input_not_invoked(
    monkeypatch, capsys
):
    error = reader.ObservationInputError(
        "issue_observation_input_unavailable",
        reader.input_observation(),
        OSError("test"),
    )
    called = []

    def provider(**kwargs):
        called.append(True)
        raise error

    monkeypatch.setattr(cli, "FilesystemIssueOperationProvider", provider)
    monkeypatch.setattr(cli.sys, "stdin", input_stream(json.dumps(frame()).encode()))
    assert cli.main(arguments("start-progress")) == 2
    payload = json.loads(capsys.readouterr().out)
    assert called == [True]
    assert "provider_invoked" not in payload and "input_observation" not in payload
    assert payload["diagnostics"] == ["request_invalid:ObservationInputError"]


@pytest.mark.parametrize("status", ["Open", "In Progress", "Blocked", "Closed"])
def test_input_selection_does_not_become_a_lifecycle_admission(status):
    value = frame(status=status)
    guard, observation = reader.read_issue_guard(
        input_stream(json.dumps(value).encode()), issue_ref=ISSUE, actor_ref=ACTOR
    )
    assert guard == value["projection"]["source"]["digest"]
    assert observation["result_validation_complete"]


@pytest.mark.parametrize(
    "outcome", ["absent", "malformed", "unsupported_profile", "authority_unavailable"]
)
def test_typed_nonfound_outcome_remains_in_private_refusal_evidence(outcome):
    value = frame()
    value.update(outcome=outcome, projection=None)
    with pytest.raises(reader.ObservationInputError) as caught:
        reader.read_issue_guard(
            input_stream(json.dumps(value).encode()), issue_ref=ISSUE, actor_ref=ACTOR
        )
    assert caught.value.observed_outcome == outcome
    assert caught.value.code == "issue_observation_input_not_found"
    assert caught.value.observation["selected_issue_guard"] is None
