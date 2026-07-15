"""Identity SDK dogfood commands for the transitional aware-sdk rail."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
)

_DEFAULT_NAMESPACE = "default"


class IdentityCommandError(RuntimeError):
    """Raised when an Identity command cannot be executed from client inputs."""


@dataclass(frozen=True, slots=True)
class _IdentityInterfaceOptions:
    namespace: str
    auth_token: str | None
    endpoint: str | None
    host_label: str | None
    environment_config_id: UUID | None


@dataclass(frozen=True, slots=True)
class _InterfaceApiEndpointTransport:
    interface_client: Any
    namespace: str

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        _ = timeout_s
        response = await self.interface_client.invoke_api_endpoint(
            namespace=self.namespace,
            endpoint_ref=invocation.endpoint_ref,
            discriminant=invocation.discriminant,
            request_payload=dict(invocation.request_payload),
        )
        status = _api_status_from_interface_response(response)
        return ApiEndpointResponse(
            status=status,
            response_payload=response.response_payload,
            error=response.error if status == "failed" else None,
        )


def register_identity_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register hidden Identity SDK dogfood commands."""

    identity_parser = subparsers.add_parser(
        "identity",
        help="Transitional Identity admission diagnostics/bootstrap.",
        description=(
            "Transitional Identity admission diagnostics/bootstrap commands. "
            "Durable product workflows should use Interface panes."
        ),
    )
    identity_subparsers = identity_parser.add_subparsers(dest="identity_command")

    status_parser = identity_subparsers.add_parser(
        "status",
        help="Describe Identity SDK diagnostic readiness.",
    )
    _add_identity_interface_options(status_parser)
    status_parser.set_defaults(identity_action="status")

    human_parser = identity_subparsers.add_parser(
        "admit-human",
        help="Admit a human Identity + Actor through aware-identity-sdk.",
    )
    _add_identity_interface_options(human_parser)
    _add_identity_profile_options(human_parser)
    human_parser.set_defaults(identity_action="admit_human")

    agent_parser = identity_subparsers.add_parser(
        "admit-agent",
        help="Admit an agent Identity + Actor through aware-identity-sdk.",
    )
    _add_identity_interface_options(agent_parser)
    _add_identity_profile_options(agent_parser)
    agent_parser.set_defaults(identity_action="admit_agent")


def handle_identity_command(args: argparse.Namespace) -> int:
    """Execute one hidden Identity command from parsed aware-sdk CLI args."""

    from aware_interface_sdk import InterfaceHostUnavailableError

    action = getattr(args, "identity_action", None)
    try:
        if action == "status":
            _print_json(_identity_status_payload(args))
            return 0
        if action == "admit_human":
            _print_json(_run(_admit_identity(args, identity_kind="human")))
            return 0
        if action == "admit_agent":
            _print_json(_run(_admit_identity(args, identity_kind="agent")))
            return 0
    except InterfaceHostUnavailableError as exc:
        _print_json(
            exc.readiness_payload(
                namespace=_identity_interface_options(args).namespace,
                command="identity",
            )
        )
        return 1
    raise IdentityCommandError(
        "Identity command required. Try `aware identity admit-human --help`."
    )


async def _admit_identity(
    args: argparse.Namespace,
    *,
    identity_kind: str,
) -> Mapping[str, Any]:
    from aware_identity_sdk import IdentityAdmissionProfile

    interface_options = _identity_interface_options(args)
    interface_client = _build_interface_client(args)
    ensured = await interface_client.ensure_namespace(
        namespace=interface_options.namespace,
        auth_token=interface_options.auth_token,
        endpoint=interface_options.endpoint,
        host_label=interface_options.host_label,
        environment_config_id=interface_options.environment_config_id,
    )
    identity_client = _build_identity_sdk_client(
        interface_client=interface_client,
        namespace=interface_options.namespace,
    )
    profile = IdentityAdmissionProfile(
        display_name=_required_text(args.display_name, "--display-name"),
        public_handle=_required_text(args.public_handle, "--public-handle"),
        full_name=_optional_text(args.full_name)
        or _required_text(args.display_name, "--display-name"),
        country_code=_required_text(args.country_code, "--country-code"),
        language_code=_required_text(args.language_code, "--language-code"),
        bio=_optional_text(args.bio),
    )
    request_id = _optional_uuid(args.request_id, "--request-id")
    if identity_kind == "human":
        admission = await identity_client.admit_human(
            public_key=_required_text(args.public_key, "--public-key"),
            profile=profile,
            request_id=request_id,
            source="aware_sdk.identity",
        )
    elif identity_kind == "agent":
        admission = await identity_client.admit_agent_identity(
            public_key=_required_text(args.public_key, "--public-key"),
            profile=profile,
            request_id=request_id,
            source="aware_sdk.identity",
        )
    else:  # pragma: no cover - argparse controls this.
        raise IdentityCommandError(f"Unsupported identity kind: {identity_kind}")

    transport = ensured.host_state.transport
    gate = identity_client.build_gate_snapshot(
        admission=admission,
        authenticated=transport.authenticated,
        authenticated_actor_id=transport.actor_id,
    )
    return {
        "identity": {
            "identity_id": admission.identity_id,
            "actor_id": admission.actor_id,
            "identity_profile_id": admission.identity_profile_id,
            "public_handle": admission.public_handle,
            "identity_type": admission.identity_type.value,
            "info": admission.info,
        },
        "gate": {
            "status": gate.status.value,
            "crossed": gate.crossed,
            "expected_actor_id": gate.expected_actor_id,
            "authenticated_actor_id": gate.authenticated_actor_id,
            "reason": gate.reason,
        },
        "api_boundary": _identity_api_boundary_payload(),
        "interface": {
            "namespace": ensured.namespace,
            "host_label": ensured.host_state.host_label,
            "transport_authenticated": transport.authenticated,
        },
    }


