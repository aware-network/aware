"""Read registration and source parity; not installed-candidate qualification."""

import builtins
import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import tomllib
import types
from pathlib import Path

import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    CommandRegistrationError,
    build_parser,
    run_cli,
)
from aware_specification_cli.main import main
from aware_specification_cli.read_commands import register_read_commands
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_sdk import (
    SPECIFICATION_OBSERVE_OPERATION_REF,
    SpecificationSdkClient,
)
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[9]
_spec = importlib.util.spec_from_file_location(
    "spec_registrar_real_fixtures", Path(__file__).with_name("test_protocol_cli.py")
)
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
canonical_tree = _fixtures.canonical_tree
selected = _fixtures.selected
fixtures = _fixtures._fixtures


@pytest.fixture(scope="module")
def predecessor():
    path = (
        "workspaces/aware_kernel/modules/specification/sdks/specification/python/"
        "cli/aware_specification_cli/main.py"
    )
    body = subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(ROOT), "show", "b0ed337b1d94:" + path]
    )
    assert hashlib.sha256(body).hexdigest() == (
        "d15d075ae45e528687b3b0b6895738a7c6345dfd52c8876cb3185eff140181bb"
    )
    module = types.ModuleType("spec_read_predecessor_source_only")
    # Explicit test oracle from pinned source, never operational CLI substitution.
    exec(compile(body, "<pinned SPEC read predecessor>", "exec"), module.__dict__)  # noqa: S102 - hash-verified committed test oracle only
    return module.main


def arguments(base, command):
    args = [command, *_fixtures.arguments(base)]
    if command == "iteration-identity":
        args += ["--iteration-ref", fixtures.ITERATION]
    return args


def capture(call, args, capsys):
    try:
        code = call(args)
        assert type(code) is int
    except SystemExit as error:
        code = error.code
    streams = capsys.readouterr()
    return code, streams.out, streams.err


def test_registration_is_effect_free_and_has_exact_canonical_labels(monkeypatch):
    def prohibited(*args, **kwargs):
        pytest.fail("registration performed IO, provider admission or an operation")

    registry = AwareCommandRegistry()
    with monkeypatch.context() as patch:
        patch.setattr(os, "open", prohibited)
        patch.setattr(Path, "read_bytes", prohibited)
        patch.setattr(Path, "read_text", prohibited)
        patch.setattr(SpecificationFsSdkProvider, "from_protocol_selection", prohibited)
        patch.setattr(SpecificationSdkClient, "observe", prohibited)
        register_read_commands(registry)
        build_parser(registry, prog="aware-spec")
    assert registry.names() == ("observe", "iteration-identity")
    for command in registry:
        assert command.operation_ref == SPECIFICATION_OBSERVE_OPERATION_REF
        assert command.source == "aware_specification_cli"
        assert command.projection_ref is None


def test_duplicate_registration_refuses_without_replacing_first():
    registry = AwareCommandRegistry()
    register_read_commands(registry)
    original = tuple(registry)
    with pytest.raises(CommandRegistrationError, match="already registered"):
        register_read_commands(registry)
    assert tuple(registry) == original


