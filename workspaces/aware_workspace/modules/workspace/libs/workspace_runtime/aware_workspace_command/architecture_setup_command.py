"""Workspace-owned CLI over the public architecture setup SDK."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from aware_workspace_sdk.architecture_setup import (
    ArchitectureSetupError,
    ArchitectureSetupRequest,
    WorkspaceSetupClient,
)

_CONTRACT = "aware.workspace.architecture-setup-command.v1"


def register_workspace_setup_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    setup = subparsers.add_parser(
        "setup", help="Create Aware architecture and align authored Python packages."
    )
    configure_workspace_setup_parser(setup)


def configure_workspace_setup_parser(parser: argparse.ArgumentParser) -> None:
    """Configure an already selected setup command, without broader routing."""
    operations = parser.add_subparsers(dest="setup_operation", required=True)
    for operation in ("repository", "workspace", "module", "python-package", "align"):
        parser = operations.add_parser(operation)
        _common(parser)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--preview", action="store_true", help="Read-only (default).")
        mode.add_argument("--apply", action="store_true")
        parser.add_argument("--expected-plan-sha256")
        parser.add_argument("--allowed-path", action="append", default=[])
        if operation != "align":
            parser.add_argument("--name", required=True)
        if operation == "repository":
            parser.add_argument("--license-expression", required=True)
        if operation == "module":
            parser.add_argument("--workspace", required=True)
        if operation == "align":
            parser.add_argument(
                "--workspace",
                help="Registered Workspace resolution root (default: Repository).",
            )
        if operation == "python-package":
            parser.add_argument(
                "--owner",
                choices=("repository", "workspace", "module"),
                default="module",
                help="Authored package owner (default: module).",
            )
            parser.add_argument("--workspace")
            parser.add_argument("--module")
            parser.add_argument("--distribution", required=True)
            parser.add_argument("--import-root", required=True)
            parser.add_argument("--package-version", default="0.1.0")
            parser.add_argument("--requires-python", default=">=3.12")
            parser.add_argument("--dependency", action="append", default=[])
        if operation in ("workspace", "module", "python-package"):
            parser.add_argument("--path")
    locks = operations.add_parser("locks", help="Explicit offline UV lock operations.")
    modes = locks.add_subparsers(dest="lock_operation", required=True)
    for operation in ("check", "update"):
        parser = modes.add_parser(operation)
        _common(parser)
        parser.add_argument("--uv-executable", type=Path, required=True)
        parser.add_argument(
            "--workspace",
            help="Registered Workspace resolution root (default: Repository).",
        )


def _common(parser: argparse.ArgumentParser) -> None:
    # Preserve the provider path across the operator shell's generic root resolution.
    parser.add_argument(
        "--repository-root", dest="setup_repository_root", type=Path, required=True
    )
    parser.add_argument("--json", action="store_true")


def _request(args: argparse.Namespace) -> ArchitectureSetupRequest:
    path = getattr(args, "path", None)
    if path is None:
        path = {
            "workspace": getattr(args, "name", ""),
            "module": "modules/" + getattr(args, "name", ""),
            "python-package": "libs/" + getattr(args, "name", "") + "/python",
        }.get(args.setup_operation, "")
    return ArchitectureSetupRequest(
        "package_manager"
        if args.setup_operation == "align"
        else "python_package"
        if args.setup_operation == "python-package"
        else args.setup_operation,
        name=getattr(args, "name", ""),
        workspace=getattr(args, "workspace", None) or "",
        module=getattr(args, "module", None) or "",
        path=path,
        distribution=getattr(args, "distribution", ""),
        import_root=getattr(args, "import_root", ""),
        version=getattr(args, "package_version", "0.1.0"),
        requires_python=getattr(args, "requires_python", ">=3.12"),
        dependencies=tuple(getattr(args, "dependency", ())),
        license_expression=getattr(args, "license_expression", ""),
        owner=getattr(args, "owner", "module"),
    )


def _emit(payload: dict[str, object], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print(f"Workspace setup: {payload['operation']} — {payload['status']}")
        # Keep complete receipts available in human output too.
        print(json.dumps(payload, sort_keys=True, indent=2))


def handle_workspace_setup_command(args: argparse.Namespace) -> int:
    payload: dict[str, object] = {
        "contract": _CONTRACT,
        "operation": args.setup_operation,
        "resolution_root": str(args.setup_repository_root),
    }
    effect_started = False
    try:
        locks = args.setup_operation == "locks"
        if not locks:
            if args.apply and not args.expected_plan_sha256:
                raise ArchitectureSetupError("apply_requires_expected_plan_sha256")
            if not args.apply and (args.expected_plan_sha256 or args.allowed_path):
                raise ArchitectureSetupError("apply_options_require_apply")
        with WorkspaceSetupClient.filesystem(
            repository_root=args.setup_repository_root,
            uv_executable=getattr(args, "uv_executable", None),
        ) as client:
            if locks:
                effect_started = True
                repository = client.repository()
                owner = (
                    repository.workspace(args.workspace)
                    if args.workspace
                    else repository
                )
                results = (
                    owner.check_locks()
                    if args.lock_operation == "check"
                    else owner.update_locks()
                )
                payload["receipts"] = [asdict(result) for result in results]
                payload["resolution_root"] = results[0].resolution_root
                payload["status"] = (
                    "succeeded"
                    if all(result.returncode == 0 for result in results)
                    else "failed"
                )
                code = 0 if payload["status"] == "succeeded" else 1
            else:
                request = _request(args)
                preview = client.preview(request)
                paths = tuple(change.path for change in preview.changes)
                payload.update(preview=asdict(preview), proposed_write_paths=paths)
                if args.apply:
                    if args.expected_plan_sha256 != preview.plan_sha256:
                        raise ArchitectureSetupError("setup_plan_changed")
                    if len(set(args.allowed_path)) != len(args.allowed_path) or set(
                        args.allowed_path
                    ) != set(paths):
                        raise ArchitectureSetupError("setup_write_scope_mismatch")
                    effect_started = True
                    receipt = client.apply(
                        request, expected_plan_sha256=args.expected_plan_sha256
                    )
                    payload.update(status=receipt.status, receipt=asdict(receipt))
                else:
                    payload["status"] = "planned"
                code = 0
        _emit(payload, json_output=args.json)
        return code
    except ArchitectureSetupError as error:
        receipt = error.receipt
        uncertain = receipt is not None and receipt.status in (
            "uncertain",
            "partial_applied",
        )
        payload.update(
            status="uncertain" if uncertain else "refused",
            error=str(error),
            receipt=asdict(receipt) if receipt is not None else None,
        )
        _emit(payload, json_output=args.json)
        return 3 if uncertain else 2
    except ModuleNotFoundError as error:
        payload.update(
            status="uncertain" if effect_started else "refused",
            error="setup_provider_unavailable",
            missing_module=error.name,
        )
        _emit(payload, json_output=args.json)
        return 3 if effect_started else 2
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        # Preserve an external failure without asserting rollback or retry safety.
        payload.update(
            status="uncertain" if effect_started else "refused",
            error=type(error).__name__,
        )
        if isinstance(error, subprocess.TimeoutExpired):
            payload.update(
                command=error.cmd,
                partial_stdout=_output(error.stdout),
                partial_stderr=_output(error.stderr),
            )
        _emit(payload, json_output=args.json)
        return 3 if effect_started else 2


def _output(value: str | bytes | None) -> str:
    return (
        value.decode("utf-8", errors="surrogateescape")
        if isinstance(value, bytes)
        else value or ""
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aware-workspace")
    register_workspace_setup_parser(
        parser.add_subparsers(dest="workspace_command", required=True)
    )
    return handle_workspace_setup_command(parser.parse_args(argv))


__all__ = [
    "configure_workspace_setup_parser",
    "handle_workspace_setup_command",
    "main",
    "register_workspace_setup_parser",
]
