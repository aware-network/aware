"""Mounted command specs for workspace-operator owned aware-cli commands."""

from __future__ import annotations


def get_command_specs() -> list[dict[str, object]]:
    return [
        {
            "name": "commit",
            "module": "aware_workspace_operator.cli.commit_command",
            "register": "register_commit_parser",
            "handle": "handle_commit_command",
            "help": "Canonical issue-scoped commit rail.",
            "pass_parser": False,
            "source": "workspace-operator-pack",
        },
        {
            "name": "module",
            "module": "aware_workspace_operator.cli.module_command",
            "register": "register_module_parser",
            "handle": "handle_module_command",
            "help": "Workspace-owned module lifecycle helpers.",
            "pass_parser": True,
            "source": "workspace-operator-pack",
        },
    ]


__all__ = ["get_command_specs"]
