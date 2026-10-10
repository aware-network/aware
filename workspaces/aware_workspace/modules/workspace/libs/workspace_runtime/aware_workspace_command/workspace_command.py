"""Lightweight Workspace command router with lazy Product delegation."""

from __future__ import annotations

import argparse
from importlib import import_module
from typing import Any

_LEGACY_PARSER_REGISTRATIONS = (
    (
        "package-manager-manifest",
        "aware_workspace.materialization.package_manager_manifest_command",
        "register_workspace_package_manager_manifest_parser",
    ),
    (
        "bootstrap",
        "aware_workspace.setup.command.bootstrap_parser",
        "register_workspace_bootstrap_parser",
    ),
    (
        "quality-gates",
        "aware_workspace.tooling.command.quality_gates_parser",
        "register_workspace_quality_gates_parser",
    ),
    (
        "status",
        "aware_workspace.status.command.status_parser",
        "register_workspace_status_parsers",
    ),
    (
        "status-benchmark",
        "aware_workspace.status.command.status_parser",
        "register_workspace_status_parsers",
    ),
    (
        "test",
        "aware_workspace.test.command.test_parser",
        "register_workspace_test_parser",
    ),
    (
        "prepare",
        "aware_workspace.prepare.command.prepare_parser",
        "register_workspace_prepare_parser",
    ),
    (
        "materialization-operation",
        "aware_workspace.materialization_operation.command",
        "register_workspace_materialization_operation_parser",
    ),
    (
        "service-host",
        "aware_workspace.deployment.command.service_host_parser",
        "register_workspace_service_host_parser",
    ),
    (
        "publication",
        "aware_workspace.publication.command.publication_parser",
        "register_workspace_publication_parsers",
    ),
    (
        "publish",
        "aware_workspace.publication.command.publication_parser",
        "register_workspace_publication_parsers",
    ),
    (
        "deployment",
        "aware_workspace.deployment.command.deployment_parser",
        "register_workspace_deployment_parser",
    ),
    (
        "revision-filesystem-root",
        "aware_workspace.revision.filesystem.command.revision_filesystem_parser",
        "register_workspace_revision_filesystem_parser",
    ),
    (
        "format-python",
        "aware_workspace.tooling.command.format_python_parser",
        "register_workspace_format_python_parser",
    ),
)


def register_workspace_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    args_list: tuple[str, ...] = (),
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "workspace",
        help="Workspace materialization and optional product helpers.",
    )
    workspace_subparsers = parser.add_subparsers(dest="workspace_command")
    workspace_subparsers.required = True
    selected = (
        str(args_list[1]).strip()
        if len(args_list) > 1 and str(args_list[0]).strip() == "workspace"
        else None
    )
    if selected in ("-h", "--help"):
        selected = None
    if selected in (None, "materialize"):
        from .materialize_command import register_workspace_materialize_parser

        register_workspace_materialize_parser(workspace_subparsers)
    if selected in (None, "checkout"):
        from .checkout_command import register_workspace_checkout_parser

        register_workspace_checkout_parser(workspace_subparsers)
    if selected is not None and selected not in ("materialize", "checkout"):
        _register_selected_legacy_parser(
            selected=selected,
            subparsers=workspace_subparsers,
        )
    return parser


def handle_workspace_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    ctx: Any,
) -> int:
    command = str(getattr(args, "workspace_command", "") or "")
    if command == "checkout":
        from .checkout_command import handle_workspace_checkout_command

        return handle_workspace_checkout_command(args, ctx)
    if command == "materialize":
        from .materialize_command import handle_workspace_materialize_command

        return handle_workspace_materialize_command(args=args, context=ctx)
    return _handle_selected_legacy_command(
        command=command,
        args=args,
        parser=parser,
        context=ctx,
    )


def _register_selected_legacy_parser(
    *,
    selected: str,
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    invoked: set[tuple[str, str]] = set()
    for command, module_name, register_name in _LEGACY_PARSER_REGISTRATIONS:
        if command != selected:
            continue
        key = (module_name, register_name)
        if key in invoked:
            continue
        try:
            register = getattr(import_module(module_name), register_name)
        except ModuleNotFoundError:
            return
        register(subparsers)
        invoked.add(key)


def _handle_selected_legacy_command(
    *,
    command: str,
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    context: Any,
) -> int:
    try:
        module = import_module("aware_workspace.cli.workspace_command")
    except ModuleNotFoundError:
        parser.error(
            f"Workspace Product command '{command}' is unavailable in this distribution"
        )
        return 2
    return int(module.handle_workspace_command(args, parser, context))


__all__ = ["handle_workspace_command", "register_workspace_parser"]