def test_foreign_registration_is_preserved_and_no_writer_is_mounted():
    registry = AwareCommandRegistry()
    registry.register_command(
        name="foreign", help="Foreign command", handle=lambda _: 9
    )
    original = registry.require("foreign")
    register_read_commands(registry)
    assert registry.require("foreign") is original
    assert registry.get("create-draft") is None
    assert registry.get("spec") is None
    assert run_cli(registry, argv=["foreign"], prog="test") == 9


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
@pytest.mark.parametrize(
    "scenario",
    [
        "success",
        "source-stale",
        "manifest-stale",
        "projection",
        "malformed",
        "provider-cleanup",
        "protocol-cleanup",
    ],
)
def test_raw_source_predecessor_successor_requests_streams_and_exits_match(
    selected, predecessor, capsys, monkeypatch, command, scenario
):
    base, _ = selected
    args = arguments(base, command)
    if scenario == "source-stale":
        args += ["--expected-source-digest", "sha256:" + "b" * 64]
    elif scenario == "manifest-stale":
        args += ["--expected-manifest-sha256", "sha256:" + "a" * 64]
    elif scenario == "projection":
        (base / "aware.protocol.toml").write_bytes(
            fixtures.protocol_bytes("projection")
        )
    elif scenario == "malformed":
        original = SpecificationFsSdkProvider.observe

        def observe(provider, request):
            original(provider, request)

        monkeypatch.setattr(SpecificationFsSdkProvider, "observe", observe)
    elif scenario == "provider-cleanup":
        original = SpecificationFsSdkProvider.close

        def close(provider):
            original(provider)
            raise OSError("fault after actual provider closure")

        monkeypatch.setattr(SpecificationFsSdkProvider, "close", close)
    elif scenario == "protocol-cleanup":
        protocol = importlib.import_module("aware_protocol_fs_adapter")
        original = protocol.release_specification_selection

        def release(selection):
            original(selection)
            raise OSError("fault after original issuer release")

        monkeypatch.setattr(protocol, "release_specification_selection", release)

    requests = []
    original_observe = SpecificationSdkClient.observe

    def sdk_observe(client, request):
        requests.append(request)
        return original_observe(client, request)

    monkeypatch.setattr(SpecificationSdkClient, "observe", sdk_observe)
    before = fixtures.bodies(base)
    descriptors = set(os.listdir("/proc/self/fd"))
    expected = capture(predecessor, args, capsys)
    split = len(requests)
    observed = capture(main, args, capsys)
    assert observed[0] == expected[0]
    assert observed[2] == expected[2]
    before_output = json.loads(expected[1])
    after_output = json.loads(observed[1])
    if "diagnostics" not in before_output and "diagnostics" in after_output:
        diagnostics = after_output.pop("diagnostics")
        assert scenario in {"manifest-stale", "projection"}
        assert diagnostics == [before_output["error"]]
    assert after_output == before_output
    assert requests[:split] == requests[split:]
    assert observed[0] == (0 if scenario == "success" else 2)
    assert fixtures.bodies(base) == before
    assert set(os.listdir("/proc/self/fd")) == descriptors


def read_mount(argv):
    registry = AwareCommandRegistry()
    register_read_commands(registry)
    return run_cli(registry, argv=argv, prog="aware-spec")


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["unknown"],
        ["create-draft"],
        ["observe"],
        ["iteration-identity"],
        ["observe", "--source-base", "/raw", "--root", "specs/example"],
        [
            "observe",
            "--repository-root",
            "/missing",
            "--spec-manifest",
            "x",
            "--unknown",
        ],
    ],
)
def test_read_mount_parser_refusal_parity(predecessor, capsys, args):
    assert capture(read_mount, args, capsys) == capture(predecessor, args, capsys)


@pytest.mark.parametrize(
    "args,description",
    [
        (["--help"], "Observe explicitly selected Specification sources."),
        (["observe", "--help"], "Observe explicitly selected Specification sources."),
        (
            ["iteration-identity", "--help"],
            "Resolve an existing iteration from a fresh observation.",
        ),
    ],
)
def test_only_declared_help_description_changes(predecessor, capsys, args, description):
    old = capture(predecessor, args, capsys)
    new = capture(read_mount, args, capsys)
    assert old[0] == new[0] == 0
    assert old[2] == new[2] == ""
    assert description in new[1]
    assert new[1] != old[1]
    assert "create-draft" not in new[1]


def test_missing_optional_protocol_integration_refuses_without_raw_fallback(
    selected, capsys, monkeypatch
):
    base, _ = selected
    original = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name == "aware_protocol_fs_adapter":
            raise ImportError("fault: optional integration absent")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", unavailable)
    assert main(arguments(base, "observe")) == 2
    assert json.loads(capsys.readouterr().out) == {
        "error": "protocol_integration_unavailable",
        "effect": "none",
    }


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
def test_composed_reader_does_not_import_governed_owners(
    selected, capsys, monkeypatch, command
):
    base, _ = selected
    original_import = builtins.__import__
    original_module = importlib.import_module
    blocked = (
        "aware_issue_sdk",
        "aware_issue_fs_adapter",
        "aware_file_system.retained_package",
        "aware_specification_fs_sdk_adapter.governed_draft",
        "aware_protocol_fs_adapter.specification_draft_target",
    )

    def check(name):
        if any(name == prefix or name.startswith(prefix + ".") for prefix in blocked):
            pytest.fail("read command loaded optional governed owner: " + name)

    def import_value(name, *args, **kwargs):
        check(name)
        return original_import(name, *args, **kwargs)

    def import_module(name, *args, **kwargs):
        check(name)
        return original_module(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_value)
    monkeypatch.setattr(importlib, "import_module", import_module)
    assert main(arguments(base, command)) == 0
    assert json.loads(capsys.readouterr().out)["retained_capability_exported"] is False


