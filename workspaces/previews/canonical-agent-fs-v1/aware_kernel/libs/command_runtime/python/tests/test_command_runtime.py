from __future__ import annotations

import pytest

from aware_command_runtime import (
    AwareCommandInvocation,
    AwareCommandRegistry,
    CommandRegistrationError,
    run_cli,
)


def test_public_and_local_registrars_compose_without_public_importing_local() -> None:
    calls: list[tuple[str, str | None]] = []

    def register_public_commands(registry: AwareCommandRegistry) -> None:
        def handle(invocation: AwareCommandInvocation) -> int:
            calls.append((invocation.command.source, invocation.command.operation_ref))
            return 0

        registry.register_command(
            name="status",
            help="Show public status.",
            handle=handle,
            source="aware-example-sdk.public",
            operation_ref="aware-example-sdk.status",
            projection_ref="aware-example-sdk.cli.status",
        )

    def register_local_commands(registry: AwareCommandRegistry) -> None:
        def configure(parser) -> None:
            parser.add_argument("--socket-path", default=None)

        def handle(invocation: AwareCommandInvocation) -> int:
            calls.append((invocation.command.source, invocation.args.socket_path))
            return 0

        registry.register_command(
            name="service",
            help="Manage local service transport.",
            configure_parser=configure,
            handle=handle,
            source="aware-example-sdk.local",
        )

    registry = AwareCommandRegistry()
    registry.extend(register_public_commands)
    registry.extend(register_local_commands)

    assert run_cli(registry, argv=["status"], prog="aware-example") == 0
    assert (
        run_cli(
            registry,
            argv=["service", "--socket-path", "/tmp/example.sock"],
            prog="aware-example",
        )
        == 0
    )

    assert calls == [
        ("aware-example-sdk.public", "aware-example-sdk.status"),
        ("aware-example-sdk.local", "/tmp/example.sock"),
    ]


def test_duplicate_registration_fails_closed() -> None:
    registry = AwareCommandRegistry()
    registry.register_command(
        name="status",
        help="Show status.",
        handle=lambda invocation: 0,
        source="public",
    )

    with pytest.raises(CommandRegistrationError, match="already registered"):
        registry.register_command(
            name="status",
            help="Show local status.",
            handle=lambda invocation: 0,
            source="local",
        )


def test_duplicate_registration_requires_explicit_replace() -> None:
    registry = AwareCommandRegistry()
    calls: list[str] = []
    registry.register_command(
        name="status",
        help="Show status.",
        handle=lambda invocation: calls.append("public") or 0,
        source="public",
    )
    registry.register_command(
        name="status",
        help="Show local status.",
        handle=lambda invocation: calls.append("local") or 0,
        source="local",
        replace=True,
    )

    assert run_cli(registry, argv=["status"], prog="aware-example") == 0
    assert calls == ["local"]


def test_invocation_passes_context_and_argv() -> None:
    registry = AwareCommandRegistry()
    seen: dict[str, object] = {}

    def configure(parser) -> None:
        parser.add_argument("--name", required=True)

    def handle(invocation: AwareCommandInvocation) -> int:
        seen["name"] = invocation.args.name
        seen["argv"] = invocation.argv
        seen["context"] = invocation.context
        return 7

    registry.register_command(
        name="hello",
        help="Say hello.",
        configure_parser=configure,
        handle=handle,
        source="test",
    )

    exit_code = run_cli(
        registry,
        argv=["hello", "--name", "Ada"],
        prog="aware-example",
        context={"actor": "tester"},
    )

    assert exit_code == 7
    assert seen == {
        "name": "Ada",
        "argv": ("hello", "--name", "Ada"),
        "context": {"actor": "tester"},
    }


def test_command_names_are_single_tokens() -> None:
    registry = AwareCommandRegistry()

    with pytest.raises(CommandRegistrationError, match="one argparse token"):
        registry.register_command(
            name="workspace status",
            help="Invalid nested command.",
            handle=lambda invocation: 0,
        )
