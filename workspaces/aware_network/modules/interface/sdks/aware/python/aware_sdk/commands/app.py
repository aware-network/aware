"""Committed App session commands over the public Interface SDK rail."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, cast

from ..app import (
    AwareAppLaunchDescriptor,
    AwareAppSession,
    failed_run_receipt,
    failed_update_frame,
)
from .interface import _add_interface_client_options, _build_client


class AwareAppCommandError(RuntimeError):
    """Raised when an unsupported App command reaches the handler."""


def register_app_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the actor-facing committed App session command."""

    app_parser = subparsers.add_parser(
        "app",
        help="Enter and render a committed App through Interface authority.",
    )
    app_subparsers = app_parser.add_subparsers(
        dest="app_command",
        required=True,
    )
    run_parser = app_subparsers.add_parser(
        "run",
        help="Enter one aware.app.launch.v0 screen and render its Interface surface.",
    )
    _add_interface_client_options(run_parser)
    run_parser.add_argument(
        "--launch-ref",
        type=Path,
        required=True,
        help="Path to one committed aware.app.launch.v0 descriptor.",
    )
    run_parser.add_argument(
        "--screen",
        help="Committed screen key. Defaults to the descriptor default_screen_key.",
    )
    mode = run_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="Enter, render one receipt, and exit (default).",
    )
    mode.add_argument(
        "--follow",
        action="store_true",
        help="Emit entered and later Interface surface updates as NDJSON.",
    )
    run_parser.add_argument(
        "--poll-interval-ms",
        type=int,
        default=1000,
        help="Polling interval for --follow (default: 1000).",
    )
    run_parser.add_argument(
        "--receipt",
        type=Path,
        help="Optional path for the terminal aware.app.run.v0 receipt.",
    )


def handle_app_command(args: argparse.Namespace) -> int:
    """Run one committed App session command with stable success/failure output."""

    if str(getattr(args, "app_command", "") or "") != "run":
        raise AwareAppCommandError(
            f"Unsupported App command: {getattr(args, 'app_command', None)!r}"
        )
    return _handle_run(args)


def _handle_run(args: argparse.Namespace) -> int:
    namespace = str(getattr(args, "namespace", "") or "")
    screen_key = _optional_text(getattr(args, "screen", None))
    launch: AwareAppLaunchDescriptor | None = None
    phase = "descriptor_validation"
    try:
        launch = AwareAppLaunchDescriptor.from_path(args.launch_ref)
        phase = "interface_client_bootstrap"
        client = _build_client(args)
        phase = "app_screen_entry"
        return asyncio.run(
            _run_session(
                args=args,
                client=client,
                launch=launch,
                namespace=namespace,
                screen_key=screen_key,
            )
        )
    except KeyboardInterrupt:  # pragma: no cover - terminal behavior
        receipt = failed_run_receipt(
            namespace=namespace,
            phase="interrupted",
            error=RuntimeError("App follow interrupted by operator."),
            launch=launch,
            screen_key=screen_key,
        )
        _write_optional_receipt(args, receipt)
        return 130
    except Exception as exc:
        receipt = failed_run_receipt(
            namespace=namespace,
            phase=phase,
            error=exc,
            launch=launch,
            screen_key=screen_key,
        )
        if getattr(args, "follow", False):
            _print_ndjson(failed_update_frame(receipt=receipt, sequence=0))
        else:
            _print_json(receipt)
        _write_optional_receipt(args, receipt)
        return 1


async def _run_session(
    *,
    args: argparse.Namespace,
    client: Any,
    launch: AwareAppLaunchDescriptor,
    namespace: str,
    screen_key: str | None,
) -> int:
    session = await AwareAppSession.open(
        client=client,
        launch_ref=launch,
        screen_key=screen_key,
        namespace=namespace,
    )
    if not getattr(args, "follow", False):
        receipt = session.run_receipt()
        _print_json(receipt)
        _write_optional_receipt(args, receipt)
        return 0

    sequence = 0
    _print_ndjson(session.update_frame(sequence=sequence, event="entered"))
    updates = session.follow(poll_interval_ms=int(args.poll_interval_ms))
    try:
        async for _snapshot in updates:
            sequence += 1
            _print_ndjson(session.update_frame(sequence=sequence, event="updated"))
    except Exception as exc:
        receipt = session.run_receipt(
            status="failed",
            phase="follow",
            update_count=sequence,
            error=str(exc) or type(exc).__name__,
        )
        _print_ndjson(failed_update_frame(receipt=receipt, sequence=sequence + 1))
        _write_optional_receipt(args, receipt)
        return 1
    finally:
        aclose = getattr(updates, "aclose", None)
        if callable(aclose):
            await cast(Callable[[], Awaitable[None]], aclose)()

    receipt = session.run_receipt(
        phase="follow_complete",
        update_count=sequence,
    )
    _write_optional_receipt(args, receipt)
    return 0


def _write_optional_receipt(
    args: argparse.Namespace,
    payload: Mapping[str, object],
) -> None:
    raw_path = getattr(args, "receipt", None)
    if raw_path is None:
        return
    path = Path(raw_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _print_json(payload: Mapping[str, object]) -> None:
    json.dump(dict(payload), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _print_ndjson(payload: Mapping[str, object]) -> None:
    json.dump(dict(payload), sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "AwareAppCommandError",
    "handle_app_command",
    "register_app_parser",
]
