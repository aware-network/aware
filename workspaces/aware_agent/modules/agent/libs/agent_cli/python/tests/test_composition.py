"""Namespace and dependency proofs, not installed or domain admission claims."""

from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from aware_command_runtime import AwareCommandRegistry
from packaging.requirements import Requirement

client = importlib.import_module("aware_agent_cli.main")


@pytest.mark.parametrize("argv", [[], ["unknown"], ["repository", "create"]])
def test_unqualified_root_commands_refuse_before_family_import(
    argv, monkeypatch, capsys
):
    def forbidden(*args, **kwargs):
        pytest.fail("root syntax selected an operation or fallback")

    monkeypatch.setattr(client, "register_family_commands", forbidden)
    with pytest.raises(SystemExit) as error:
        client.main(argv)
    assert error.value.code == 2
    assert capsys.readouterr().out == ""


def test_root_help_does_not_import_families_or_service():
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class RejectDomain(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_issue', 'aware_protocol', 'aware_specification',
                                'aware_workspace', 'aware_agent_sdk', 'aware_agent.')):
            raise AssertionError('root help imported domain: ' + fullname)
sys.meta_path.insert(0, RejectDomain())
from aware_agent_cli.main import main
try:
    main(['--help'])
except SystemExit as error:
    assert error.code == 0
else:
    raise AssertionError('help did not stop')
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "issue,protocol,spec,workspace" in result.stdout
    assert "does not establish Issue enforcement" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize("family", ["issue", "protocol", "spec", "workspace"])
def test_leaf_identity_argv_context_and_owner_return_are_preserved(family, monkeypatch):
    calls = []
    context = {"not_authority": object()}

    def handle(invocation):
        calls.append(invocation)
        return 7

    def registrar(registry, selected):
        assert selected == family
        registry.register_command(
            name="probe",
            help="Transport-only test probe.",
            handle=handle,
            configure_parser=lambda parser: parser.add_argument("--value"),
        )

    monkeypatch.setattr(client, "register_family_commands", registrar)
    argv = ["probe", "--value", "literal/path"]
    assert client.run_family(family, argv, context=context) == 7
    assert client.main([family, *argv]) == 7
    for invocation in calls:
        assert invocation.args.command == invocation.args._aware_command_name == "probe"
        assert invocation.argv == tuple(argv)
        assert invocation.args.value == "literal/path"
        assert invocation.command.handle is handle
    assert calls[0].context is context
    assert calls[1].context is None


@pytest.mark.parametrize("family", ["issue", "protocol", "spec", "workspace"])
@pytest.mark.parametrize("failure", ["import", "export", "not_callable"])
def test_missing_supplier_refuses_before_dispatch(family, failure, monkeypatch, capsys):
    def unavailable(name):
        if failure == "import":
            raise ImportError("missing qualified supplier")
        if failure == "export":
            return SimpleNamespace()
        names = [
            "register_issue_commands",
            "register_admit_command",
            "register_setup_specification_command",
            "register_read_commands",
            "register_workspace_setup_commands",
        ]
        return SimpleNamespace(**dict.fromkeys(names, None))

    monkeypatch.setattr(client.importlib, "import_module", unavailable)
    monkeypatch.setattr(
        client, "run_cli", lambda *a, **k: pytest.fail("fallback dispatch")
    )
    assert client.main([family, "anything"]) == 2
    streams = capsys.readouterr()
    assert streams.out == ""
    result = json.loads(streams.err)
    assert result["error"] == "family_registrar_unavailable"
    assert result["effect"] == "none"
    assert result["operation_invoked"] is False


def test_missing_draft_port_does_not_dispatch_partially_registered_spec(
    monkeypatch, capsys
):
    original = client.importlib.import_module

    def imports(name):
        if name == "aware_specification_cli.draft_commands":
            raise ImportError("required draft supplier unavailable")
        return original(name)

    monkeypatch.setattr(client.importlib, "import_module", imports)
    monkeypatch.setattr(
        client, "run_cli", lambda *a, **k: pytest.fail("partial dispatch")
    )
    assert client.main(["spec", "observe"]) == 2
    assert json.loads(capsys.readouterr().err)["operation_invoked"] is False


@pytest.mark.parametrize("family", ["issue", "protocol", "spec", "workspace"])
def test_handler_failures_and_interruptions_are_not_reinterpreted(family, monkeypatch):
    def registrar(registry, selected):
        registry.register_command(name="probe", help="Unit probe", handle=handle)

    monkeypatch.setattr(client, "register_family_commands", registrar)
    for error in (
        ValueError("owner refusal"),
        ImportError("owner invocation error"),
        KeyboardInterrupt(),
    ):

        def handle(invocation, exception=error):
            raise exception

        with pytest.raises(type(error)) as caught:
            client.main([family, "probe"])
        assert caught.value is error


@pytest.mark.parametrize("family", ["issue", "protocol", "spec", "workspace"])
def test_original_public_handler_identities_are_mounted(family):
    actual = AwareCommandRegistry()
    client.register_family_commands(actual, family)
    expected = AwareCommandRegistry()
    if family == "issue":
        from aware_issue_cli.main import register_issue_commands

        register_issue_commands(expected)
    elif family == "protocol":
        from aware_protocol_cli.main import (
            register_admit_command,
            register_setup_specification_command,
        )

        register_admit_command(expected)
        register_setup_specification_command(expected)
    elif family == "workspace":
        from aware_workspace_command.setup_registration import (
            register_workspace_setup_commands,
        )

        register_workspace_setup_commands(expected)
        from aware_agent_cli.workspace_review import register_workspace_review_command

        register_workspace_review_command(expected)
    else:
        from aware_specification_cli.draft_commands import register_draft_commands
        from aware_specification_cli.read_commands import register_read_commands

        register_read_commands(expected)
        register_draft_commands(expected)
        from aware_agent_cli.draft_preparation import register_draft_preparation_command

        register_draft_preparation_command(expected)
    assert actual.names() == expected.names()
    for a, e in zip(actual, expected, strict=True):
        assert a.handle is e.handle
        assert (a.name, a.operation_ref, a.projection_ref) == (
            e.name,
            e.operation_ref,
            e.projection_ref,
        )


