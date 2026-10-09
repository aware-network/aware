"""Workspace-owned module lifecycle command projection."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Protocol, cast

from aware_workspace_operator.models import WorkspaceModuleCreateOptions
from aware_workspace_operator.module_create import (
    print_workspace_module_create_result,
    run_workspace_module_create,
)

_REPO_ROOT_ENV_VARS = ("AWARE_REPO_ROOT", "AWARE_REPOSITORY_ROOT")


class ModuleCreateArgs(Protocol):
    module_command: str | None
    module_id: str
    dependency: list[str]
    title: str | None
    description: str | None
    handler_module: list[str]
    runtime_project_name: str | None
    runtime_import_root: str | None
    dry_run: bool
    force: bool
    json: bool
    repo_root: str | None


class SubparserCollection(Protocol):
    def add_parser(self, name: str, **kwargs: object) -> argparse.ArgumentParser: ...


def handle_module_command(
    args: argparse.Namespace, parser: argparse.ArgumentParser, ctx: Any
) -> int:
    _ = ctx
    module_args = _as_module_create_args(args)

    if module_args.module_command != "create":
        parser.error("Unknown module subcommand")

    repo_root = _resolve_repo_root(args=module_args, parser=parser)

    try:
        outcome = run_workspace_module_create(
            options=WorkspaceModuleCreateOptions(
                repo_root=repo_root,
                module_id=module_args.module_id,
                dependencies=tuple(module_args.dependency),
                title=module_args.title,
                description=module_args.description,
                runtime_handler_modules=tuple(module_args.handler_module),
                runtime_project_name=module_args.runtime_project_name,
                runtime_import_root=module_args.runtime_import_root,
                force=module_args.force,
                dry_run=module_args.dry_run,
            )
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    exit_code = int(outcome.exit_code)
    report_payload = cast(
        dict[str, object], outcome.report.model_dump(mode="json")
    )

    if module_args.json:
        print(json.dumps(report_payload, indent=2))
        return exit_code

    print_workspace_module_create_result(payload=report_payload)
    return exit_code


def register_module_parser(subparsers: SubparserCollection) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "module",
        help=(
            "Module lifecycle helpers "
            "(compiler-owned scaffolding for structure/docs-specs/runtime/app-surface rails)."
        ),
    )
    module_subparsers = parser.add_subparsers(dest="module_command")
    module_subparsers.required = True

    create = module_subparsers.add_parser(
        "create",
        help=(
            "Create a canonical module scaffold under modules/<module_id>/ "
            "with structure/docs-specs/runtime/app-surface service rails."
        ),
    )
    _ = create.add_argument(
        "module_id", help="Module id (lowercase, e.g. experimental, network)."
    )
    _ = create.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Optional repository root. "
            "When omitted, aware-cli uses AWARE_REPO_ROOT/AWARE_REPOSITORY_ROOT."
        ),
    )
    _ = create.add_argument(
        "--title",
        default=None,
        help="Optional ontology package title for ontology/structure/aware.toml.",
    )
    _ = create.add_argument(
        "--description",
        default=None,
        help="Optional ontology package description for ontology/structure/aware.toml.",
    )
    _ = create.add_argument(
        "--dependency",
        action="append",
        default=[],
        help="Repeatable ontology dependency package_name to append to aware.toml.",
    )
    _ = create.add_argument(
        "--handler-module",
        action="append",
        default=[],
        help=(
            "Repeatable runtime handler module import path for [runtime].handler_modules in aware.module.toml. "
            "Default is an explicit empty list."
        ),
    )
    _ = create.add_argument(
        "--runtime-project-name",
        default=None,
        help=(
            "Optional runtime package distribution name override for "
            "ontology/runtime/python/pyproject.toml "
            "and [runtime].project_name in aware.module.toml."
        ),
    )
    _ = create.add_argument(
        "--runtime-import-root",
        default=None,
        help=(
            "Optional runtime Python import root override for generated runtime package path "
            "and [runtime].import_root in aware.module.toml."
        ),
    )
    _ = create.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan scaffold outputs without writing files.",
    )
    _ = create.add_argument(
        "--force",
        action="store_true",
        help="Overwrite scaffold files if they already exist.",
    )
    _ = create.add_argument(
        "--json",
        action="store_true",
        help="Emit scaffold result as JSON.",
    )
    return parser


def _module_create_import_error(exc: Exception) -> str:
    return (
        "Module creation requires the Workspace Operator package "
        f"to be importable. Error: {exc}"
    )


def _as_module_create_args(args: argparse.Namespace) -> ModuleCreateArgs:
    return cast(ModuleCreateArgs, cast(object, args))


def _resolve_repo_root(
    *, args: ModuleCreateArgs, parser: argparse.ArgumentParser
) -> Path:
    raw = (args.repo_root or "").strip()
    if raw:
        return _validate_repo_root(parser=parser, raw_root=raw, source="--repo-root")

    for env_name in _REPO_ROOT_ENV_VARS:
        raw_root = (os.environ.get(env_name) or "").strip()
        if raw_root:
            return _validate_repo_root(
                parser=parser,
                raw_root=raw_root,
                source=env_name,
            )

    parser.error(
        "Module creation requires an explicit repository root. Pass --repo-root "
        f"or set {' / '.join(_REPO_ROOT_ENV_VARS)}."
    )
    raise AssertionError("unreachable")


def _validate_repo_root(
    *,
    parser: argparse.ArgumentParser,
    raw_root: object,
    source: str,
) -> Path:
    root = Path(str(raw_root)).expanduser().resolve()
    if not root.exists():
        parser.error(f"{source} does not exist: {root}")
    if not root.is_dir():
        parser.error(f"{source} must be a directory: {root}")
    return root


__all__ = ["handle_module_command", "register_module_parser"]
