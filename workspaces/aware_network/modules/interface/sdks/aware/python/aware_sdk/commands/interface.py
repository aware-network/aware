"""Interface-first renderer commands for the public aware-sdk rail."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any, cast

_DEFAULT_NAMESPACE = "default"
_TRANSITIONAL_ACTION_COMMANDS = frozenset({"actions", "run"})


class InterfaceRendererCommandError(RuntimeError):
    """Raised when an Interface renderer command cannot be executed."""


def register_interface_renderer_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    include_transitional_actions: bool = False,
) -> None:
    """Register root Interface renderer commands on the aware-sdk parser."""

    status_parser = subparsers.add_parser(
        "status",
        help="Render the current Interface status snapshot.",
    )
    _add_interface_client_options(status_parser)

    render_parser = subparsers.add_parser(
        "render",
        help="Render the current Interface screen, sections, and panes.",
    )
    _add_interface_client_options(render_parser)

    panes_parser = subparsers.add_parser(
        "panes",
        help="List panes and pane API capability endpoints for the current Interface surface.",
    )
    _add_interface_client_options(panes_parser)

    invoke_parser = subparsers.add_parser(
        "invoke",
        help="Invoke one capability endpoint exposed by a rendered pane.",
    )
    _add_interface_client_options(invoke_parser)
    invoke_parser.add_argument("pane_ref")
    invoke_parser.add_argument("capability_ref")
    invoke_parser.add_argument(
        "--discriminant",
        help="Optional service-operation discriminant. Defaults to capability_ref.",
    )
    invoke_parser.add_argument(
        "--payload-json",
        help="Optional JSON object payload for the pane capability endpoint.",
    )

    act_parser = subparsers.add_parser(
        "act",
        help="Perform one action exposed by a rendered pane.",
    )
    _add_interface_client_options(act_parser)
    act_parser.add_argument("pane_ref")
    act_parser.add_argument("action_ref")
    act_parser.add_argument(
        "--payload-json",
        help="Optional JSON object payload for the pane action.",
    )

    follow_parser = subparsers.add_parser(
        "follow",
        help="Stream Interface status snapshots.",
    )
    _add_interface_client_options(follow_parser)
    follow_parser.add_argument(
        "--poll-interval-ms",
        type=int,
        default=1000,
        help="Polling interval used by the Interface follow stream.",
    )
    follow_parser.add_argument(
        "--once",
        action="store_true",
        help="Print one snapshot and exit.",
    )

    capabilities_parser = subparsers.add_parser(
        "capabilities",
        help="Render Interface-mediated capability state.",
    )
    _add_interface_client_options(capabilities_parser)

    profile_parser = subparsers.add_parser(
        "profile",
        help="Select or inspect Interface control-plane profiles.",
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command",
        required=True,
    )
    profile_select_parser = profile_subparsers.add_parser(
        "select",
        help="Select the active Interface control-plane profile.",
    )
    _add_interface_client_options(profile_select_parser)
    profile_select_parser.add_argument("profile_id")

    if include_transitional_actions:
        actions_parser = subparsers.add_parser(
            "actions",
            help="Transitional: list current surface affordances.",
        )
        _add_interface_client_options(actions_parser)

        run_parser = subparsers.add_parser(
            "run",
            help="Transitional: ask Interface to perform one current surface affordance.",
        )
        _add_interface_client_options(run_parser)
        run_parser.add_argument("action_key")
        run_parser.add_argument(
            "--payload-json",
            help="Optional JSON object payload for the surface affordance.",
        )


def handle_interface_renderer_command(args: argparse.Namespace) -> int:
    """Execute one root Interface renderer command."""

    from aware_interface_sdk import InterfaceHostUnavailableError

    command = str(getattr(args, "command", "") or "")
    namespace = _namespace(args)
    try:
        client = _build_client(args)
        surface_context = _surface_context_from_args(args)
        if command == "status":
            surface = _surface_for_renderer_command(
                client=client,
                namespace=namespace,
                args=args,
                surface_context=surface_context,
            )
            _print_json(_with_local_host_ensure(args, surface.status_payload()))
            return 0
        if command == "render":
            surface = _surface_for_renderer_command(
                client=client,
                namespace=namespace,
                args=args,
                surface_context=surface_context,
            )
            _print_json(surface.render_payload())
            return 0
        if command == "panes":
            surface = _surface_for_renderer_command(
                client=client,
                namespace=namespace,
                args=args,
                surface_context=surface_context,
            )
            _print_json(surface.panes_payload())
            return 0
        if command == "invoke":
            payload = _parse_json_object_payload(
                getattr(args, "payload_json", None),
                label="pane capability payload",
            )
            _print_json(
                _run(
                    client.invoke_pane_capability(
                        namespace=namespace,
                        pane_ref=_required_text(
                            getattr(args, "pane_ref", None), "pane_ref"
                        ),
                        capability_ref=_required_text(
                            getattr(args, "capability_ref", None),
                            "capability_ref",
                        ),
                        discriminant=getattr(args, "discriminant", None),
                        request_payload=payload,
                        ensure_current_surface=_should_ensure_current_surface(args),
                        **surface_context,
                    )
                )
            )
            return 0
        if command == "act":
            payload = _parse_json_object_payload(
                getattr(args, "payload_json", None),
                label="pane action payload",
            )
            _print_json(
                _run(
                    client.invoke_pane_action(
                        namespace=namespace,
                        pane_ref=_required_text(
                            getattr(args, "pane_ref", None), "pane_ref"
                        ),
                        action_ref=_required_text(
                            getattr(args, "action_ref", None),
                            "action_ref",
                        ),
                        payload=payload,
                        ensure_current_surface=_should_ensure_current_surface(args),
                        **surface_context,
                    )
                )
            )
            return 0
        if command == "actions":
            surface = _surface_for_renderer_command(
                client=client,
                namespace=namespace,
                args=args,
                surface_context=surface_context,
            )
            _print_json(surface.surface_affordances_payload())
            return 0
        if command == "run":
            payload = _parse_json_object_payload(
                getattr(args, "payload_json", None),
                label="Interface action payload",
            )
            _print_json(
                _run(
                    client.action(
                        namespace=namespace,
                        action_key=_required_text(
                            getattr(args, "action_key", None),
                            "action_key",
                        ),
                        payload=payload,
                    )
                )
            )
            return 0
        if command == "follow":
            return _follow(client=client, namespace=namespace, args=args)
        if command == "capabilities":
            surface = _surface_for_renderer_command(
                client=client,
                namespace=namespace,
                args=args,
                surface_context=surface_context,
            )
            _print_json(surface.capabilities_payload())
            return 0
        if command == "profile":
            profile_command = str(getattr(args, "profile_command", "") or "")
            if profile_command == "select":
                _print_json(
                    _run(
                        client.select_profile(
                            namespace=namespace,
                            profile_id=_required_text(
                                getattr(args, "profile_id", None),
                                "profile_id",
                            ),
                        )
                    )
                )
                return 0
    except InterfaceHostUnavailableError as exc:
        _print_json(exc.readiness_payload(namespace=namespace, command=command))
        return 1
    raise InterfaceRendererCommandError(
        f"Unsupported Interface renderer command: {command}"
    )


def _add_interface_client_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--namespace",
        default=_default_namespace(),
        help="Interface namespace. Defaults to AWARE_INTERFACE_NAMESPACE or 'default'.",
    )
    parser.add_argument(
        "--socket-path",
        type=Path,
        help="Override the local Interface ServiceHost socket path.",
    )
    parser.add_argument(
        "--control-socket-path",
        type=Path,
        help=(
            "Override the local Interface control-plane socket path. Use this "
            "for node-hosted InterfaceHost observer mode."
        ),
    )
    parser.add_argument(
        "--state-home",
        type=Path,
        help="Override Interface service state-home used to derive the local socket path.",
    )
    ensure_group = parser.add_mutually_exclusive_group()
    ensure_group.add_argument(
        "--ensure-local-host",
        dest="ensure_local_host",
        action="store_true",
        default=None,
        help="Ensure the local Interface service host before building the SDK client.",
    )
    ensure_group.add_argument(
        "--no-ensure-local-host",
        dest="ensure_local_host",
        action="store_false",
        help="Skip local Interface service host ensure before building the SDK client.",
    )
    parser.add_argument(
        "--authority-root",
        type=Path,
        help="Shared Interface authority root for local-host service state.",
    )
    parser.add_argument(
        "--host-handle",
        help="Local Interface host handle used when deriving the shared authority.",
    )
    parser.add_argument(
        "--endpoint",
        help="Interface host node endpoint. Defaults to AWARE_INTERFACE_SERVICE_ENDPOINT.",
    )
    parser.add_argument(
        "--auth-token",
        help="Interface admission token. Defaults to AWARE_AUTH_TOKEN or AWARE_APT_TOKEN.",
    )
    parser.add_argument(
        "--interface-package-name",
        help="Interface package name to expose through the local host.",
    )
    parser.add_argument(
        "--allow-degraded-local-shell",
        dest="allow_degraded_local_shell",
        action="store_true",
        default=None,
        help="Allow local-shell fallback when live runtime bootstrap is unavailable.",
    )
    runtime_group = parser.add_mutually_exclusive_group()
    runtime_group.add_argument(
        "--require-live-runtime",
        dest="require_live_runtime",
        action="store_true",
        default=None,
        help="Require live Interface runtime bootstrap for local host ensure.",
    )
    runtime_group.add_argument(
        "--no-require-live-runtime",
        dest="require_live_runtime",
        action="store_false",
        help="Allow local host ensure to proceed without live runtime bootstrap.",
    )
    parser.add_argument(
        "--local-host-start-timeout-s",
        type=float,
        default=60.0,
        help="Seconds to wait for local Interface service host startup.",
    )
    parser.add_argument(
        "--local-host-probe-timeout-s",
        type=float,
        default=2.0,
        help="Seconds to wait for local Interface service host probes.",
    )


def _build_client(args: argparse.Namespace) -> Any:
    from aware_interface_sdk import InterfaceHostUnavailableError, InterfaceSdkClient

    namespace = _namespace(args)
    _ensure_local_host_for_args(args, namespace=namespace)
    socket_path = getattr(args, "socket_path", None)
    state_home = getattr(args, "state_home", None)
    control_socket_path = _resolve_control_socket_path_for_args(args)
    if control_socket_path is not None:
        try:
            return InterfaceSdkClient.from_local_control(
                socket_path=control_socket_path,
                state_home=state_home,
            )
        except ModuleNotFoundError as exc:
            if exc.name != "aware_interface_control":
                raise
            raise InterfaceHostUnavailableError(
                operation="interface_client_bootstrap",
                reason="local_control_adapter_not_installed",
                details=(
                    "The local Interface control adapter is not installed. "
                    "Install the Interface SDK local extras or configure an "
                    "Interface service host transport."
                ),
                socket_path=control_socket_path,
                state_home=state_home,
            ) from exc
    try:
        return InterfaceSdkClient.from_local_service_host(
            socket_path=socket_path,
            state_home=state_home,
        )
    except ModuleNotFoundError as exc:
        if exc.name != "aware_interface_service":
            raise
        raise InterfaceHostUnavailableError(
            operation="interface_client_bootstrap",
            reason="local_adapter_not_installed",
            details=(
                "The source-local Interface service host adapter is not installed. "
                "Install `aware-sdk[local]` for local Interface Host development "
                "or configure a generated Interface service API transport."
            ),
            socket_path=socket_path,
            state_home=state_home,
        ) from exc


def _resolve_control_socket_path_for_args(args: argparse.Namespace) -> Path | None:
    explicit_control_socket_path = getattr(args, "control_socket_path", None)
    if explicit_control_socket_path is not None:
        return Path(explicit_control_socket_path).expanduser().resolve()
    if getattr(args, "socket_path", None) is not None:
        return None
    if _should_ensure_local_host(args):
        return None
    value = _first_text(os.environ.get("AWARE_INTERFACE_CONTROL_SOCKET"))
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _surface_context_from_args(args: argparse.Namespace) -> dict[str, object | None]:
    return {
        "auth_token": _resolve_auth_token_arg(args),
        "endpoint": _resolve_endpoint_arg(args),
        "interface_package_name": _resolve_interface_package_name_arg(args),
    }


def _surface_for_renderer_command(
    *,
    client: Any,
    namespace: str,
    args: argparse.Namespace,
    surface_context: Mapping[str, object | None],
) -> Any:
    if getattr(args, "ensure_local_host", None) is False:
        _ = surface_context
        return _run(client.status_surface(namespace=namespace))
    return _run(client.ensure_surface(namespace=namespace, **surface_context))


def _should_ensure_current_surface(args: argparse.Namespace) -> bool:
    configured = getattr(args, "ensure_local_host", None)
    if configured is not None:
        return bool(configured)
    return _resolve_control_socket_path_for_args(args) is None


def _resolve_auth_token_arg(args: argparse.Namespace) -> str | None:
    return _first_text(
        getattr(args, "auth_token", None),
        os.environ.get("AWARE_AUTH_TOKEN"),
        os.environ.get("AWARE_APT_TOKEN"),
    )


def _resolve_endpoint_arg(args: argparse.Namespace) -> str | None:
    return _first_text(
        getattr(args, "endpoint", None),
        os.environ.get("AWARE_INTERFACE_SERVICE_ENDPOINT"),
    )


def _resolve_interface_package_name_arg(args: argparse.Namespace) -> str | None:
    declared = _first_text(
        getattr(args, "interface_package_name", None),
        os.environ.get("AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME"),
    )
    if declared is not None:
        return declared
    packages = _first_text(os.environ.get("AWARE_FLUTTER_APP_INTERFACE_PACKAGES"))
    if packages is None:
        return None
    return _first_text(packages.split(",", 1)[0])


def _first_text(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        token = str(value).strip()
        if token:
            return token
    return None


def _ensure_local_host_for_args(
    args: argparse.Namespace,
    *,
    namespace: str,
) -> dict[str, object] | None:
    from aware_interface_sdk import InterfaceHostUnavailableError

    if not _should_ensure_local_host(args):
        return None
    try:
        from aware_interface_sdk.local_host import (
            ensure_local_interface_host,
            resolve_interface_local_host_context,
        )
    except ModuleNotFoundError as exc:
        if exc.name != "aware_interface_service":
            raise
        raise InterfaceHostUnavailableError(
            operation="interface_local_host_bootstrap",
            reason="local_adapter_not_installed",
            details=(
                "The source-local Interface service host adapter is not installed. "
                "Install `aware-sdk[local]` for local Interface Host development "
                "or configure a generated Interface service API transport."
            ),
            socket_path=getattr(args, "socket_path", None),
            state_home=getattr(args, "state_home", None),
        ) from exc

    context = resolve_interface_local_host_context(
        namespace=namespace,
        socket_path=getattr(args, "socket_path", None),
        state_home=getattr(args, "state_home", None),
        authority_root=getattr(args, "authority_root", None),
        endpoint=getattr(args, "endpoint", None),
        interface_package_name=getattr(args, "interface_package_name", None),
        auth_token=getattr(args, "auth_token", None),
        allow_degraded_local_shell=getattr(args, "allow_degraded_local_shell", None),
        require_live_runtime=getattr(args, "require_live_runtime", None),
        host_handle=getattr(args, "host_handle", None),
    )
    try:
        report = _run(
            ensure_local_interface_host(
                context=context,
                start_timeout_s=float(
                    getattr(args, "local_host_start_timeout_s", 60.0)
                ),
                probe_timeout_s=float(getattr(args, "local_host_probe_timeout_s", 2.0)),
            )
        )
    except ModuleNotFoundError as exc:
        if exc.name != "aware_interface_service":
            raise
        raise InterfaceHostUnavailableError(
            operation="interface_local_host_ensure",
            reason="local_adapter_not_installed",
            details=(
                "The source-local Interface service host adapter is not installed. "
                "Install `aware-sdk[local]` for local Interface Host development "
                "or configure a generated Interface service API transport."
            ),
            socket_path=context.control_socket_path,
            state_home=context.state_home,
        ) from exc
    except Exception as exc:
        raise InterfaceHostUnavailableError(
            operation="interface_local_host_ensure",
            reason="ensure_failed",
            details=str(exc) or type(exc).__name__,
            socket_path=context.control_socket_path,
            state_home=context.state_home,
        ) from exc
    if report.get("healthy") is not True:
        raise InterfaceHostUnavailableError(
            operation="interface_local_host_ensure",
            reason=str(report.get("status") or "unhealthy"),
            details=_ensure_failure_message(report),
            socket_path=context.control_socket_path,
            state_home=context.state_home,
        )
    setattr(args, "socket_path", context.control_socket_path)
    setattr(args, "state_home", context.state_home)
    setattr(args, "_interface_local_host_ensure", report)
    return report


def _follow(*, client: Any, namespace: str, args: argparse.Namespace) -> int:
    async def _follow_loop() -> None:
        update_count = 0
        states = client.follow_states(
            namespace=namespace,
            poll_interval_ms=int(getattr(args, "poll_interval_ms", 1000)),
        )
        try:
            async for state in states:
                if update_count > 0:
                    sys.stdout.write("\n")
                _print_json(state)
                update_count += 1
                if getattr(args, "once", False):
                    break
        finally:
            aclose = getattr(states, "aclose", None)
            if callable(aclose):
                await cast(Callable[[], Awaitable[None]], aclose)()

    coro = _follow_loop()
    try:
        _run(coro)
    except KeyboardInterrupt:  # pragma: no cover - terminal behavior
        coro.close()
        return 130
    return 0


def _run(value: Any) -> Any:
    return asyncio.run(value)


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


def _with_local_host_ensure(
    args: argparse.Namespace,
    payload: Mapping[str, object],
) -> dict[str, object]:
    ensure = getattr(args, "_interface_local_host_ensure", None)
    if ensure is None:
        return dict(payload)
    return {**dict(payload), "interface_local_host_ensure": ensure}


def _should_ensure_local_host(args: argparse.Namespace) -> bool:
    configured = getattr(args, "ensure_local_host", None)
    if configured is not None:
        return bool(configured)
    if getattr(args, "control_socket_path", None) is not None:
        return False
    if getattr(args, "socket_path", None) is None and _first_text(
        os.environ.get("AWARE_INTERFACE_CONTROL_SOCKET")
    ):
        return False
    env_value = str(
        os.environ.get("AWARE_INTERFACE_SDK_ENSURE_LOCAL_HOST") or ""
    ).strip()
    if env_value:
        return _parse_env_bool(
            env_value,
            env_name="AWARE_INTERFACE_SDK_ENSURE_LOCAL_HOST",
        )
    return getattr(args, "socket_path", None) is None


def _parse_env_bool(value: str, *, env_name: str) -> bool:
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise InterfaceRendererCommandError(
        f"Unsupported boolean value for {env_name}: {value!r}."
    )


def _ensure_failure_message(report: Mapping[str, object]) -> str:
    blocking_warnings = report.get("blocking_warnings")
    warnings = report.get("warnings")
    status = report.get("status") or "unhealthy"
    return (
        f"Interface local host ensure returned {status}. "
        f"blocking_warnings={blocking_warnings!r}; warnings={warnings!r}"
    )


def _parse_json_object_payload(
    raw: str | None, *, label: str
) -> dict[str, object] | None:
    if raw is None:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise InterfaceRendererCommandError(f"{label} must decode to a JSON object.")
    return parsed


def _namespace(args: argparse.Namespace) -> str:
    return _required_text(getattr(args, "namespace", None), "--namespace")


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise InterfaceRendererCommandError(
            f"Missing required Interface renderer value: {label}."
        )
    return text


def _default_namespace() -> str:
    return (
        str(os.environ.get("AWARE_INTERFACE_NAMESPACE") or "").strip()
        or _DEFAULT_NAMESPACE
    )


__all__ = [
    "handle_interface_renderer_command",
    "register_interface_renderer_parsers",
]
