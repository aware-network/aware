from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    AwareApiEndpointInvoker,
)
from aware_service_runtime.api_endpoint_duplex import ApiEndpointDuplexClient
from aware_environment_sdk import EnvironmentGeneratedApiClient
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequest,
    NetworkRequestStatus,
)

from aware_service_service.app import ServiceHostApp
from aware_service_service.config import (
    ServiceHostAppConfig,
    ServiceHostBootstrapConfig,
)

LOCAL_ENVIRONMENT_API_ENDPOINT = "aware-environment-service://local"
_REMOTE_ENVIRONMENT_API_SOURCE_NODE_ID = uuid5(
    NAMESPACE_URL,
    "aware:service-host:environment-api:source-node",
)


@dataclass(slots=True)
class _EnvironmentServiceEndpointTransport:
    endpoint: str
    request_timeout_s: float
    source_node_id: UUID = _REMOTE_ENVIRONMENT_API_SOURCE_NODE_ID
    _duplex: ApiEndpointDuplexClient | None = None

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        environment_id = _required_environment_id(invocation=invocation)
        actor_id = _optional_uuid(dict(invocation.request_payload).get("actor_id"))
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=NetworkRequest(requester_id=actor_id),
            api_operation=ApiOperation(
                request=InvokeApiEndpointRequest(
                    actor_id=actor_id,
                    endpoint_ref=invocation.endpoint_ref,
                    discriminant=invocation.discriminant,
                    request_payload=dict(invocation.request_payload),
                )
            ),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=self.source_node_id,
                    target_app_type=NetworkAppType.environment,
                    target_environment_id=environment_id,
                )
            ],
        )
        duplex = await self._ensure_duplex()
        raw_response = await duplex.send_request(
            connection_id=duplex.connection_id,
            data_serialized=network_op.model_dump_json(),
            timeout_s=timeout_s or self.request_timeout_s,
        )
        response_op = _parse_network_operation_response(raw_response)
        network_response = response_op.network_response
        if network_response is None:
            return ApiEndpointResponse(
                status="failed",
                error="Environment API endpoint response missing network_response.",
            )
        if network_response.status == NetworkRequestStatus.failed:
            return ApiEndpointResponse(
                status="failed",
                error=network_response.error or "Environment API endpoint failed.",
            )
        api_response = (
            response_op.api_operation.response
            if response_op.api_operation is not None
            else None
        )
        if not isinstance(api_response, InvokeApiEndpointResponse):
            return ApiEndpointResponse(
                status="failed",
                error="Environment API endpoint response missing API payload.",
            )
        return ApiEndpointResponse(
            status=getattr(api_response.status, "value", str(api_response.status)),
            response_payload=api_response.response_payload,
            error=api_response.error,
            stream_lifecycle=getattr(
                api_response.stream_lifecycle,
                "value",
                str(api_response.stream_lifecycle),
            ),
        )

    async def _ensure_duplex(self) -> ApiEndpointDuplexClient:
        if self._duplex is not None:
            return self._duplex
        duplex = ApiEndpointDuplexClient(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.network_node.value,
            endpoint=self.endpoint,
            request_timeout=self.request_timeout_s,
        )
        await duplex.ensure_connection(
            duplex.connection_id,
            external_url=self.endpoint,
        )
        self._duplex = duplex
        return duplex


def build_environment_api_client_for_service_host_config(
    *,
    config: ServiceHostAppConfig,
) -> EnvironmentGeneratedApiClient | None:
    endpoint = _normalized_endpoint(config.environment.api_endpoint)
    if endpoint is None:
        return None
    if endpoint != LOCAL_ENVIRONMENT_API_ENDPOINT:
        return AwareEnvironmentServiceApiClient(
            AwareApiEndpointInvoker(
                _EnvironmentServiceEndpointTransport(
                    endpoint=_normalize_environment_service_endpoint(endpoint),
                    request_timeout_s=config.environment.request_timeout_s,
                )
            )
        )
    try:
        from aware_environment_service import build_local_environment_service_api_client
        from aware_environment_service.app import EnvironmentServiceApp
    except ImportError as exc:
        raise RuntimeError(
            "ServiceHost local Environment API endpoint requires the "
            "aware-environment-service package to be installed."
        ) from exc
    environment_app = EnvironmentServiceApp()
    return build_local_environment_service_api_client(app=environment_app)


def build_service_host_app(
    *,
    config: ServiceHostAppConfig,
) -> ServiceHostApp:
    return ServiceHostApp(
        config=config,
        environment_api_client=build_environment_api_client_for_service_host_config(
            config=config,
        ),
    )


def build_service_host_app_from_bootstrap_config(
    *,
    config: ServiceHostBootstrapConfig,
) -> ServiceHostApp:
    return build_service_host_app(config=config.app)


def _normalized_endpoint(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _normalize_environment_service_endpoint(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("Environment API endpoint is required.")
    if "://" not in raw:
        raw = f"ws://{raw}"
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        parsed = parsed._replace(scheme="ws")
    elif scheme == "https":
        parsed = parsed._replace(scheme="wss")
    elif scheme not in {"ws", "wss"}:
        raise ValueError(
            "Unsupported Environment API endpoint scheme "
            f"{parsed.scheme!r}; expected ws, wss, http, or https."
        )
    path = parsed.path.rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if path.endswith(suffix):
            path = path[: -len(suffix)].rstrip("/")
            break
    parsed = parsed._replace(path=path, params="", query="", fragment="")
    return urlunparse(parsed)


def _required_environment_id(*, invocation: ApiEndpointInvocation) -> UUID:
    payload = dict(invocation.request_payload)
    value = payload.get("environment_id")
    if value is None:
        raise RuntimeError(
            "Environment API endpoint request payload requires environment_id "
            f"for endpoint_ref={invocation.endpoint_ref!r}."
        )
    return UUID(str(value))


def _optional_uuid(value: object) -> UUID | None:
    if value is None or value == "":
        return None
    return UUID(str(value))


def _parse_network_operation_response(raw_response: object) -> NetworkOperation:
    if isinstance(raw_response, NetworkOperation):
        return raw_response
    if isinstance(raw_response, str):
        return NetworkOperation.model_validate_json(raw_response)
    if isinstance(raw_response, dict):
        return NetworkOperation.model_validate(raw_response)
    raise TypeError(
        "Environment API endpoint returned unsupported NetworkOperation payload "
        f"type: {type(raw_response)}"
    )


__all__ = [
    "LOCAL_ENVIRONMENT_API_ENDPOINT",
    "build_environment_api_client_for_service_host_config",
    "build_service_host_app",
    "build_service_host_app_from_bootstrap_config",
]
