from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
import sys


ParserConfigurator = Callable[[argparse.ArgumentParser], None]
CommandHandler = Callable[["AwareCommandInvocation"], int | None]


class CommandRegistrationError(ValueError):
    """Raised when command registration would create an ambiguous CLI surface."""


@dataclass(frozen=True, slots=True)
class AwareCommandSpec:
    """One command mounted into an Aware CLI surface."""

    name: str
    help: str
    configure_parser: ParserConfigurator
    handle: CommandHandler
    source: str = "unknown"
    description: str | None = None
    operation_ref: str | None = None
    projection_ref: str | None = None
    hidden: bool = False


@dataclass(frozen=True, slots=True)
class AwareCommandInvocation:
    """Runtime invocation object passed to command handlers."""

    command: AwareCommandSpec
    args: argparse.Namespace
    parser: argparse.ArgumentParser
    argv: tuple[str, ...]
    context: Mapping[str, object] | None = None


class AwareCommandRegistry:
    """Function-based command registry for composable SDK CLIs."""

    def __init__(self) -> None:
        self._commands: dict[str, AwareCommandSpec] = {}

    def register(self, spec: AwareCommandSpec, *, replace: bool = False) -> None:
        command_name = _normalize_command_name(spec.name)
        if command_name != spec.name:
            spec = AwareCommandSpec(
                name=command_name,
                help=spec.help,
                configure_parser=spec.configure_parser,
                handle=spec.handle,
                source=spec.source,
                description=spec.description,
                operation_ref=spec.operation_ref,
                projection_ref=spec.projection_ref,
                hidden=spec.hidden,
            )
        if command_name in self._commands and not replace:
            existing = self._commands[command_name]
            raise CommandRegistrationError(
                "Command "
                f"{command_name!r} is already registered by {existing.source!r}; "
                "pass replace=True only for an intentional launcher-level override."
            )
        self._commands[command_name] = spec

    def register_command(
        self,
        *,
        name: str,
        help: str,
        configure_parser: ParserConfigurator | None = None,
        handle: CommandHandler,
        source: str = "unknown",
        description: str | None = None,
        operation_ref: str | None = None,
        projection_ref: str | None = None,
        hidden: bool = False,
        replace: bool = False,
    ) -> None:
        self.register(
            AwareCommandSpec(
                name=name,
                help=help,
                configure_parser=configure_parser or _noop_configure_parser,
                handle=handle,
                source=source,
                description=description,
                operation_ref=operation_ref,
                projection_ref=projection_ref,
                hidden=hidden,
            ),
            replace=replace,
        )

    def extend(self, registrar: Callable[["AwareCommandRegistry"], None]) -> None:
        registrar(self)

    def merge(self, other: "AwareCommandRegistry", *, replace: bool = False) -> None:
        for spec in other:
            self.register(spec, replace=replace)

    def get(self, name: str) -> AwareCommandSpec | None:
        return self._commands.get(_normalize_command_name(name))

    def require(self, name: str) -> AwareCommandSpec:
        spec = self.get(name)
        if spec is None:
            raise CommandRegistrationError(f"Unknown command: {name!r}")
        return spec

    def names(self) -> tuple[str, ...]:
        return tuple(self._commands)

    def __iter__(self) -> Iterator[AwareCommandSpec]:
        return iter(self._commands.values())

    def __len__(self) -> int:
        return len(self._commands)


def build_parser(
    registry: AwareCommandRegistry,
    *,
    prog: str,
    description: str | None = None,
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for spec in registry:
        command_parser = subparsers.add_parser(
            spec.name,
            help=argparse.SUPPRESS if spec.hidden else spec.help,
            description=spec.description or spec.help,
        )
        spec.configure_parser(command_parser)
        command_parser.set_defaults(_aware_command_name=spec.name)
    return parser


def dispatch_command(
    registry: AwareCommandRegistry,
    *,
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    argv: Iterable[str],
    context: Mapping[str, object] | None = None,
) -> int:
    command_name = str(getattr(args, "_aware_command_name", "") or "")
    if not command_name:
        parser.print_help()
        return 2
    spec = registry.require(command_name)
    result = spec.handle(
        AwareCommandInvocation(
            command=spec,
            args=args,
            parser=parser,
            argv=tuple(str(item) for item in argv),
            context=context,
        )
    )
    return 0 if result is None else int(result)


def run_cli(
    registry: AwareCommandRegistry,
    *,
    argv: Iterable[str] | None = None,
    prog: str,
    description: str | None = None,
    context: Mapping[str, object] | None = None,
) -> int:
    args_list = tuple(str(item) for item in (sys.argv[1:] if argv is None else argv))
    parser = build_parser(registry, prog=prog, description=description)
    args = parser.parse_args(args_list)
    return dispatch_command(
        registry,
        args=args,
        parser=parser,
        argv=args_list,
        context=context,
    )


def _normalize_command_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise CommandRegistrationError("Command name must not be empty.")
    if any(character.isspace() for character in normalized):
        raise CommandRegistrationError(
            f"Command name must be one argparse token, got {name!r}."
        )
    return normalized


def _noop_configure_parser(parser: argparse.ArgumentParser) -> None:
    del parser
