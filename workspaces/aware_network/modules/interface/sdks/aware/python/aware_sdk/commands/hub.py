"""Hub API commands for the public aware-sdk product rail."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING
from typing import Any
from uuid import UUID

from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
)

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from aware_hub_service_api import AwareHubServiceApiClient


_ENDPOINT_ENVS = ("AWARE_HUB_API_ENDPOINT", "AWARE_API_ENDPOINT")
_ACTOR_ID_ENVS = ("AWARE_ACTOR_ID", "AWARE_INTERFACE_ACTOR_ID")
_SESSION_TOKEN_ENVS = ("AWARE_AUTH_TOKEN", "AWARE_APT_TOKEN", "AWARE_API_TOKEN")


class HubCommandError(RuntimeError):
    """Raised when a Hub command cannot be executed from client inputs."""


@dataclass(frozen=True, slots=True)
class _ConfigValue:
    value: str | None
    source: str | None


@dataclass(frozen=True, slots=True)
class _HubClientConfigStatus:
    endpoint: _ConfigValue
    actor_id_value: _ConfigValue
    actor_id: UUID | None
    session_token: _ConfigValue
    request_timeout: float
    errors: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.errors


@dataclass(frozen=True, slots=True)
class _HubClientConfig:
    endpoint: str
    actor_id: UUID
    session_token: str | None
    request_timeout: float


def register_hub_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the Hub command pack on an aware-sdk parser."""

    hub_parser = subparsers.add_parser(
        "hub",
        help="Transitional Hub diagnostics/bootstrap.",
        description=(
            "Transitional Hub diagnostics/bootstrap commands. Product workflows "
            "must use root Interface renderer commands."
        ),
    )
    hub_subparsers = hub_parser.add_subparsers(dest="hub_command")

    status_parser = hub_subparsers.add_parser(
        "status",
        help="Describe Hub client configuration readiness.",
    )
    _add_hub_client_options(status_parser)
    status_parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero when required Hub client config is missing or invalid.",
    )
    status_parser.set_defaults(hub_action="status")

    workspace_deployment_parser = hub_subparsers.add_parser(
        "workspace-deployment",
        help="Resolve WorkspaceDeployment authority revisions through Hub.",
    )
    workspace_deployment_subparsers = workspace_deployment_parser.add_subparsers(
        dest="hub_workspace_deployment_command"
    )
    resolve_parser = workspace_deployment_subparsers.add_parser(
        "resolve",
        help="Resolve one workspace-deployment revision through the Hub API.",
    )
    _add_hub_client_options(resolve_parser)
    resolve_parser.add_argument("--artifact-key")
    resolve_parser.add_argument("--channel", default="stable")
    resolve_parser.add_argument("--revision-id")
    resolve_parser.add_argument("--authority-base-url")
    resolve_parser.add_argument("--index-url")
    resolve_parser.set_defaults(hub_action="workspace_deployment_resolve")


def handle_hub_command(args: argparse.Namespace) -> int:
    """Execute a Hub command from parsed aware-sdk CLI args."""

    action = getattr(args, "hub_action", None)
    if action == "status":
        payload = _hub_status_payload(args)
        _print_json(payload)
        return (
            1
            if getattr(args, "require_ready", False) and not payload["hub"]["ready"]
            else 0
        )
    if action == "workspace_deployment_resolve":
        payload = _run(_resolve_workspace_deployment(args))
        _print_json(payload)
        return 0
    raise HubCommandError(
        "Hub command required. Try `aware hub workspace-deployment resolve --help`."
    )


async def _resolve_workspace_deployment(args: argparse.Namespace) -> dict[str, Any]:

    config = _resolve_required_hub_client_config(args)
    _validate_workspace_deployment_selector(args)
    client = _build_hub_api_client(
        endpoint=config.endpoint,
        actor_id=config.actor_id,
        session_token=config.session_token,
        request_timeout=config.request_timeout,
    )
    request = ResolveDeploymentArtifactRequest(
        artifact_key=_optional_text(args.artifact_key),
        channel=_required_text(args.channel, "--channel"),
        revision_id=_optional_text(args.revision_id),
        authority_base_url=_optional_text(args.authority_base_url),
        index_url=_optional_text(args.index_url),
    )
    response = await client.hub.deployment_artifact.resolve(request)
    return _model_to_jsonable(response)


def _build_hub_api_client(
    *,
    endpoint: str,
    actor_id: UUID,
    session_token: str | None,
    request_timeout: float,
) -> "AwareHubServiceApiClient":
    from aware_api.client import AwareApiClient, AwareApiConfig
    from aware_hub_service_api import AwareHubServiceApiClient

    return AwareHubServiceApiClient(
        AwareApiClient(
            AwareApiConfig(
                endpoint=endpoint,
                actor_id=actor_id,
                session_token=session_token,
                request_timeout=request_timeout,
            )
        )
    )


def _add_hub_client_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--endpoint",
        help="Hub API endpoint. Defaults to AWARE_HUB_API_ENDPOINT or AWARE_API_ENDPOINT.",
    )
    parser.add_argument(
        "--actor-id",
        help="Actor UUID for the API request. Defaults to AWARE_ACTOR_ID.",
    )
    parser.add_argument(
        "--session-token",
        help="Optional bearer/session token. Defaults to AWARE_AUTH_TOKEN / AWARE_APT_TOKEN.",
    )
    parser.add_argument("--request-timeout", type=float, default=10.0)


