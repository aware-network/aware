"""Original registrar/SDK/reader proofs; no operation replay or installation."""

import builtins
import hashlib
import importlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
)
from aware_file_system import confined_mutation as physical
from aware_specification_cli import receipt_commands as command
from aware_specification_cli.main import main
from aware_specification_cli.read_commands import register_read_commands
from aware_specification_fs_sdk_adapter import SpecificationFsSavedReceiptProvider
from aware_specification_sdk import (
    SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE,
    SPECIFICATION_SAVED_RECEIPT_OPERATION_REF,
    SpecificationSavedReceiptClient,
    SpecificationSdkClient,
)


def capture(**changes):
    packet = {
        "effect": "none",
        "consumer_completion_verified": False,
        "retained_capability_exported": False,
        "cleanup_evidence": None,
        "input_custody": None,
        "caller_cleanup": {},
        "cleanup_diagnostics": [],
        "protocol_owner_completion": "unknown",
        "error": "historical_refusal",
    }
    packet.update(changes)
    return json.dumps(packet, indent=2).encode()


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def arguments(root, body, view=None, source="receipt.json"):
    result = [
        "present-receipt",
        "--receipt-base",
        str(root),
        "--receipt",
        source,
        "--expected-receipt-sha256",
        digest(body),
        "--input-profile",
        SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE,
    ]
    if view is not None:
        result += ["--format", view]
    return result


def forbidden(*_args, **_kwargs):
    pytest.fail("presentation entered an operation, fallback or repeated reader")


