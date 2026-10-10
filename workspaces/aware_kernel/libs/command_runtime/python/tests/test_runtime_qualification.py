"""Neutral dispatch proofs; no SDK binding or domain admission is implied."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import aware_command_runtime
import pytest
from aware_command_runtime import (
    AwareCommandRegistry,
    AwareCommandSpec,
    CommandRegistrationError,
    build_parser,
    dispatch_command,
    run_cli,
)


def registry_for(name="observe", *, handle=lambda invocation: 0):
    registry = AwareCommandRegistry()
    registry.register_command(name=name, help="Read explicitly.", handle=handle)
    return registry


@pytest.mark.parametrize("name", ["", " ", "two words", "two\twords", "two\nwords"])
def test_invalid_names_refuse_before_registration(name):
    registry = AwareCommandRegistry()
    with pytest.raises(CommandRegistrationError):
        registry.register_command(name=name, help="Invalid", handle=lambda value: 0)
    assert registry.names() == ()


def test_normalized_duplicate_preserves_original():
    registry = registry_for()
    original = registry.require("observe")
    with pytest.raises(CommandRegistrationError, match="already registered"):
        registry.register_command(
            name=" observe ", help="Replacement", handle=lambda value: 9
        )
    assert registry.require("observe") is original


def test_merge_does_not_implicitly_replace():
    registry = registry_for()
    original = registry.require("observe")
    with pytest.raises(CommandRegistrationError, match="already registered"):
        registry.merge(registry_for())
    assert registry.require("observe") is original


def test_explicit_replacement_preserves_all_projection_fields():
    registry = registry_for()
    spec = AwareCommandSpec(
        name=" observe ",
        help="New",
        configure_parser=lambda parser: None,
        handle=lambda invocation: 8,
        source="explicit",
        description="Description",
        operation_ref="sdk.operation",
        projection_ref="sdk.surface",
        hidden=True,
    )
    registry.register(spec, replace=True)
    normalized = registry.require("observe")
    assert normalized.name == "observe"
    for field in (
        "help",
        "configure_parser",
        "handle",
        "source",
        "description",
        "operation_ref",
        "projection_ref",
        "hidden",
    ):
        assert getattr(normalized, field) == getattr(spec, field)
    assert run_cli(registry, prog="neutral", argv=["observe"]) == 8


@pytest.mark.parametrize("argv", [[], ["missing"], ["observe", "--unknown"]])
def test_parser_refusals_do_not_invoke_handler(argv, capsys):
    calls = []
    registry = registry_for(handle=lambda invocation: calls.append(invocation))
    with pytest.raises(SystemExit) as raised:
        run_cli(registry, prog="neutral", argv=argv)
    assert raised.value.code == 2
    assert calls == []
    assert capsys.readouterr().err


def test_handler_exception_is_not_reinterpreted_as_success():
    error = RuntimeError("owner refusal")

    def handle(invocation):
        raise error

    with pytest.raises(RuntimeError) as raised:
        run_cli(registry_for(handle=handle), prog="neutral", argv=["observe"])
    assert raised.value is error


def test_missing_dispatch_selection_does_not_select_a_command(capsys):
    calls = []
    registry = registry_for(handle=lambda invocation: calls.append(invocation))
    assert (
        dispatch_command(
            registry,
            args=argparse.Namespace(),
            parser=build_parser(registry, prog="neutral"),
            argv=(),
        )
        == 2
    )
    assert calls == []
    assert "usage:" in capsys.readouterr().out


def test_unknown_dispatch_selection_refuses():
    registry = registry_for()
    with pytest.raises(CommandRegistrationError, match="Unknown command"):
        dispatch_command(
            registry,
            args=argparse.Namespace(_aware_command_name="missing"),
            parser=build_parser(registry, prog="neutral"),
            argv=(),
        )


def test_configuration_is_eager_but_handlers_are_selected_only():
    configured, invoked = [], []
    registry = AwareCommandRegistry()
    for name in ("observe", "optional"):
        registry.register_command(
            name=name,
            help=name,
            configure_parser=lambda parser, name=name: configured.append(name),
            handle=lambda invocation: invoked.append(invocation.command.name),
        )
    assert run_cli(registry, prog="neutral", argv=["observe"]) == 0
    assert configured == ["observe", "optional"]
    assert invoked == ["observe"]


def test_runtime_imports_are_standard_library_or_same_package():
    root = Path(aware_command_runtime.__file__).parent
    for source in root.glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                imports = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [(node.module or "").split(".")[0]]
            else:
                continue
            assert set(imports) <= sys.stdlib_module_names | {"aware_command_runtime"}
