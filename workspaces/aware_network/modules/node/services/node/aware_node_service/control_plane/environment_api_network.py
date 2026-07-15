from __future__ import annotations

from uuid import UUID, uuid4

from aware_api import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointTransport,
    AwareApiEndpointInvoker,
)
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
)
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequest,
    NetworkRequestStatus,
)

from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
)


class EnvironmentApiEndpointTransport(ApiEndpointTransport):
    """Node-owned transport for generated Environment API clients."""

    def __init__(
        self,
        *,
        route_to_environment_service: EnvironmentRouteHandler,
        environment_id: UUID,
        node_id: UUID,
        actor_id: UUID | None,
        default_timeout_s: float | None = None,
    ) -> None:
        self._route_to_environment_service = route_to_environment_service
        self._environment_id = environment_id
        self._node_id = node_id
        self._actor_id = actor_id
        self._default_timeout_s = default_timeout_s

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        request_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=NetworkRequest(requester_id=self._actor_id),
            api_operation=ApiOperation(
                request=InvokeApiEndpointRequest(
                    actor_id=self._actor_id,
                    endpoint_ref=invocation.endpoint_ref,
                    discriminant=invocation.discriminant,
                    request_payload=invocation.request_payload,
                )
            ),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=self._node_id,
                    target_app_type=NetworkAppType.environment,
                    target_environment_id=self._environment_id,
                )
            ],
        )
        response_op = await self._route_to_environment_service(
            request_op,
            timeout_s=timeout_s if timeout_s is not None else self._default_timeout_s,
        )
        return _api_endpoint_response_from_network_operation(
            response=response_op,
            label=invocation.endpoint_ref,
        )


def build_environment_service_api_client(
    *,
    route_to_environment_service: EnvironmentRouteHandler,
    environment_id: UUID,
    node_id: UUID,
    actor_id: UUID | None,
    default_timeout_s: float | None = None,
) -> AwareEnvironmentServiceApiClient:
    return AwareEnvironmentServiceApiClient(
        client=AwareApiEndpointInvoker(
            EnvironmentApiEndpointTransport(
                route_to_environment_service=route_to_environment_service,
                environment_id=environment_id,
                node_id=node_id,
                actor_id=actor_id,
                default_timeout_s=default_timeout_s,
            )
        )
    )


def _api_endpoint_response_from_network_operation(
    *,
    response: NetworkOperation | None,
    label: str,
) -> ApiEndpointResponse:
    if response is None:
        raise RuntimeError(f"{label}: missing Environment API network response")
    network_response = response.network_response
    if network_response is None:
        raise RuntimeError(f"{label}: missing network_response")
    if network_response.status == NetworkRequestStatus.failed:
        return ApiEndpointResponse(
            status=ApiRequestStatus.failed.value,
            error=network_response.error or "unknown network error",
        )
    api_response = (
        response.api_operation.response if response.api_operation is not None else None
    )
    if not isinstance(api_response, InvokeApiEndpointResponse):
        raise RuntimeError(f"{label}: missing API endpoint response")
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


__all__ = [
    "EnvironmentApiEndpointTransport",
    "build_environment_service_api_client",
    "invoke_environment_service_api_request",
]


async def invoke_environment_service_api_request(
    client: AwareEnvironmentServiceApiClient,
    request: object,
) -> object:
    operation = str(getattr(request, "operation", "") or "").strip()
    if operation == "apply_program_ref":
        return await client.environment.program_ref.apply_program_ref(request)
    if operation == "configure_service_api_dependency_routes":
        return await client.environment.service_routes.configure_service_api_dependency_routes(
            request
        )
    if operation == "describe_environment":
        return await client.environment.describe.describe_environment(request)
    if operation == "describe_environment_config":
        return await client.environment.describe_config.describe_environment_config(
            request
        )
    if operation == "describe_environment_status":
        return await client.environment.status.describe_environment_status(request)
    if operation == "describe_environment_topology":
        return await client.environment.topology.describe_environment_topology(request)
    if operation == "ensure_ready":
        return await client.environment.ready.ensure_ready(request)
    if operation == "fetch_capabilities":
        return await client.environment.capabilities.fetch_capabilities(request)
    if operation == "get_lane_head":
        return await client.environment.lane_head.get_lane_head(request)
    if operation == "get_object_instance_graph_commit":
        return await client.environment.object_instance_graph_commit.get_object_instance_graph_commit(
            request
        )
    if operation == "get_turn_execution":
        return await client.environment.turn_execution.get_turn_execution(request)
    if operation == "invoke_function":
        return await client.environment.function_call.invoke_function(request)
    if operation == "provision_environment_profile":
        return await client.environment.profile.provision_environment_profile(request)
    if operation == "resolve_runtime_refs":
        return await client.environment.runtime_ref.resolve_runtime_refs(request)
    if operation == "run_program":
        return await client.environment.program.run_program(request)
    if operation == "submit_program_turn":
        return await client.environment.program_turn.submit_program_turn(request)
    if operation == "upsert_environment_profile":
        return await client.environment.profile.upsert_environment_profile(request)
    raise RuntimeError(
        f"Unsupported Environment API operation: {operation or '<missing>'}"
    )