def _run(coro: "Coroutine[Any, Any, Mapping[str, Any]]") -> Mapping[str, Any]:
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt as exc:  # pragma: no cover - terminal behavior
        raise HubCommandError("Hub command interrupted.") from exc


def _print_json(payload: Mapping[str, Any]) -> None:
    json.dump(dict(payload), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def _hub_status_payload(args: argparse.Namespace) -> dict[str, Any]:
    status = _resolve_hub_client_config_status(args)
    return {
        "hub": {
            "ready": status.ready,
            "endpoint": status.endpoint.value,
            "endpoint_source": status.endpoint.source,
            "actor_id": (
                str(status.actor_id)
                if status.actor_id is not None
                else status.actor_id_value.value
            ),
            "actor_id_source": status.actor_id_value.source,
            "actor_id_valid": status.actor_id is not None,
            "session_token_present": status.session_token.value is not None,
            "session_token_source": status.session_token.source,
            "request_timeout": status.request_timeout,
            "errors": list(status.errors),
        },
        "api_boundary": {
            "kind": "generated-api-client",
            "package": "aware_hub_service_api",
            "package_version": _safe_version("aware_hub_service_api"),
            "service_imports_allowed": False,
        },
        "commands": {
            "workspace_deployment_resolve": {
                "status": "available",
                "requires": [
                    "endpoint",
                    "actor_id",
                    "index_url or authority_base_url + artifact_key",
                ],
            }
        },
    }


def _resolve_required_hub_client_config(args: argparse.Namespace) -> _HubClientConfig:
    status = _resolve_hub_client_config_status(args)
    if not status.ready or status.actor_id is None or status.endpoint.value is None:
        raise HubCommandError("Hub client is not ready: " + "; ".join(status.errors))
    return _HubClientConfig(
        endpoint=status.endpoint.value,
        actor_id=status.actor_id,
        session_token=status.session_token.value,
        request_timeout=status.request_timeout,
    )


def _resolve_hub_client_config_status(
    args: argparse.Namespace,
) -> _HubClientConfigStatus:
    endpoint = _resolve_config_value(args, "endpoint", _ENDPOINT_ENVS)
    actor_id_value = _resolve_config_value(args, "actor_id", _ACTOR_ID_ENVS)
    session_token = _resolve_config_value(args, "session_token", _SESSION_TOKEN_ENVS)
    errors: list[str] = []

    actor_id: UUID | None = None
    if actor_id_value.value is None:
        errors.append(
            "missing actor id: pass --actor-id or set AWARE_ACTOR_ID "
            "or AWARE_INTERFACE_ACTOR_ID"
        )
    else:
        try:
            actor_id = UUID(actor_id_value.value)
        except ValueError:
            errors.append(f"invalid actor id UUID: {actor_id_value.value!r}")

    if endpoint.value is None:
        errors.append(
            "missing endpoint: pass --endpoint or set AWARE_HUB_API_ENDPOINT "
            "or AWARE_API_ENDPOINT"
        )

    raw_timeout = getattr(args, "request_timeout", 10.0)
    request_timeout = 10.0 if raw_timeout is None else float(raw_timeout)
    if request_timeout <= 0:
        errors.append("request timeout must be greater than zero")

    return _HubClientConfigStatus(
        endpoint=endpoint,
        actor_id_value=actor_id_value,
        actor_id=actor_id,
        session_token=session_token,
        request_timeout=request_timeout,
        errors=tuple(errors),
    )


def _resolve_config_value(
    args: argparse.Namespace,
    attr: str,
    env_names: tuple[str, ...],
) -> _ConfigValue:
    explicit = _optional_text(getattr(args, attr, None))
    if explicit is not None:
        return _ConfigValue(value=explicit, source="argument")
    value, env_name = _env(env_names)
    if value is not None:
        return _ConfigValue(value=value, source=f"env:{env_name}")
    return _ConfigValue(value=None, source=None)


def _validate_workspace_deployment_selector(args: argparse.Namespace) -> None:
    index_url = _optional_text(getattr(args, "index_url", None))
    if index_url is not None:
        return
    authority_base_url = _optional_text(getattr(args, "authority_base_url", None))
    artifact_key = _optional_text(getattr(args, "artifact_key", None))
    if authority_base_url is None or artifact_key is None:
        raise HubCommandError(
            "WorkspaceDeployment resolution requires --index-url or both "
            "--authority-base-url and --artifact-key."
        )


def _model_to_jsonable(value: Any) -> dict[str, Any]:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, dict):
            return dumped
    if isinstance(value, Mapping):
        return dict(value)
    raise HubCommandError(
        f"Hub API returned an unsupported response type: {type(value).__name__}"
    )


def _safe_version(distribution_name: str) -> str | None:
    try:
        return version(distribution_name)
    except PackageNotFoundError:
        return None


def _env(names: tuple[str, ...]) -> tuple[str | None, str | None]:
    for name in names:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip(), name
    return None, None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: object, label: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise HubCommandError(f"Missing required Hub client value: {label}.")
    return text


def _parse_uuid(value: object, label: str) -> UUID:
    text = _required_text(value, label)
    try:
        return UUID(text)
    except ValueError as exc:
        raise HubCommandError(f"{label} must be a UUID: {text!r}.") from exc
