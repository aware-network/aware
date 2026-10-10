"""Command-pack metadata owned by the neutral Workspace runtime."""

from __future__ import annotations


def get_command_specs() -> dict[str, dict[str, object]]:
    return {
        "workspace": {
            "name": "workspace",
            "module": "aware_workspace_command.workspace_command",
            "register": "register_workspace_parser",
            "handle": "handle_workspace_command",
            "help": "Workspace materialization and optional product helpers.",
            "pass_parser": True,
            "source": "workspace-runtime-pack",
        }
    }


__all__ = ["get_command_specs"]
