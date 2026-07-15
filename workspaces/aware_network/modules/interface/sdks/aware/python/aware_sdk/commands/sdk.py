"""Preview SDK operation catalog renderer commands."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aware_sdk.operation_catalog import (
    SDK_OPERATION_CATALOG_CONTRACT,
    SdkOperationCatalogError,
    invoke_sdk_operation,
    load_sdk_operation_catalog_index,
    parse_json_object,
    path_context_value,
)


def register_sdk_operation_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register hidden/preview SDK operation catalog commands."""

    sdk_parser = subparsers.add_parser(
        "sdk",
        help="Preview: render SDK-declared operation catalogs.",
    )
    sdk_subparsers = sdk_parser.add_subparsers(
        dest="sdk_command", metavar="sdk-command"
    )

    operations_parser = sdk_subparsers.add_parser(
        "operations",
        help="List SDK-declared operations from discovered catalogs.",
    )
    _add_catalog_options(operations_parser)

    describe_parser = sdk_subparsers.add_parser(
        "describe",
        help="Describe one SDK-declared operation.",
    )
    _add_catalog_options(describe_parser)
    describe_parser.add_argument("operation_ref")

    invoke_parser = sdk_subparsers.add_parser(
        "invoke",
        help="Invoke one SDK-declared operation through its explicit handler.",
    )
    _add_catalog_options(invoke_parser)
    invoke_parser.add_argument("operation_ref")
    invoke_parser.add_argument(
        "--payload-json",
        help="JSON object request payload for the SDK operation.",
    )
    invoke_parser.add_argument(
        "--context-json",
        help="JSON object context payload passed to the SDK operation handler.",
    )
    invoke_parser.add_argument(
        "--namespace",
        help="Optional renderer namespace context for SDK operation handlers.",
    )
    invoke_parser.add_argument(
        "--socket-path",
        type=Path,
        help="Optional local control socket path context.",
    )
    invoke_parser.add_argument(
        "--state-home",
        type=Path,
        help="Optional local control state-home context.",
    )
    invoke_parser.add_argument(
        "--timeout-s",
        type=float,
        help="Optional SDK operation timeout hint in seconds.",
    )
    invoke_parser.add_argument(
        "--allow-mutation",
        action="store_true",
        help="Allow invoking SDK operations declared with non-read effects.",
    )


def handle_sdk_command(args: argparse.Namespace) -> int:
    """Execute one preview SDK operation catalog command."""

    sdk_command = str(getattr(args, "sdk_command", "") or "")
    if not sdk_command:
        raise SdkOperationCatalogError("Missing SDK operation catalog command.")

    index = load_sdk_operation_catalog_index(
        extra_provider_refs=tuple(getattr(args, "catalog_provider", ()) or ()),
        include_builtin_providers=not bool(getattr(args, "no_builtin_catalogs", False)),
    )
    if sdk_command == "operations":
        _print_json(index.list_payload())
        return 0
    if sdk_command == "describe":
        operation = index.resolve(_required_text(getattr(args, "operation_ref", None)))
        _print_json(
            {
                "catalog_contract": SDK_OPERATION_CATALOG_CONTRACT,
                "operation": operation.detail_payload(),
            }
        )
        return 0
    if sdk_command == "invoke":
        operation = index.resolve(_required_text(getattr(args, "operation_ref", None)))
        request_payload = parse_json_object(
            getattr(args, "payload_json", None),
            label="SDK operation payload",
        )
        context = _context_payload(args)
        result = asyncio.run(
            invoke_sdk_operation(
                operation=operation,
                request_payload=request_payload,
                context=context,
                timeout_s=getattr(args, "timeout_s", None),
                allow_mutation=bool(getattr(args, "allow_mutation", False)),
            )
        )
        _print_json(
            {
                "catalog_contract": SDK_OPERATION_CATALOG_CONTRACT,
                "operation_ref": operation.operation_ref,
                "effect": operation.effect,
                "result": result,
            }
        )
        return 0
    raise SdkOperationCatalogError(
        f"Unsupported SDK operation catalog command: {sdk_command}"
    )


def _add_catalog_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--catalog-provider",
        action="append",
        default=[],
        help=(
            "Extra catalog provider import ref using module:callable syntax. "
            "Installed entry points and built-in bootstrap providers are loaded first."
        ),
    )
    parser.add_argument(
        "--no-builtin-catalogs",
        action="store_true",
        help="Disable built-in bootstrap catalog providers.",
    )


def _context_payload(args: argparse.Namespace) -> dict[str, object]:
    context = parse_json_object(
        getattr(args, "context_json", None),
        label="SDK operation context",
    )
    for key, value in {
        "namespace": getattr(args, "namespace", None),
        "socket_path": path_context_value(getattr(args, "socket_path", None)),
        "state_home": path_context_value(getattr(args, "state_home", None)),
    }.items():
        if value is not None:
            context[key] = value
    return context


def _print_json(value: Any) -> None:
    json.dump(_jsonable(value), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _jsonable(value: Any) -> Any:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _required_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise SdkOperationCatalogError("Missing required SDK operation value.")
    return text


__all__ = [
    "handle_sdk_command",
    "register_sdk_operation_parsers",
]
