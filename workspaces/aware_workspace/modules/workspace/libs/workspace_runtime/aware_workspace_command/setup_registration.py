"""Setup-only registration for a host's original neutral command registry.

The host supplies the registry and owns its family mounting and Issue admission.
This registrar changes neither global command-pack discovery nor provider choice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry


def register_workspace_setup_commands(registry: AwareCommandRegistry) -> None:
    """Mount only setup; parser configuration and dispatch stay with Workspace."""
    from .architecture_setup_command import configure_workspace_setup_parser

    registry.register_command(
        name="setup",
        help="Create Aware architecture and align authored Python packages.",
        configure_parser=configure_workspace_setup_parser,
        handle=_handle_setup,
        source="workspace-setup",
    )


def _handle_setup(invocation: AwareCommandInvocation) -> int:
    from .architecture_setup_command import handle_workspace_setup_command

    return handle_workspace_setup_command(invocation.args)


__all__ = ["register_workspace_setup_commands"]