def _build_identity_sdk_client(
    *,
    interface_client: Any,
    namespace: str,
) -> Any:
    from aware_identity_service_api import AwareIdentityServiceApiClient
    from aware_identity_sdk import IdentitySdkClient

    transport = _InterfaceApiEndpointTransport(
        interface_client=interface_client,
        namespace=namespace,
    )
    generated_client = AwareIdentityServiceApiClient(AwareApiEndpointInvoker(transport))
    return IdentitySdkClient(generated_client)


def _build_interface_client(args: argparse.Namespace) -> Any:
    from aware_interface_sdk import InterfaceHostUnavailableError, InterfaceSdkClient

    socket_path = getattr(args, "socket_path", None)
    state_home = getattr(args, "state_home", None)
    try:
        return InterfaceSdkClient.from_local_control(
            socket_path=socket_path,
            state_home=state_home,
        )
    except ModuleNotFoundError as exc:
        if exc.name != "aware_interface_control":
            raise
        raise InterfaceHostUnavailableError(
            operation="interface_client_bootstrap",
            reason="local_adapter_not_installed",
            details=(
                "The source-local Interface control adapter is not installed. "
                "Install `aware-sdk[local]` for local Interface Host development "
                "or configure a generated Interface service API transport."
            ),
            socket_path=socket_path,
            state_home=state_home,
        ) from exc


def _identity_status_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    options = _identity_interface_options(args)
    return {
        "identity": {
            "ready": True,
            "namespace": options.namespace,
            "interface_endpoint": options.endpoint,
            "auth_token_present": options.auth_token is not None,
            "host_label": options.host_label,
            "environment_config_id": options.environment_config_id,
        },
        "api_boundary": _identity_api_boundary_payload(),
        "commands": {
            "admit_human": {
                "status": "available",
                "route": (
                    "aware-sdk -> aware-identity-sdk -> generated Identity API "
                    "-> Interface API ingress"
                ),
            },
            "admit_agent": {
                "status": "available",
                "agent_process_thread_creation": "not-owned-by-identity",
            },
        },
    }


def _identity_api_boundary_payload() -> Mapping[str, Any]:
    return {
        "kind": "sdk-over-generated-api-client",
        "sdk_package": "aware-identity-sdk",
        "sdk_package_version": _safe_version("aware-identity-sdk"),
        "generated_api_package": "aware_identity_service_api",
        "generated_api_package_version": _safe_version("aware_identity_service_api"),
        "transport": "interface-api-ingress",
        "service_imports_allowed": False,
        "agent_process_thread_owner": "agent-service",
    }


def _add_identity_interface_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--namespace",
        default=_default_namespace(),
        help="Interface namespace. Defaults to AWARE_INTERFACE_NAMESPACE or 'default'.",
    )
    parser.add_argument(
        "--socket-path",
        type=Path,
        help="Override the local Interface control socket path.",
    )
    parser.add_argument(
        "--state-home",
        type=Path,
        help="Override Interface service state-home used to derive the local socket path.",
    )
    parser.add_argument("--auth-token", help="Optional Interface namespace auth token.")
    parser.add_argument(
        "--endpoint", help="Optional Interface namespace endpoint override."
    )
    parser.add_argument("--host-label", help="Optional Interface namespace host label.")
    parser.add_argument(
        "--environment-config-id",
        help="Optional Interface namespace environment config UUID.",
    )


def _add_identity_profile_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--public-handle", required=True)
    parser.add_argument("--full-name")
    parser.add_argument("--country-code", default="US")
    parser.add_argument("--language-code", default="en")
    parser.add_argument("--bio")
    parser.add_argument("--request-id")


def _identity_interface_options(args: argparse.Namespace) -> _IdentityInterfaceOptions:
    return _IdentityInterfaceOptions(
        namespace=_required_text(getattr(args, "namespace", None), "--namespace"),
        auth_token=_optional_text(getattr(args, "auth_token", None)),
        endpoint=_optional_text(getattr(args, "endpoint", None)),
        host_label=_optional_text(getattr(args, "host_label", None)),
        environment_config_id=_optional_uuid(
            getattr(args, "environment_config_id", None),
            "--environment-config-id",
        ),
    )


def _run(coro: Any) -> Mapping[str, Any]:
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt as exc:  # pragma: no cover - terminal behavior
        raise IdentityCommandError("Identity command interrupted.") from exc


def _print_json(payload: Mapping[str, Any]) -> None:
    json.dump(_jsonable(dict(payload)), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _jsonable(value: Any) -> Any:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _api_status_from_interface_response(response: Any) -> str:
    if not bool(getattr(response, "success", False)):
        return "failed"
    service_status = str(getattr(response, "service_status", "") or "").strip().lower()
    if service_status in {"", "ok", "success", "succeeded"}:
        return "succeeded"
    if service_status == "pending":
        return "pending"
    return "failed"


def _optional_uuid(raw: object, label: str) -> UUID | None:
    text = _optional_text(raw)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError as exc:
        raise IdentityCommandError(f"{label} must be a UUID.") from exc


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_text(value: object, label: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise IdentityCommandError(f"Missing required Identity value: {label}.")
    return text


def _default_namespace() -> str:
    return (
        str(os.environ.get("AWARE_INTERFACE_NAMESPACE") or "").strip()
        or _DEFAULT_NAMESPACE
    )


def _safe_version(distribution_name: str) -> str | None:
    try:
        return version(distribution_name)
    except PackageNotFoundError:
        return None


__all__ = [
    "handle_identity_command",
    "register_identity_parser",
]
