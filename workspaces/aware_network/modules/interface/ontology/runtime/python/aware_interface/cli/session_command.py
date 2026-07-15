"""Interface-owned session CLI command implementation."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any
from uuid import UUID

from aware_cli import session as cli_session
from aware_cli.shared.roots import RootKey

from . import session_support


_event_loop: asyncio.AbstractEventLoop | None = None


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop


def _run(coro):  # type: ignore[no-untyped-def]
    """Run an async coroutine from sync CLI code (reuses a stable event loop)."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = _get_or_create_event_loop()
        return loop.run_until_complete(coro)
    raise RuntimeError("aware-cli session command cannot run inside an existing event loop")


def _resolve_repository_root(ctx: Any):
    environment = getattr(ctx, "environment", None)
    if environment is None or not hasattr(environment, "resolve_root"):
        raise RuntimeError("Session command requires aware-cli execution context.")
    return environment.resolve_root(RootKey.REPOSITORY).resolve()


def handle_session_command(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
    ctx: Any,
) -> int:
    if args.session_command not in {"attach", "bootstrap", "describe", "login", "status", "whoami"}:
        parser.error("Unknown session subcommand")
        return 1

    try:
        repo_root = _resolve_repository_root(ctx)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    endpoint = str(args.endpoint).strip() if args.endpoint else None
    env_config_id = UUID(args.environment_config_id) if args.environment_config_id else None
    apt_id_value = getattr(args, "apt_id", None)
    apt_id = UUID(apt_id_value) if apt_id_value else None
    agent_identity_id = UUID(args.agent_identity_id) if args.agent_identity_id else None
    namespace = (args.namespace or "").strip() or (os.environ.get("AWARE_STATE_NAMESPACE") or "").strip() or "cli"
    state_home = str(args.state_home).strip() if args.state_home else None

    if args.session_command == "login":
        try:
            resolved = _run(
                session_support.login_cli_session(
                    repository_root=repo_root,
                    endpoint=endpoint,
                    namespace=namespace,
                    state_home=state_home,
                    auth_token=getattr(args, "auth_token", None),
                )
            )
            print(
                json.dumps(
                    cli_session.render_session_payload(resolved),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.session_command in {"attach", "status", "whoami"}:
        try:
            resolved = session_support.resolve_cli_session(
                repository_root=repo_root,
                endpoint=endpoint,
                environment_config_id=env_config_id,
                agent_identity_id=agent_identity_id,
                namespace=namespace,
                state_home=state_home,
                provider=getattr(args, "provider", None),
                provider_session_id=getattr(args, "provider_session_id", None),
            )
            if args.session_command == "attach":
                attached = cli_session.attach_cli_session(
                    resolved=resolved,
                    process_key=getattr(args, "process", None),
                    thread_key=getattr(args, "thread", None),
                )
                print(
                    json.dumps(
                        cli_session.render_session_payload(
                            resolved,
                            attached_context=attached,
                        ),
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0
            if args.session_command == "whoami":
                print(
                    json.dumps(
                        cli_session.render_session_payload(resolved),
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0

            local_status = session_support.describe_local_session_status(
                resolved=resolved,
            )
            interface_backend = session_support.describe_interface_backend_status(
                resolved=resolved,
            )
            print(
                json.dumps(
                    cli_session.render_session_status_payload(
                        resolved=resolved,
                        local_status=local_status,
                        interface_backend=interface_backend,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.session_command == "describe":
        _ = repo_root, endpoint, env_config_id, apt_id, agent_identity_id
        print(
            "Error: session describe requires the Environment SDK session rail; "
            "root aware_environment.runtime.api_session is retired.",
            file=sys.stderr,
        )
        return 1

    _ = repo_root, endpoint, env_config_id, apt_id, agent_identity_id, namespace
    print(
        "Error: session bootstrap requires the Environment SDK session rail; "
        "root aware_environment.runtime.api_session is retired.",
        file=sys.stderr,
    )
    return 1


def register_session_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "session", help="Bootstrap and cache remote authority metadata."
    )
    parser.set_defaults(command="session")
    session_subparsers = parser.add_subparsers(dest="session_command", required=True)

    def _add_scope_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--namespace",
            default=None,
            help="State namespace under $AWARE_STATE_HOME (default: $AWARE_STATE_NAMESPACE or 'cli').",
        )
        p.add_argument(
            "--state-home",
            default=None,
            help="Override $AWARE_STATE_HOME for cache/context location.",
        )
        p.add_argument(
            "--endpoint",
            default=None,
            help="Override Node WS endpoint (else AWARE_NODE_WS_URL/AWARE_NODE_BASE_URL/.aware/network_node.json).",
        )
        p.add_argument(
            "--environment-config-id",
            default=None,
            help="Override environment config id (UUID).",
        )
        p.add_argument(
            "--agent-identity-id",
            default=None,
            help="Override agent identity id (UUID) when multiple keys are configured.",
        )

    def _add_provider_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--provider",
            default=None,
            help="Interface provider name (for example codex, claude_code, gemini).",
        )
        p.add_argument(
            "--provider-session-id",
            default=None,
            help="Provider session id override. Defaults to AWARE_INTERFACE_PROVIDER_SESSION_ID or provider-specific env fallbacks.",
        )

    attach = session_subparsers.add_parser(
        "attach",
        help="Resolve actor/session identity offline and persist active process/thread context.",
    )
    _add_scope_flags(attach)
    _add_provider_flags(attach)
    attach.add_argument(
        "--process",
        default=None,
        help="Explicit process key override. Defaults to a provider-derived key when provider identity is available.",
    )
    attach.add_argument(
        "--thread",
        default=None,
        help="Explicit thread key override. Defaults to a provider-session-derived key when provider identity is available.",
    )

    whoami = session_subparsers.add_parser(
        "whoami",
        help="Resolve actor/session identity offline and print the current interface session summary.",
    )
    _add_scope_flags(whoami)
    _add_provider_flags(whoami)

    login = session_subparsers.add_parser(
        "login",
        help="Authenticate the current interface session with an auth token and persist auth state.",
    )
    _add_scope_flags(login)
    login.add_argument(
        "--auth-token",
        default=None,
        help="Auth token override. Defaults to $AWARE_AUTH_TOKEN.",
    )

    status = session_subparsers.add_parser(
        "status",
        help="Show offline session/context/status/catalog readiness without requiring a live Node.",
    )
    _add_scope_flags(status)
    _add_provider_flags(status)

    describe = session_subparsers.add_parser(
        "describe",
        help="Describe the remote environment (describe_environment_config + describe_environment).",
    )
    _add_scope_flags(describe)
    describe.add_argument(
        "--apt-id",
        default=None,
        help="Override AgentProcessThread id (UUID).",
    )

    bootstrap = session_subparsers.add_parser(
        "bootstrap",
        help="Authenticate + provision + cache describe_environment_config + capabilities.",
    )
    _add_scope_flags(bootstrap)
    bootstrap.add_argument(
        "--apt-id",
        default=None,
        help="Override AgentProcessThread id (UUID).",
    )
    return parser


__all__ = ["handle_session_command", "register_session_parser"]
