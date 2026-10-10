"""Direct neutral Workspace source checkout, with no resident transport."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def register_workspace_checkout_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "checkout",
        help="Resolve declared Python packages and copy their source closure.",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="Declared distribution with optional extras/version constraint; repeatable.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Repo-declared source profile; repeatable and composable.",
    )
    parser.add_argument(
        "--overlay",
        action="append",
        default=[],
        help="Declared repository-file overlay; repeatable.",
    )
    parser.add_argument("--forbid-package", action="append", default=[])
    parser.add_argument(
        "--marker",
        action="append",
        default=[],
        help="NAME=VALUE; cross-target requests must supply the complete PEP 508 environment.",
    )
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--plan", action="store_true")
    output.add_argument(
        "--destination", help="New directory outside the source repository."
    )
    output.add_argument(
        "--verify",
        metavar="DESTINATION",
        help="Verify an existing generated source checkout.",
    )
    parser.add_argument("--json", action="store_true")


def handle_workspace_checkout_command(args: argparse.Namespace, context: Any) -> int:
    del context
    from aware_workspace_runtime.composition import WorkspaceCompositionFailure
    from aware_workspace_runtime.package_checkout import (
        PackageCheckoutError,
        PackageSourceCheckout,
        verify_package_checkout,
    )
    from aware_workspace_runtime.source_observation_io import (
        SourceObservationUnavailable,
    )

    try:
        if args.verify:
            if (
                args.package
                or args.profile
                or args.overlay
                or args.marker
                or args.forbid_package
            ):
                raise PackageCheckoutError(
                    "verification accepts no selection overrides"
                )
            result = verify_package_checkout(args.verify)
        else:
            environment = None
            if args.marker:
                environment = {}
                for raw in args.marker:
                    name, separator, value = raw.partition("=")
                    if not separator or name in environment:
                        raise PackageCheckoutError(
                            "marker fields must be unique NAME=VALUE"
                        )
                    environment[name] = value
            with PackageSourceCheckout(args.repo_root) as checkout:
                result = checkout.resolve(
                    args.package,
                    profiles=args.profile,
                    overlays=args.overlay,
                    marker_environment=environment,
                    forbidden_packages=args.forbid_package,
                )
                if args.destination:
                    result = {**checkout.write(args.destination), "inventory": result}
        print(
            json.dumps(result, sort_keys=True, indent=2)
            if args.json
            else f"Workspace checkout: {result.get('state', 'verified')}"
        )
        return 0
    except (
        PackageCheckoutError,
        WorkspaceCompositionFailure,
        SourceObservationUnavailable,
        OSError,
        ValueError,
    ) as error:
        result = {"state": "refused", "reason": str(error)}
        print(
            json.dumps(result, sort_keys=True)
            if args.json
            else f"Workspace checkout refused: {error}",
            file=sys.stderr,
        )
        return 2


__all__ = ["handle_workspace_checkout_command", "register_workspace_checkout_parser"]
