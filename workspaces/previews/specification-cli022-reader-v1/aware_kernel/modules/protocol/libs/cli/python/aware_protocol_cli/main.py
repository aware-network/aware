"""CLI projection for canonical Protocol SDK operations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib import metadata
from typing import TextIO

from aware_command_runtime import (
    AwareCommandInvocation,
    AwareCommandRegistry,
    dispatch_command,
)
from aware_protocol_fs_adapter import FilesystemProtocolSdkProvider
from aware_protocol_runtime import (
    ProtocolAdmissionOutcomeKind,
    ProtocolAuthorityMode,
)
from aware_protocol_sdk import (
    PROTOCOL_ADMIT_TARGET_OPERATION_REF,
    ProtocolSdkClient,
    ProtocolTargetAdmissionRequest,
)


def main(argv: Sequence[str] | None = None) -> int:
    registry = AwareCommandRegistry()
    register_admit_command(registry)
    parser = _parser(registry)
    args = parser.parse_args(argv)
    if args.command == "version":
        _print_json(_version_payload())
        return 0
    if args.command == "setup-specification":
        # Optional composition above the owners; never select a different rail.
        from .specification_setup import setup_command_payload

        payload, exit_code = setup_command_payload(args)
        payload["interface"] = {
            "kind": "cli",
            "distribution": "aware-protocol-cli",
            "version": _distribution_version("aware-protocol-cli"),
        }
        _print_json(payload)
        return exit_code
    return dispatch_command(
        registry,
        args=args,
        parser=parser,
        argv=sys.argv[1:] if argv is None else argv,
    )


def register_admit_command(registry: AwareCommandRegistry) -> None:
    """Expose one SDK projection; registration is not provider admission."""
    registry.register_command(
        name="admit",
        help="Admit one explicit repository Protocol target.",
        configure_parser=_configure_admit_parser,
        handle=_handle_admit,
        source="aware_protocol_cli",
        operation_ref=PROTOCOL_ADMIT_TARGET_OPERATION_REF,
    )


def _handle_admit(invocation: AwareCommandInvocation) -> int:
    args = invocation.args
    try:
        request = ProtocolTargetAdmissionRequest(
            authority_mode=ProtocolAuthorityMode(args.authority_mode),
            target_ref=args.repository_root,
            source_ref=str(args.manifest_path),
        )
        result = ProtocolSdkClient(
            provider=FilesystemProtocolSdkProvider()
        ).admit_target(request)
        payload = result.to_wire()
        payload["interface"] = {
            "kind": "cli",
            "distribution": "aware-protocol-cli",
            "version": _distribution_version("aware-protocol-cli"),
        }
        _print_json(payload)
        return (
            0
            if result.admission.outcome is ProtocolAdmissionOutcomeKind.CANONICAL_V1
            else 2
        )
    except Exception as error:  # noqa: BLE001 - stable CLI boundary.
        _print_json(
            {
                "status": "error",
                "operation_ref": PROTOCOL_ADMIT_TARGET_OPERATION_REF,
                "error_type": type(error).__name__,
                "message": str(error),
            },
            stream=sys.stderr,
        )
        return 1


def _configure_admit_parser(admit: argparse.ArgumentParser) -> None:
    admit.add_argument("--repository-root", required=True)
    admit.add_argument("--manifest-path", default="aware.protocol.toml")
    admit.add_argument(
        "--authority-mode",
        choices=tuple(item.value for item in ProtocolAuthorityMode),
        default=ProtocolAuthorityMode.FILESYSTEM.value,
    )


def _parser(registry: AwareCommandRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-protocol",
        description="Invoke canonical Aware Protocol SDK operations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    spec = registry.require("admit")
    admit = subparsers.add_parser(spec.name, help=spec.help)
    spec.configure_parser(admit)
    admit.set_defaults(_aware_command_name=spec.name)
    setup = subparsers.add_parser(
        "setup-specification",
        help="Preview or explicitly apply Issue-governed SPEC binding setup.",
        description=(
            "Configure the explicit filesystem SPEC binding only. Preview is "
            "the default; apply obtains fresh Issue admission. No documents, "
            "approval, staging or repository publication."
        ),
    )
    setup.add_argument("--repository-root", required=True)
    setup.add_argument("--manifest-path", default="aware.protocol.toml")
    setup.add_argument("--expected-manifest-sha256", required=True)
    setup.add_argument("--issue-ref", required=True)
    setup.add_argument("--expected-issue-sha256", required=True)
    setup.add_argument("--specification-root", required=True)
    setup.add_argument(
        "--directory-path",
        action="append",
        default=[],
        help="Repeat for each explicitly admitted root/ancestor, in effect order.",
    )
    setup.add_argument("--client-intent-id", required=True)
    intent = setup.add_mutually_exclusive_group()
    intent.add_argument("--dry-run", action="store_true", help="Explicit preview.")
    intent.add_argument("--apply", action="store_true", help="Perform governed setup.")
    subparsers.add_parser(
        "version",
        help="Report installed interface, SDK, provider, and operation identity.",
    )
    return parser


def _version_payload() -> dict[str, object]:
    return {
        "status": "ok",
        "operation_ref": PROTOCOL_ADMIT_TARGET_OPERATION_REF,
        "authority_modes": [ProtocolAuthorityMode.FILESYSTEM.value],
        "distributions": {
            name: _distribution_version(name)
            for name in (
                "aware-protocol-cli",
                "aware-protocol-sdk",
                "aware-protocol-fs-adapter",
                "aware-protocol-runtime",
            )
        },
    }


def _distribution_version(distribution_name: str) -> str:
    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "source"


def _print_json(payload: object, *, stream: TextIO | None = None) -> None:
    print(
        json.dumps(payload, indent=2, sort_keys=True),
        file=sys.stdout if stream is None else stream,
    )


if __name__ == "__main__":
    raise SystemExit(main())