def _assert_owned_metadata(project):
    assert project["project"]["name"] == "aware-agent-cli"
    assert project["project"]["version"] == "0.2.0a7"
    assert project["project"]["scripts"] == {"aware": "aware_agent_cli.main:main"}
    dependencies = [Requirement(raw) for raw in project["project"]["dependencies"]]
    assert {r.name for r in dependencies} == {
        "aware-command-runtime",
        "aware-issue-cli",
        "aware-protocol-cli",
        "aware-specification-cli",
        "aware-workspace-sdk",
        "aware-workspace-runtime",
        "aware-issue-sdk",
        "aware-issue-fs-adapter",
        "aware-protocol-sdk",
        "aware-protocol-fs-adapter",
        "aware-protocol-runtime",
        "aware-specification-sdk",
        "aware-specification-fs-sdk-adapter",
        "aware-specification-runtime",
    }
    assert next(r for r in dependencies if r.name == "aware-protocol-cli").extras == {
        "specification-setup",
        "bootstrap",
    }
    assert next(
        r for r in dependencies if r.name == "aware-specification-cli"
    ).extras == {
        "governed",
    }
    # A1 admission is a neutral extra, not permission to add a Service rail.
    expected = (
        "aware-command-runtime>=0.1.1,<0.2.0",
        "aware-issue-cli>=0.8.0,<0.9.0",
        "aware-protocol-cli[bootstrap,specification-setup]>=0.3.5,<0.4.0",
        "aware-workspace-sdk[preparation,setup,setup_admission,setup_review]>=0.2.10,<0.3.0",
        "aware-workspace-runtime[setup_admission,setup_review]>=0.2.15,<0.3.0",
        "aware-specification-cli[governed]>=0.4.3,<0.5.0",
        "aware-issue-sdk[workspace_setup_admission]>=0.10.6,<0.11.0",
        "aware-issue-fs-adapter>=0.9.6,<0.10.0",
        "aware-protocol-sdk>=0.3.2,<0.4.0",
        "aware-protocol-fs-adapter>=0.6.5,<0.7.0",
        "aware-protocol-runtime>=0.1.1,<0.2.0",
        "aware-specification-sdk>=0.3.3,<0.4.0",
        "aware-specification-fs-sdk-adapter[governed]>=0.4.3,<0.5.0",
        "aware-specification-runtime>=0.1.0,<0.2.0",
    )
    assert len(dependencies) == len(expected)
    assert {str(r) for r in dependencies} == {str(Requirement(r)) for r in expected}
    assert all(r.marker is None and r.url is None for r in dependencies)
    assert all(any(s.operator == ">=" for s in r.specifier) for r in dependencies)
    assert all(any(s.operator == "<" for s in r.specifier) for r in dependencies)


def test_owned_metadata_is_finite_neutral_and_explicit():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    _assert_owned_metadata(project)


@pytest.mark.parametrize(
    "change",
    (
        "version",
        "entrypoint",
        "sdk-extra",
        "runtime-extra",
        "issue-extra",
        "sdk-floor",
        "runtime-floor",
        "issue-floor",
        "sdk-ceiling",
        "service",
        "marker",
        "direct-url",
    ),
)
def test_owned_metadata_rejects_stale_or_widened_candidate_contract(change):
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    altered = copy.deepcopy(project)
    metadata = altered["project"]
    if change == "version":
        metadata["version"] = "0.2.0a5"
    elif change == "entrypoint":
        metadata["scripts"] = {"aware": "other_rail:main"}
    elif change == "service":
        metadata["dependencies"].append("aware-local-service>=0.1.0,<0.2.0")
    else:
        name, before, after = {
            "sdk-extra": ("aware-workspace-sdk", ",setup_admission", ""),
            "runtime-extra": (
                "aware-workspace-runtime",
                "[setup_admission,setup_review]",
                "",
            ),
            "issue-extra": (
                "aware-issue-sdk",
                "[workspace_setup_admission]",
                "",
            ),
            "sdk-floor": ("aware-workspace-sdk", ">=0.2.10", ">=0.2.9"),
            "runtime-floor": ("aware-workspace-runtime", ">=0.2.15", ">=0.2.14"),
            "issue-floor": ("aware-issue-sdk", ">=0.10.6", ">=0.10.5"),
            "sdk-ceiling": ("aware-workspace-sdk", "<0.3.0", "<0.4.0"),
            "marker": (
                "aware-workspace-sdk",
                "<0.3.0",
                '<0.3.0; python_version < "3.12"',
            ),
            "direct-url": (
                "aware-workspace-sdk",
                "[preparation,setup,setup_admission,setup_review]>=0.2.10,<0.3.0",
                " @ file:///unqualified-test-only.whl",
            ),
        }[change]
        dependencies = metadata["dependencies"]
        index = next(
            i for i, raw in enumerate(dependencies) if Requirement(raw).name == name
        )
        assert dependencies[index].count(before) == 1
        dependencies[index] = dependencies[index].replace(before, after)
    with pytest.raises(AssertionError):
        _assert_owned_metadata(altered)
