"""One-command composition proofs; real provider policy remains its owner."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys

import pytest
from aware_command_runtime import AwareCommandRegistry, CommandRegistrationError
from aware_protocol_sdk import (
    PROTOCOL_ADMIT_TARGET_OPERATION_REF,
    ProtocolSdkClient,
    ProtocolTargetAdmissionRequest,
)

cli = importlib.import_module("aware_protocol_cli.main")


def test_only_admit_is_registered_to_the_existing_sdk_operation():
    registry = AwareCommandRegistry()
    cli.register_admit_command(registry)
    assert registry.names() == ("admit",)
    spec = registry.require("admit")
    assert spec.operation_ref == PROTOCOL_ADMIT_TARGET_OPERATION_REF
    assert spec.source == "aware_protocol_cli"
    assert spec.projection_ref is None
    with pytest.raises(CommandRegistrationError, match="already registered"):
        cli.register_admit_command(registry)


@pytest.mark.parametrize("authority", ["filesystem", "service_api"])
def test_dispatch_preserves_typed_request_text_and_real_provider_result(
    monkeypatch, tmp_path, capsys, authority
):
    captured = []
    native_client = ProtocolSdkClient

    class RecordingClient:
        def __init__(self, *, provider):
            assert type(provider) is cli.FilesystemProtocolSdkProvider
            self.client = native_client(provider)

        def admit_target(self, request):
            assert type(request) is ProtocolTargetAdmissionRequest
            captured.append(request)
            return self.client.admit_target(request)

    monkeypatch.setattr(cli, "ProtocolSdkClient", RecordingClient)
    target = str(tmp_path / "missing" / "..")
    source = "nested/../aware.protocol.toml"
    assert (
        cli.main(
            [
                "admit",
                "--repository-root",
                target,
                "--manifest-path",
                source,
                "--authority-mode",
                authority,
            ]
        )
        == 2
    )
    output = capsys.readouterr()
    assert output.err == ""
    (request,) = captured
    assert request.target_ref == target
    assert request.source_ref == source
    assert request.authority_mode.value == authority
    actual = json.loads(output.out)
    expected = (
        native_client(cli.FilesystemProtocolSdkProvider())
        .admit_target(request)
        .to_wire()
    )
    assert {k: v for k, v in actual.items() if k != "interface"} == expected


@pytest.mark.parametrize("command", ["version", "setup-specification"])
def test_siblings_do_not_dispatch_through_admit(monkeypatch, capsys, command):
    def forbidden(*args, **kwargs):
        raise AssertionError("sibling must not use admit dispatch")

    monkeypatch.setattr(cli, "dispatch_command", forbidden)
    if command == "version":
        assert cli.main([command]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == "ok"
    else:
        with pytest.raises(SystemExit) as error:
            cli.main([command])
        assert error.value.code == 2


def test_unexpected_provider_failure_keeps_original_stderr_boundary(
    monkeypatch, capsys
):
    class FailingClient:
        def __init__(self, *, provider):
            pass

        def admit_target(self, request):
            raise OSError("explicit provider failure")

    monkeypatch.setattr(cli, "ProtocolSdkClient", FailingClient)
    assert cli.main(["admit", "--repository-root", "/explicit-target"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "status": "error",
        "operation_ref": PROTOCOL_ADMIT_TARGET_OPERATION_REF,
        "error_type": "OSError",
        "message": "explicit provider failure",
    }


@pytest.mark.parametrize("command", ["admit", "version", "setup-specification"])
def test_all_parser_commands_remain_available(command):
    registry = AwareCommandRegistry()
    cli.register_admit_command(registry)
    parser = cli._parser(registry)
    sub = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert set(sub.choices) == {"admit", "version", "setup-specification"}
    if command == "admit":
        args = parser.parse_args([command, "--repository-root", "unchanged"])
        assert args._aware_command_name == "admit"


def test_read_help_version_do_not_import_optional_issue_setup():
    # Source diagnostic only; installed parity uses actual console scripts.
    code = (
        "import sys; from aware_protocol_cli.main import main; "
        "main(['version']); "
        "assert 'aware_protocol_cli.specification_setup' not in sys.modules; "
        "assert not any(n.startswith('aware_issue') for n in sys.modules)"
    )
    run = subprocess.run(
        [sys.executable, "-c", code], text=True, capture_output=True, check=False
    )
    assert run.returncode == 0, run.stderr
