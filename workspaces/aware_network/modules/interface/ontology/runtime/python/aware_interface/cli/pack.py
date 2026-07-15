"""Interface runtime aware-cli command-pack metadata."""

from __future__ import annotations


def get_command_specs() -> dict[str, dict[str, object]]:
    return {
        "session": {
            "name": "session",
            "module": "aware_interface.cli.session_command",
            "register": "register_session_parser",
            "handle": "handle_session_command",
            "help": "Agent/session bootstrap helpers.",
            "pass_parser": True,
            "source": "interface-pack",
        },
    }


__all__ = ["get_command_specs"]
