"""One neutral entrance; existing family registrars own every leaf operation."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Mapping, Sequence

from aware_command_runtime import AwareCommandRegistry, run_cli

# Interface mounting only. Package membership belongs to portable_protocols.
_REGISTRARS = {
    "issue": ("aware_issue_cli.main", ("register_issue_commands",)),
    "protocol": (
        "aware_protocol_cli.main",
        ("register_admit_command", "register_setup_specification_command"),
    ),
    "spec": (
        "aware_specification_cli.read_commands",
        ("register_read_commands",),
    ),
}


def register_family_commands(registry: AwareCommandRegistry, family: str) -> None:
    """Import only the explicit family; use public registrar ports unchanged."""
    module_name, names = _REGISTRARS[family]
    module = importlib.import_module(module_name)
    for name in names:
        registrar = getattr(module, name)
        if not callable(registrar):
            raise ImportError(  # noqa: TRY004 - incompatible supplier export, not caller input.
                f"Required registrar unavailable: {module_name}.{name}"
            )
        registrar(registry)
    if family == "spec":
        draft = importlib.import_module("aware_specification_cli.draft_commands")
        registrar = draft.register_draft_commands
        if not callable(registrar):
            raise ImportError("Required SPEC draft registrar unavailable")
        registrar(registry)


def run_family(
    family: str,
    argv: Sequence[str],
    *,
    context: Mapping[str, object] | None = None,
) -> int:
    """Retain original leaf argv and generic transport context, never authority."""
    registry = AwareCommandRegistry()
    try:
        register_family_commands(registry, family)
    except (ImportError, AttributeError) as error:
        print(
            json.dumps(
                {
                    "error": "family_registrar_unavailable",
                    "family": family,
                    "detail": str(error),
                    "effect": "none",
                    "operation_invoked": False,
                    "next_action": "Install the qualified complete Agent CLI candidate; do not substitute another environment or provider.",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    # Owner exceptions/results remain owner evidence. Never catch them above.
    return run_cli(registry, argv=argv, prog="aware " + family, context=context)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="aware",
        description=(
            "Use neutral Issue, Protocol and Specification operations through "
            "their canonical SDKs. Run aware FAMILY --help for exact leaf inputs."
        ),
        epilog=(
            "Initialization previews by default; creation and effects require "
            "explicit intent. No Agent sessions, approval or Service fallback."
        ),
    )
    parser.add_argument("family", choices=(*_REGISTRARS, "init"))
    selected = parser.parse_args(arguments[:1])
    if selected.family == "init":
        from .initialization import register_init_command

        registry = AwareCommandRegistry()
        register_init_command(registry)
        return run_cli(registry, argv=arguments, prog="aware")
    return run_family(selected.family, arguments[1:])