@pytest.mark.parametrize("view", [None, "summary", "full"])
@pytest.mark.parametrize("ending", [b"", b"\n", b" \n\n"])
def test_actual_reader_once_exact_bytes_and_flags(
    tmp_path, monkeypatch, capsysbinary, view, ending
):
    body = capture() + ending
    source = tmp_path / "receipt.json"
    source.write_bytes(body)
    original = physical.observe_confined_file_with_cleanup
    calls = []

    def read(*, root, path, maximum_bytes):
        calls.append((root, path, maximum_bytes))
        return original(root=root, path=path, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    monkeypatch.setattr(SpecificationSdkClient, "create_draft", forbidden)
    monkeypatch.chdir("/")
    before = set(os.listdir("/proc/self/fd"))
    assert main(arguments(tmp_path, body, view)) == 0
    streams = capsysbinary.readouterr()
    assert streams.err == b""
    assert len(calls) == 1
    assert source.read_bytes() == body
    assert set(os.listdir("/proc/self/fd")) == before
    if view == "full":
        assert streams.out == body
    else:
        summary = json.loads(streams.out)
        assert summary["record"] == json.loads(body)
        assert summary["source"]["source_sha256"] == digest(body)
        assert summary["source"]["cleanup"]["closed_count"] == 2
        assert summary["capture_grade"] == "captured_transport_not_authenticated"
        assert summary["currentness"] == "not_revalidated"
        assert summary["operation_invoked"] is False
        assert summary["authority_restored"] is False
        assert summary["authorizes_retry"] is False
        assert summary["full_capture_omitted"] is True
        assert "full_body_hex" not in summary
        access = summary["full_access"]
        assert access["availability"] == "guarded_source_read"
        assert access["standalone_argv"] == [
            "aware-spec",
            *arguments(tmp_path, body, "full"),
        ]
        assert access["agent_argv"] == [
            "aware",
            "spec",
            *arguments(tmp_path, body, "full"),
        ]
        # The real full-access arguments retrieve the same guarded capture.
        assert main(access["standalone_argv"][1:]) == 0
        assert capsysbinary.readouterr().out == body
        assert len(calls) == 2  # Two explicit read commands, not an SDK retry.


@pytest.mark.parametrize("view", ["summary", "full"])
def test_untouched_accepted_recovery_capture_in_both_cli_views(
    capsysbinary, monkeypatch, view
):
    coordinate = os.environ.get("AWARE_SAVED_RECEIPT_ACCEPTED_R_CAPTURE")
    assert coordinate, "Replay requires the explicit accepted frozen R capture."
    path = Path(coordinate)
    body = path.read_bytes()
    assert len(body) == 121484
    assert digest(body) == (
        "sha256:5b82f485682523d9afd8aa105dd0f7da7a5a66d7ec21de7b1fcd10a2ecc33007"
    )
    monkeypatch.setattr(SpecificationSdkClient, "create_draft", forbidden)
    assert main(arguments(path.parent, body, view, source=path.name)) == 0
    streams = capsysbinary.readouterr()
    assert streams.err == b""
    if view == "full":
        assert streams.out == body
    else:
        summary = json.loads(streams.out)
        assert len(streams.out) < len(body)
        assert summary["record"]["effect"] == json.loads(body)["effect"]
        assert summary["record"]["protocol_owner_completion"] == "completed"
        assert summary["omissions"]
        assert all(
            omission["availability"] == "guarded_source_read"
            for omission in summary["omissions"]
        )
        assert "full_body_hex" not in summary


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize(
    "kind", ["missing", "stale", "invalid-json", "invalid-omitted", "symlink", "fifo"]
)
def test_real_source_refusals_are_lossless_and_never_retry(
    tmp_path, monkeypatch, capsysbinary, kind, view
):
    body = capture()
    source = tmp_path / "receipt.json"
    if kind == "stale":
        source.write_bytes(body + b" ")
    elif kind == "invalid-json":
        body = b"not-json"
        source.write_bytes(body)
    elif kind == "invalid-omitted":
        body = capture(members=[{"path": "x", "bytes": 1, "sha256": "invalid"}])
        source.write_bytes(body)
    elif kind == "symlink":
        target = tmp_path / "other"
        target.write_bytes(body)
        source.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(source)
    calls = []
    original = physical.observe_confined_file_with_cleanup

    def read(*, root, path, maximum_bytes):
        calls.append((root, path, maximum_bytes))
        return original(root=root, path=path, maximum_bytes=maximum_bytes)

    monkeypatch.setattr(physical, "observe_confined_file_with_cleanup", read)
    before = set(os.listdir("/proc/self/fd"))
    assert main(arguments(tmp_path, body, view)) == 2
    streams = capsysbinary.readouterr()
    assert streams.err == b""
    evidence = json.loads(streams.out)
    assert evidence["provider_invoked"] is True
    assert evidence["cleanup"] == "closed"
    assert evidence["evidence_grade"] == "provider_observation"
    assert evidence["request"]["expected_source_sha256"] == digest(body)
    assert evidence["operation_invoked"] is False
    assert evidence["authorizes_retry"] is False
    assert "full_access" not in evidence
    if kind == "stale":
        assert evidence["observed_source"]["source_sha256"] == digest(body + b" ")
    assert len(calls) == 1
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize(
    "flag,value",
    [
        ("--receipt-base", "relative"),
        ("--receipt", "../receipt.json"),
        ("--receipt", "/receipt.json"),
        ("--receipt", "bad\ud800"),
        ("--expected-receipt-sha256", "semantic-digest"),
    ],
)
def test_invalid_request_is_local_not_observed(
    tmp_path, monkeypatch, capsysbinary, flag, value
):
    argv = arguments(tmp_path, capture())
    argv[argv.index(flag) + 1] = value
    monkeypatch.setattr(
        SpecificationFsSavedReceiptProvider, "present_draft_receipt", forbidden
    )
    assert main(argv) == 2
    evidence = json.loads(capsysbinary.readouterr().out)
    assert evidence["error"] == "receipt_request_invalid"
    assert evidence["provider_invoked"] is False
    assert evidence["cleanup"] == "not_acquired"
    assert evidence["effect"] == "none"
    assert evidence["evidence_grade"] == "local_not_observed"


@pytest.mark.parametrize(
    "missing",
    ["--receipt-base", "--receipt", "--expected-receipt-sha256", "--input-profile"],
)
def test_parser_requires_explicit_coordinates_guard_and_profile(
    tmp_path, monkeypatch, capsysbinary, missing
):
    argv = arguments(tmp_path, capture())
    index = argv.index(missing)
    del argv[index : index + 2]
    monkeypatch.setattr(
        SpecificationFsSavedReceiptProvider, "present_draft_receipt", forbidden
    )
    with pytest.raises(SystemExit) as caught:
        main(argv)
    assert caught.value.code == 2
    streams = capsysbinary.readouterr()
    assert streams.out == b""
    assert missing.encode() in streams.err


def test_effect_free_registration_help_and_collision(tmp_path, monkeypatch, capsys):
    registry = AwareCommandRegistry()
    with monkeypatch.context() as patch:
        patch.setattr(os, "open", forbidden)
        patch.setattr(
            SpecificationSavedReceiptClient, "present_draft_receipt", forbidden
        )
        command.register_receipt_commands(registry)
        build_parser(registry, prog="aware-spec")
        with pytest.raises(SystemExit) as caught:
            main(["present-receipt", "--help"])
        assert caught.value.code == 0
    text = " ".join(capsys.readouterr().out.split())
    assert "exact saved receipt bytes" in text
    assert "no operation replay" in text
    assert "without an added newline" in text
    assert "--apply" not in text
    original = registry.require("present-receipt")
    assert original.operation_ref == SPECIFICATION_SAVED_RECEIPT_OPERATION_REF
    with pytest.raises(CommandRegistrationError):
        command.register_receipt_commands(registry)
    assert registry.require("present-receipt") is original
    with pytest.raises(CommandRegistrationError):
        register_read_commands(registry)
    assert registry.require("present-receipt") is original


def test_missing_optional_reader_does_not_open_source(
    tmp_path, monkeypatch, capsysbinary
):
    original = importlib.import_module

    def unavailable(name, *args, **kwargs):
        if name == "aware_file_system.confined_mutation":
            raise ImportError("original optional reader unavailable")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", unavailable)
    owner = importlib.import_module("aware_specification_fs_sdk_adapter.saved_receipt")
    monkeypatch.setattr(owner, "import_module", unavailable)
    monkeypatch.setattr(os, "open", forbidden)
    assert main(arguments(tmp_path, capture())) == 2
    evidence = json.loads(capsysbinary.readouterr().out)
    assert evidence["error"] == "receipt_reader_integration_unavailable"
    assert evidence["cleanup"] == "not_acquired"
    assert "reader_not_invoked" in evidence["diagnostics"]


@pytest.mark.parametrize(
    "fault", ["malformed", "foreign", "interrupt", "malformed-error"]
)
def test_sdk_rejected_provider_reports_remain_unvalidated(
    tmp_path, monkeypatch, capsysbinary, fault
):
    from aware_specification_sdk import SpecificationSavedReceiptError

    calls = []
    original = SpecificationFsSavedReceiptProvider.present_draft_receipt
    (tmp_path / "receipt.json").write_bytes(capture())

    def provider(self, request):
        calls.append(request)
        if fault == "interrupt":
            raise KeyboardInterrupt("original provider interruption")
        if fault == "malformed-error":
            error = SpecificationSavedReceiptError.__new__(
                SpecificationSavedReceiptError
            )
            ValueError.__init__(error, "missing original carrier")
            raise error
        result = original(self, request)
        if fault == "malformed":
            return {"foreign_report": "retained"}
        object.__setattr__(
            result, "request", replace(request, source_ref="foreign.json")
        )
        return result

    monkeypatch.setattr(
        SpecificationFsSavedReceiptProvider, "present_draft_receipt", provider
    )
    assert main(arguments(tmp_path, capture())) == 2
    evidence = json.loads(capsysbinary.readouterr().out)
    assert evidence["evidence_grade"] == "unvalidated_provider_report"
    assert evidence["cleanup"] == "unknown"
    assert evidence["effect"] == "unknown"
    assert evidence["observed_source"] is None
    assert evidence["authorizes_retry"] is False
    assert len(calls) == 1
    assert evidence["cause_kinds"]
    if fault == "interrupt":
        assert "KeyboardInterrupt" in evidence["cause_kinds"]
    if fault == "malformed":
        assert evidence["reported_result"] == {"foreign_report": "retained"}


@pytest.mark.parametrize("view", ["summary", "full"])
def test_unknown_close_retains_read_evidence_without_reclose(
    tmp_path, monkeypatch, capsysbinary, view
):
    body = capture()
    (tmp_path / "receipt.json").write_bytes(body)
    close = physical.os.close
    calls = []

    def uncertain(fd):
        calls.append(fd)
        close(fd)
        if len(calls) == 1:
            raise OSError("original ambiguous close after effect")

    before = set(os.listdir("/proc/self/fd"))
    monkeypatch.setattr(physical.os, "close", uncertain)
    assert main(arguments(tmp_path, body, view)) == 2
    evidence = json.loads(capsysbinary.readouterr().out)
    assert evidence["cleanup"] == "unknown"
    assert evidence["observed_source"]["source_sha256"] == digest(body)
    assert evidence["evidence_grade"] == "provider_observation"
    assert "SpecificationSavedReceiptError" in evidence["cause_kinds"]
    assert len(calls) == len(set(calls)) == 2
    assert "full_access" not in evidence
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize("fault", ["short", "broken", "interrupt"])
def test_output_failure_preserves_verified_source_and_never_retries(
    tmp_path, monkeypatch, capsysbinary, view, fault
):
    body = capture()
    (tmp_path / "receipt.json").write_bytes(body)
    calls = []

    def write(value):
        calls.append(value)
        if fault == "short":
            return len(value) - 1
        if fault == "broken":
            raise BrokenPipeError("output unavailable")
        raise KeyboardInterrupt("interrupted output")

    stream = SimpleNamespace(write=write, flush=forbidden)
    stdout = SimpleNamespace(buffer=stream, write=write, flush=forbidden)
    before = set(os.listdir("/proc/self/fd"))
    with monkeypatch.context() as patch:
        patch.setattr(command.sys, "stdout", stdout)
        assert main(arguments(tmp_path, body, view)) == 2
    evidence = json.loads(capsysbinary.readouterr().err)
    assert evidence["error"] == "receipt_output_failed"
    assert evidence["output_completion"] == "unknown"
    assert evidence["validated_source"]["source_sha256"] == digest(body)
    assert evidence["validated_source"]["cleanup"]["outcome"] == "closed"
    assert evidence["operation_invoked"] is False
    assert evidence["authorizes_retry"] is False
    assert len(calls) == 1
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("entrance", ["standalone", "agent"])
@pytest.mark.parametrize("view", ["summary", "full"])
def test_real_source_subprocess_mounts_original_registrar(tmp_path, entrance, view):
    body = capture() + b"\n\n"
    (tmp_path / "receipt.json").write_bytes(body)
    module = (
        "aware_specification_cli.main"
        if entrance == "standalone"
        else "aware_agent_cli.main"
    )
    argv = arguments(tmp_path, body, view)
    if entrance == "agent":
        argv.insert(0, "spec")
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            f"import sys; from {module} import main; sys.exit(main(sys.argv[1:]))",
            *argv,
        ],
        cwd=tmp_path,
        env={"PYTHONPATH": os.environ["PYTHONPATH"], "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert process.returncode == 0, process.stderr
    assert process.stderr == b""
    if view == "full":
        assert process.stdout == body
    else:
        assert json.loads(process.stdout)["record"] == json.loads(body)
    assert (tmp_path / "receipt.json").read_bytes() == body


def test_existing_mutation_handler_and_console_target_remain_exact():
    root = Path(__file__).resolve().parents[1]
    assert hashlib.sha256(
        (root / "aware_specification_cli/draft_commands.py").read_bytes()
    ).hexdigest() == (
        "e4856e4537f39993417d7619bcac090684868323e3a703cc110bb6974b8be32c"
    )
    assert (
        "register_receipt_commands"
        not in (root / "aware_specification_cli/main.py").read_text()
    )
    assert (
        "aware_file_system"
        not in (root / "aware_specification_cli/receipt_commands.py").read_text()
    )


def test_registration_does_not_import_optional_physical_reader(monkeypatch):
    original = builtins.__import__

    def restricted(name, *args, **kwargs):
        if name == "aware_file_system" or name.startswith("aware_file_system."):
            pytest.fail("registration imported an optional physical owner")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", restricted)
    registry = AwareCommandRegistry()
    register_read_commands(registry)
    build_parser(registry, prog="aware-spec")
    assert (
        registry.require("present-receipt").operation_ref
        == SPECIFICATION_SAVED_RECEIPT_OPERATION_REF
    )


@pytest.mark.parametrize(
    "suffix",
    [["--apply"], ["--format", "brief"], ["--input-profile", "guessed-profile"]],
)
def test_unsupported_apply_format_or_profile_never_dispatches(
    tmp_path, capsysbinary, monkeypatch, suffix
):
    monkeypatch.setattr(
        SpecificationFsSavedReceiptProvider, "present_draft_receipt", forbidden
    )
    with pytest.raises(SystemExit) as result:
        main(arguments(tmp_path, capture()) + suffix)
    assert result.value.code == 2
    assert capsysbinary.readouterr().out == b""


def test_saved_full_access_refuses_source_drift_without_refresh(tmp_path, capsysbinary):
    root = tmp_path / "evidence with 'quotes' and $literal"
    root.mkdir()
    body = capture()
    path = root / "receipt.json"
    path.write_bytes(body)
    assert main(arguments(root, body)) == 0
    saved = json.loads(capsysbinary.readouterr().out)
    original_arguments = saved["full_access"]["standalone_argv"][1:]
    path.write_bytes(body + b"\n")
    assert main(original_arguments) == 2
    refusal = json.loads(capsysbinary.readouterr().out)
    assert refusal["request"]["expected_source_sha256"] == digest(body)
    assert refusal["observed_source"]["source_sha256"] == digest(body + b"\n")
    assert refusal["authorizes_retry"] is False
    assert path.read_bytes() == body + b"\n"


def test_fresh_receipt_registration_and_help_load_no_optional_owners():
    script = """
import importlib.abc, sys
class RejectOwners(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
            'aware_file_system', 'aware_issue_sdk', 'aware_issue_fs_adapter',
            'aware_protocol_fs_adapter'
        }:
            raise ImportError('registration_loaded_optional_owner:' + fullname)
sys.meta_path.insert(0, RejectOwners())
from aware_command_runtime import AwareCommandRegistry, build_parser
from aware_specification_cli.read_commands import register_read_commands
registry = AwareCommandRegistry()
register_read_commands(registry)
parser = build_parser(registry, prog='aware-spec')
try:
    parser.parse_args(['present-receipt', '--help'])
except SystemExit as result:
    assert result.code == 0
assert not any(name.startswith('aware_file_system') for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script],
        env={"PYTHONPATH": os.environ["PYTHONPATH"], "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    assert b"exact saved receipt bytes" in result.stdout


@pytest.mark.parametrize("entrance", ["standalone", "agent"])
@pytest.mark.parametrize("view", ["summary", "full"])
@pytest.mark.parametrize(
    "phase", ["success", "stale", "local", "malformed", "unknown-cleanup"]
)
def test_real_closed_stdout_preserves_refusals_and_terminal_exit(
    tmp_path, entrance, view, phase
):
    body = capture() + b"\n\n"
    source = tmp_path / "receipt.json"
    source.write_bytes(body)
    module = (
        "aware_specification_cli.main"
        if entrance == "standalone"
        else "aware_agent_cli.main"
    )
    script = f"""
import json, sys
from aware_file_system import confined_mutation as physical
from aware_specification_fs_sdk_adapter import SpecificationFsSavedReceiptProvider
from aware_specification_sdk import SpecificationSdkClient
from {module} import main
phase = sys.argv[1]
counts = {{'reader_calls': 0, 'provider_calls': 0, 'source_closes': 0}}
reading = False
read = physical.observe_confined_file_with_cleanup
close = physical.os.close
provider = SpecificationFsSavedReceiptProvider.present_draft_receipt
def observed_read(*, root, path, maximum_bytes):
    global reading
    counts['reader_calls'] += 1
    reading = True
    try:
        return read(root=root, path=path, maximum_bytes=maximum_bytes)
    finally:
        reading = False
def original_close(fd):
    close(fd)
    if reading:
        counts['source_closes'] += 1
        if phase == 'unknown-cleanup' and counts['source_closes'] == 1:
            raise OSError('uncertain original close after effect')
def observed_provider(self, request):
    counts['provider_calls'] += 1
    result = provider(self, request)
    return {{'original_foreign_report': 'retained'}} if phase == 'malformed' else result
def prohibited_operation(*args, **kwargs):
    raise AssertionError('presentation replayed draft operation')
physical.observe_confined_file_with_cleanup = observed_read
physical.os.close = original_close
SpecificationFsSavedReceiptProvider.present_draft_receipt = observed_provider
SpecificationSdkClient.create_draft = prohibited_operation
code = main(sys.argv[2:])
print(json.dumps({{'probe_counts': counts}}), file=sys.stderr, flush=True)
sys.exit(code)
"""
    argv = arguments(tmp_path, body, view)
    if phase == "stale":
        argv[argv.index("--expected-receipt-sha256") + 1] = "sha256:" + "0" * 64
    elif phase == "local":
        argv[argv.index("--receipt-base") + 1] = "relative"
    if entrance == "agent":
        argv.insert(0, "spec")
    invocation = [sys.executable, "-B", "-c", script, phase, *argv]
    environment = {
        "PYTHONPATH": os.environ["PYTHONPATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    baseline = subprocess.run(
        invocation,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        check=False,
        timeout=20,
    )
    assert baseline.returncode == (0 if phase == "success" else 2), baseline.stderr
    baseline_counts = json.loads(baseline.stderr)["probe_counts"]
    expected_counts = {
        "reader_calls": 0 if phase == "local" else 1,
        "provider_calls": 0 if phase == "local" else 1,
        "source_closes": 0 if phase == "local" else 2,
    }
    assert baseline_counts == expected_counts
    if phase == "success" and view == "full":
        assert baseline.stdout == body

    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    try:
        result = subprocess.run(
            invocation,
            stdout=write_fd,
            stderr=subprocess.PIPE,
            cwd=tmp_path,
            env=environment,
            check=False,
            timeout=20,
        )
    finally:
        os.close(write_fd)
    assert result.returncode == 2, result.stderr
    assert b"Exception ignored in:" not in result.stderr
    assert b"BrokenPipeError:" not in result.stderr
    failure, observation = [json.loads(line) for line in result.stderr.splitlines()]
    assert observation["probe_counts"] == expected_counts
    assert failure["output_error"] == "receipt_output_failed"
    assert failure["output_error_kind"] == "BrokenPipeError"
    assert failure["output_completion"] == "unknown"
    assert failure["output_retirement"] == "discard_sink_installed"
    assert failure["output_retirement_diagnostics"] == []
    assert failure["operation_invoked"] is False
    assert failure["authorizes_retry"] is False
    if phase == "success":
        assert failure["error"] == "receipt_output_failed"
        assert failure["validated_source"]["source_sha256"] == digest(body)
        assert failure["validated_source"]["cleanup"]["outcome"] == "closed"
    else:
        # All original refusal fields, including unvalidated reports/uncertain
        # cleanup, remain identical. Output failure is a separate carrier.
        original = json.loads(baseline.stdout)
        assert {key: failure[key] for key in original} == original
        if phase == "stale":
            assert failure["observed_source"]["source_sha256"] == digest(body)
            assert failure["request"]["expected_source_sha256"] == "sha256:" + "0" * 64
        elif phase == "local":
            assert failure["provider_invoked"] is False
            assert failure["cleanup"] == "not_acquired"
            assert failure["effect"] == "none"
        elif phase == "unknown-cleanup":
            assert failure["cleanup"] == "unknown"
            assert failure["observed_source"]["source_sha256"] == digest(body)
        else:
            assert failure["evidence_grade"] == "unvalidated_provider_report"
            assert failure["cleanup"] == failure["effect"] == "unknown"
            assert failure["reported_result"] == {"original_foreign_report": "retained"}
            assert failure["observed_source"] is None
    assert source.read_bytes() == body
