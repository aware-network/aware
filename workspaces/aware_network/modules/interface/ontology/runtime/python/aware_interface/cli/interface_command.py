"""Owner-mounted Interface CLI command implementation."""

from __future__ import annotations

import argparse
from typing import Any

from aware_interface_control.cli import (
    handle_interface_command as _handle_interface_command,
    register_interface_parser as _register_interface_parser,
)


def register_interface_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    return _register_interface_parser(subparsers)


def handle_interface_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    ctx: Any,
) -> int:
    _ = ctx
    return _handle_interface_command(args, parser)


__all__ = [
    "handle_interface_command",
    "register_interface_parser",
]