def test_generic_invocation_context_cannot_substitute_for_explicit_sources(
    selected, capsys
):
    base, _ = selected
    registry = AwareCommandRegistry()
    register_read_commands(registry)
    args = arguments(base, "observe")
    expected = capture(main, args, capsys)
    context = {"repository_root": "/unadmitted", "provider": object(), "actor": "fake"}
    assert (
        capture(
            lambda argv: run_cli(
                registry, argv=argv, prog="aware-spec", context=context
            ),
            args,
            capsys,
        )
        == expected
    )


@pytest.mark.parametrize("command", ["observe", "iteration-identity"])
def test_interrupt_propagation_and_cleanup_match_predecessor(
    selected, predecessor, capsys, monkeypatch, command
):
    base, _ = selected
    original = SpecificationFsSdkProvider.observe

    def interrupted(provider, request):
        original(provider, request)
        raise KeyboardInterrupt("fault after actual observation")

    monkeypatch.setattr(SpecificationFsSdkProvider, "observe", interrupted)
    before = fixtures.bodies(base)
    descriptors = set(os.listdir("/proc/self/fd"))
    for entry in (predecessor, main):
        with pytest.raises(KeyboardInterrupt, match="actual observation"):
            entry(arguments(base, command))
        streams = capsys.readouterr()
        assert streams.out == streams.err == ""
        assert fixtures.bodies(base) == before
        assert set(os.listdir("/proc/self/fd")) == descriptors


def test_source_metadata_has_only_agreed_neutral_consumer_edges():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert project["project"]["version"] == "0.4.2"
    assert project["project"]["dependencies"] == [
        "aware-specification-sdk>=0.3.1,<0.4.0",
        "aware-specification-fs-sdk-adapter[protocol]>=0.4.1,<0.5.0",
        "aware-command-runtime>=0.1.1,<0.2.0",
    ]
    assert project["project"]["scripts"] == {
        "aware-spec": "aware_specification_cli.main:main"
    }
    assert project["project"]["optional-dependencies"] == {
        "governed": ["aware-specification-fs-sdk-adapter[governed]>=0.4.1,<0.5.0"]
    }
    assert project["tool"]["uv"]["sources"]["aware-command-runtime"] == {
        "workspace": True
    }


@pytest.mark.parametrize(
    "version,admitted",
    [
        ("0.2.2", False),
        ("0.3.0rc1", False),
        ("0.3.0", False),
        ("0.3.9", False),
        ("0.4.0rc1", False),
        ("0.4.0", False),
        ("0.4.1", True),
        ("0.4.9", True),
        ("0.5.0", False),
    ],
)
def test_successor_admits_only_agreed_adapter_generation(version, admitted):
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    adapter = Requirement(project["project"]["dependencies"][1])
    assert adapter.extras == {"protocol"}
    assert adapter.specifier.contains(version) is admitted


@pytest.mark.parametrize("syntax", ["create-draft", "compatibility-writer", "spec"])
def test_console_target_refuses_writer_without_compatibility_or_provider_fallback(
    selected, capsys, monkeypatch, syntax
):
    base, _ = selected
    module = importlib.import_module("aware_specification_cli.main")
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    target_module, target_name = project["project"]["scripts"]["aware-spec"].split(":")
    assert target_module == module.__name__
    entry = getattr(module, target_name)

    def forbidden(*args, **kwargs):
        pytest.fail("unsupported writer reached compatibility or provider authority")

    monkeypatch.setattr(module, "compatibility_main", forbidden)
    monkeypatch.setattr(SpecificationSdkClient, "create_draft", forbidden)
    monkeypatch.setattr(
        SpecificationFsSdkProvider, "from_protocol_selection", forbidden
    )
    before = fixtures.bodies(base)
    descriptors = set(os.listdir("/proc/self/fd"))
    code, out, err = capture(
        entry,
        [syntax, "--source-base", str(base), "--root", "new-draft"],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert ("required" if syntax == "create-draft" else "invalid choice") in err
    assert fixtures.bodies(base) == before
    assert not (base / "new-draft").exists()
    assert set(os.listdir("/proc/self/fd")) == descriptors
