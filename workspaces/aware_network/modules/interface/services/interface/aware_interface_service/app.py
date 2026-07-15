from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from datetime import datetime, timezone
import inspect
import json
import os
import signal
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Mapping,
    Protocol,
    Sequence,
    cast,
)
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import PrivateAttr

from aware_api.context import AwareApiContext
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointStream,
    AwareApiEndpointInvoker,
)
from aware_code.types import JsonObject, JsonValue
from aware_comms import DuplexIpcEndpoint
from aware_environment_service_api import AwareEnvironmentServiceApiClient
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentConfigRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyRequest,
)
from aware_environment_service_dto.environment.environment import (
    FetchCapabilitiesRequest,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt,
)
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_dto.experience.program.service_operation import (
    ApplyProgramRefRequest,
)
from aware_experience_service_dto.experience.actor_admission.models import (
    ExperienceActorConfigAdmissionReceipt,
)
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
    StreamApiEndpointRequest,
)
from aware_node_sdk import AwareNodeSdk, NodeSdkCache
from aware_node_service_api import AwareNodeServiceApiClient
from aware_interface import (
    InterfaceHostRuntime,
    EnvironmentInterfaceGatePort,
)
from aware_interface.host_runtime import (
    load_committed_interface_config_bundle_from_package_ref,
    load_workspace_interface_config_bundle,
)
from aware_interface.package_ref_resolution import InterfaceRuntimePackageRef
from aware_interface.session_port import (
    InterfaceBootstrapResult,
    InterfaceRuntimeSessionPort,
)
from aware_interface.session_state import InterfaceRuntimeSessionStateStore
from aware_interface.session_target import (
    InterfaceSessionTarget,
    resolve_interface_session_target,
    resolve_interface_session_target_coordinates,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_service.host.capabilities.attention import (
    AttentionLayoutIntentSection,
    AttentionLayoutTopologyIntentSection,
)
from aware_interface_sdk.attachment import (
    InterfaceAttachment,
    create_interface_attachment,
)
from aware_interface_sdk.auth_store import (
    InterfaceAuthSession,
    load_interface_auth_session,
    save_interface_auth_session,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_service_runtime.contracts import (
    ServiceHostApiIngressRequest,
    ServiceStreamEventEnvelope,
    ServiceStreamEventKind,
    ServiceStreamSession,
)
from aware_service_runtime.duplex import (
    ServiceDuplexStreamEvent,
    ServiceDuplexStreamEventEnvelope,
)
from aware_service_runtime.duplex_client import (
    ServiceHostDuplexClient,
    ServiceHostDuplexRequestHandle,
)
from aware_service_runtime.api_endpoint_duplex import ApiEndpointDuplexClient
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequest,
    NetworkRequestStatus,
)
from aware_network_service_dto.comms.identity.identity_session_operation import (
    TokenLoginRequest,
    TokenLoginResponse,
    WhoamiRequest,
    WhoamiResponse,
)
from aware_network_service_dto.comms.models.network_node import (
    InterfaceSessionHeartbeatRequest,
    InterfaceSessionHeartbeatResponse,
    InterfaceSessionRegisterRequest,
    InterfaceSessionRegisterResponse,
    NetworkNodeOperation,
)
from aware_utils.logging import logger
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

from aware_interface_service.config import (
    DEFAULT_HOST_LABEL,
    InterfaceHostInterfacePackageRef,
    InterfaceHostServiceConfig,
    resolve_state_home,
)
from aware_interface_service.local_runtime import InterfaceLocalRuntimeController
from aware_interface_service.local_state import (
    ensure_interface_service_local_state_registry,
)
from aware_interface_service.dev_adapters import (
    build_interface_host_dev_adapter_selection,
    interface_host_dev_adapter_selected,
)
from aware_interface_service.runtime import InterfaceHostServiceRuntime
from aware_interface_service.host.actions import InterfaceActionTarget
from aware_interface_service.host.capabilities.navigation_context_layout import (
    ServiceApiInterfaceNavigationContextLayoutPort,
)
from aware_interface_service.models import (
    InterfaceAppScreenEntryResult,
    InterfaceEnvironmentEntryResult,
    InterfaceEnvironmentNavigationSelectResult,
    InterfaceEnvironmentSessionJoinResult,
    InterfaceHostServiceRendererCapabilitiesState,
    InterfaceHostAttentionLayoutTransitionResult,
    InterfaceHostAttentionLayoutTopologyTransitionResult,
    InterfaceHostServiceState,
)


_UNAUTHENTICATED_ACTOR_ID = UUID(int=0)
_AWARE_CONTROL_BOOT_PROGRAM_REF = "aware_control:EnsureBootInterfaceGraph"


@dataclass(slots=True)
class AwareApiConfig:
    endpoint: str
    actor_id: UUID
    context: AwareApiContext | None = None
    request_timeout: float = 10.0


@dataclass(frozen=True, slots=True)
class AwareApiEndpointStreamHandle:
    events: AsyncIterator[InvokeApiEndpointResponse]
    close: Callable[[], Awaitable[None]]
    response: Awaitable[InvokeApiEndpointResponse]


@dataclass(slots=True)
class _ApiEndpointStreamState:
    request_id: UUID
    connection_id: UUID
    actor_id: UUID
    queue: asyncio.Queue[InvokeApiEndpointResponse | None]
    terminal_task: asyncio.Task[InvokeApiEndpointResponse]


class _InterfaceApiEndpointDuplexClient(ApiEndpointDuplexClient):
    """Interface-side Product-A duplex client with stream notification fan-in."""

    _api_endpoint_streams: dict[UUID, _ApiEndpointStreamState] = PrivateAttr(
        default_factory=dict
    )

    async def open_api_endpoint_stream(
        self,
        *,
        connection_id: UUID,
        operation: NetworkOperation,
        actor_id: UUID,
        timeout_s: float | None = None,
    ) -> AwareApiEndpointStreamHandle:
        request_id = uuid4()
        frame = self._build_message(
            message_type=WsMessageFrameType.REQUEST,
            data_serialized=operation.model_dump_json(),
            request_id=request_id,
        )
        queue: asyncio.Queue[InvokeApiEndpointResponse | None] = asyncio.Queue()
        terminal_task = asyncio.create_task(
            self._run_api_endpoint_stream_terminal(
                connection_id=connection_id,
                request_id=request_id,
                request_data=frame.model_dump_json(),
                actor_id=actor_id,
                timeout_s=None,
            )
        )
        state = _ApiEndpointStreamState(
            request_id=request_id,
            connection_id=connection_id,
            actor_id=actor_id,
            queue=queue,
            terminal_task=terminal_task,
        )
        self._api_endpoint_streams[operation.id] = state
        terminal_task.add_done_callback(
            lambda task: self._complete_api_endpoint_stream(operation.id, task)
        )

        async def _events() -> AsyncIterator[InvokeApiEndpointResponse]:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event

        async def _close() -> None:
            await self.close_api_endpoint_stream(operation.id)

        return AwareApiEndpointStreamHandle(
            events=_events(),
            close=_close,
            response=terminal_task,
        )

    async def close_api_endpoint_stream(self, operation_id: UUID) -> None:
        state = self._api_endpoint_streams.pop(operation_id, None)
        if state is None:
            return
        self.messenger.pending_futures.pop(state.request_id, None)
        if not state.terminal_task.done():
            state.terminal_task.cancel()
        state.queue.put_nowait(None)
        await asyncio.gather(state.terminal_task, return_exceptions=True)

    async def _run_api_endpoint_stream_terminal(
        self,
        *,
        connection_id: UUID,
        request_id: UUID,
        request_data: str,
        actor_id: UUID,
        timeout_s: float | None,
    ) -> InvokeApiEndpointResponse:
        try:
            raw_response = await self.messenger.send_request(
                request_id=request_id,
                request_data=request_data,
                connection_id=connection_id,
                timeout_s=timeout_s,
            )
            response_op = _parse_network_operation_response(raw_response)
            api_response = (
                response_op.api_operation.response
                if response_op.api_operation is not None
                else None
            )
            if isinstance(api_response, InvokeApiEndpointResponse):
                return api_response
            raise RuntimeError(
                "Node API gateway did not return an API stream terminal payload."
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return InvokeApiEndpointResponse(
                actor_id=actor_id,
                status=ApiRequestStatus.failed,
                error=str(exc),
                stream_lifecycle=ApiStreamLifecycle.closed,
            )

    def _complete_api_endpoint_stream(
        self,
        operation_id: UUID,
        task: asyncio.Task[InvokeApiEndpointResponse],
    ) -> None:
        state = self._api_endpoint_streams.get(operation_id)
        if state is None:
            return
        if not task.cancelled():
            with suppress(Exception):
                terminal = task.result()
                if (
                    terminal.status is not ApiRequestStatus.failed
                    and terminal.stream_lifecycle is ApiStreamLifecycle.started
                ):
                    return
                self._api_endpoint_streams.pop(operation_id, None)
                if terminal.status is ApiRequestStatus.failed:
                    state.queue.put_nowait(terminal)
        else:
            self._api_endpoint_streams.pop(operation_id, None)
        state.queue.put_nowait(None)

    async def handle_data(self, connection_id: UUID, data: dict) -> None:
        try:
            frame = WsMessageFrame.model_validate(data)
        except Exception:
            await super().handle_data(connection_id, data)
            return
        if frame.type is not WsMessageFrameType.NOTIFICATION:
            await super().handle_data(connection_id, data)
            return
        await self._handle_notification_frame(frame)

    async def _handle_notification_frame(self, frame: WsMessageFrame) -> None:
        payload: object = frame.data
        try:
            if isinstance(payload, str):
                network_op = NetworkOperation.model_validate_json(payload)
            elif isinstance(payload, dict):
                network_op = NetworkOperation.model_validate(payload)
            else:
                return
        except Exception as exc:
            logger.warning(
                "aware_interface_service ignored invalid stream notification: %s",
                exc,
            )
            return
        if network_op.message_type is not NetworkOperationMessageType.stream:
            return
        state = self._api_endpoint_streams.get(network_op.id)
        if state is None:
            logger.debug(
                "aware_interface_service ignored orphan API stream notification: %s",
                network_op.id,
            )
            return
        api_response = (
            network_op.api_operation.response
            if network_op.api_operation is not None
            else None
        )
        if not isinstance(api_response, InvokeApiEndpointResponse):
            logger.warning(
                "aware_interface_service ignored API stream notification without "
                "InvokeApiEndpointResponse: %s",
                network_op.id,
            )
            return
        await state.queue.put(api_response)
        if api_response.stream_lifecycle is not ApiStreamLifecycle.started:
            self._api_endpoint_streams.pop(network_op.id, None)
            await state.queue.put(None)


class _GeneratedApiEndpointRawClient(Protocol):
    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
        timeout_s: float | None = None,
    ) -> InvokeApiEndpointResponse: ...

    async def open_api_endpoint_stream_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        timeout_s: float | None = None,
    ) -> AwareApiEndpointStreamHandle: ...


@dataclass(frozen=True, slots=True)
class _InterfaceApiEndpointTransport:
    """Generated API transport over the Interface-owned Node API gateway."""

    client: _GeneratedApiEndpointRawClient

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        response = await self.client.invoke_api_endpoint_raw(
            endpoint_ref=invocation.endpoint_ref,
            discriminant=invocation.discriminant,
            request_payload=invocation.request_payload,
            timeout_s=timeout_s,
        )
        return _api_endpoint_response_from_raw(response)

    async def open_stream(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointStream:
        raw_handle = await self.client.open_api_endpoint_stream_raw(
            endpoint_ref=invocation.endpoint_ref,
            discriminant=invocation.discriminant,
            request_payload=invocation.request_payload,
            timeout_s=timeout_s,
        )

        async def _events() -> AsyncIterator[ApiEndpointResponse]:
            async for event in raw_handle.events:
                yield _api_endpoint_response_from_raw(event)

        async def _response() -> ApiEndpointResponse:
            return _api_endpoint_response_from_raw(await raw_handle.response)

        return ApiEndpointStream(
            events=_events(),
            close=raw_handle.close,
            response=_response(),
        )


def _api_endpoint_response_from_raw(
    response: InvokeApiEndpointResponse,
) -> ApiEndpointResponse:
    return ApiEndpointResponse(
        status=_enum_token(response.status, default="succeeded"),
        response_payload=response.response_payload,
        error=response.error,
        stream_lifecycle=_enum_token(
            response.stream_lifecycle,
            default="auto_close",
        ),
    )


def _enum_token(value: object, *, default: str) -> str:
    raw = getattr(value, "value", value)
    if raw is None:
        return default
    token = str(raw).strip()
    return token or default


class AwareApiClient:
    """Interface-service owned Node gateway over the shared network transport."""

    def __init__(self, config: AwareApiConfig) -> None:
        self.config = config
        self.connection_id = uuid4()
        self._duplex: ApiEndpointDuplexClient | None = None
        self._generated_api_invoker = AwareApiEndpointInvoker(
            _InterfaceApiEndpointTransport(client=self)
        )
        self._node_sdk = AwareNodeSdk(
            AwareNodeServiceApiClient(client=self._generated_api_invoker),
            cache=NodeSdkCache(),
        )
        self._environment_api = AwareEnvironmentServiceApiClient(
            client=self._generated_api_invoker,
        )
        self._experience_api = AwareExperienceServiceApiClient(
            client=self._generated_api_invoker,
        )

    def get_context(self) -> AwareApiContext | None:
        return self.config.context

    def set_context(self, context: AwareApiContext) -> None:
        self.config.context = context

    async def invoke_api_endpoint(self, **kwargs: Any) -> Any:
        if kwargs.get("timeout_s") is None:
            kwargs["timeout_s"] = self.config.request_timeout
        return await self._generated_api_invoker.invoke_api_endpoint(**kwargs)

    async def stream_api_endpoint(self, **kwargs: Any) -> AsyncIterator[Any]:
        if kwargs.get("timeout_s") is None:
            kwargs["timeout_s"] = self.config.request_timeout
        async for event in self._generated_api_invoker.stream_api_endpoint(**kwargs):
            yield event

    async def close(self) -> None:
        if self._duplex is not None:
            await self._duplex.disconnect(self.connection_id)
            self._duplex = None

    async def discover_environment_configs(self) -> Any:
        return await self._node_sdk.node.discover_environment_configs(
            actor_id=self.config.actor_id,
        )

    async def discover_service_api_dependency_routes(
        self,
        *,
        consumer_service_package_id: UUID | None = None,
        api_package_id: UUID | None = None,
    ) -> Any:
        return await self._node_sdk.node.discover_service_api_dependency_routes(
            consumer_service_package_id=consumer_service_package_id,
            api_package_id=api_package_id,
            actor_id=self.config.actor_id,
        )

    async def describe_hosted_service_runtimes(self) -> Any:
        return await self._node_sdk.node.describe_hosted_service_runtimes(
            actor_id=self.config.actor_id,
        )

    async def describe_hosted_runtimes(
        self,
        *,
        runtime_kind: str | None = None,
        runtime_key: str | None = None,
    ) -> Any:
        return await self._node_sdk.node.describe_hosted_runtimes(
            runtime_kind=runtime_kind,
            runtime_key=runtime_key,
            actor_id=self.config.actor_id,
        )

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key: str,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> Any:
        return await self._node_sdk.node.restart_hosted_runtime(
            runtime_key=runtime_key,
            reason=reason,
            evidence=evidence,
            actor_id=self.config.actor_id,
        )

    async def get_boot_environment_descriptor(self) -> Any:
        return await self._node_sdk.node.get_boot_environment_descriptor(
            actor_id=self.config.actor_id,
        )

    async def provision_environment(
        self,
        *,
        environment_config_id: UUID | None = None,
        eager_ready: bool = True,
    ) -> Any:
        return await self._node_sdk.node.provision_environment(
            environment_config_id=environment_config_id,
            eager_ready=eager_ready,
            actor_id=self.config.actor_id,
        )

    async def get_environment_status(
        self,
        *,
        environment_id: UUID,
    ) -> Any:
        return await self._node_sdk.node.get_environment_status(
            environment_id=environment_id,
            actor_id=self.config.actor_id,
        )

    async def describe_environment_config(self) -> Any:
        return await self._environment_api.environment.describe_config.describe_environment_config(
            DescribeEnvironmentConfigRequest(**self._environment_request_context())
        )

    async def describe_environment(self) -> Any:
        return await self._environment_api.environment.describe.describe_environment(
            DescribeEnvironmentRequest(**self._environment_request_context())
        )

    async def fetch_capabilities(self) -> Any:
        return await self._environment_api.environment.capabilities.fetch_capabilities(
            FetchCapabilitiesRequest(**self._environment_request_context())
        )

    async def describe_environment_topology(
        self,
        *,
        process_key: str | None = None,
        thread_key: str | None = None,
    ) -> Any:
        return await self._environment_api.environment.topology.describe_environment_topology(
            DescribeEnvironmentTopologyRequest(
                **self._environment_request_context(),
                process_key=process_key,
                thread_key=thread_key,
            )
        )

    async def apply_program_ref(
        self,
        *,
        program_ref: str,
        symbols: dict[str, object] | JsonObject | None = None,
        validate_only: bool = False,
        commit: bool = True,
        publish: bool = False,
    ) -> Any:
        return await self._experience_api.experience.program.apply_program_ref(
            ApplyProgramRefRequest(
                **self._environment_request_context(),
                program_ref=program_ref,
                symbols=cast(JsonObject, _jsonable(symbols or {})),
                validate_only=validate_only,
                commit=commit,
                publish=publish,
            )
        )

    def _environment_request_context(self) -> dict[str, Any]:
        context = self.config.context
        if context is None:
            raise RuntimeError(
                "Environment API request requires an active AwareApiContext. "
                "Call Interface attachment bootstrap first."
            )
        return {
            "actor_id": self.config.actor_id,
            "environment_id": context.environment_id,
            "process_id": context.process_id,
            "thread_id": context.thread_id,
            "branch_id": context.branch_id,
            "projection_hash": context.projection_hash,
        }

    # Compatibility hold: Interface admission/session/auth is being canonicalized
    # under the Interface API lane. Keep these legacy Node operations narrow so
    # Node SDK does not become a catch-all for Interface-owned admission.
    async def ensure_interface_session_registered(
        self,
        *,
        profile: InterfaceSessionRegisterRequest,
    ) -> InterfaceSessionRegisterResponse:
        response = await self._send_network_node_request(profile)
        if not isinstance(response, InterfaceSessionRegisterResponse):
            raise RuntimeError(
                "Node did not return interface_session_register response."
            )
        return response

    async def heartbeat_interface_session(
        self,
        *,
        profile: InterfaceSessionRegisterRequest,
        timestamp: str,
    ) -> InterfaceSessionHeartbeatResponse:
        response = await self._send_network_node_request(
            InterfaceSessionHeartbeatRequest(
                actor_id=self.config.actor_id,
                interface_session_id=profile.interface_session_id,
                timestamp=timestamp,
            )
        )
        if not isinstance(response, InterfaceSessionHeartbeatResponse):
            raise RuntimeError(
                "Node did not return interface_session_heartbeat response."
            )
        return response

    async def token_login(self, *, token: str) -> TokenLoginResponse:
        response = await self._send_network_node_request(
            TokenLoginRequest(actor_id=self.config.actor_id, token=token)
        )
        if not isinstance(response, TokenLoginResponse):
            raise RuntimeError("Node did not return token_login response.")
        actor_id = getattr(response, "actor_id", None)
        if actor_id is not None:
            self.config.actor_id = actor_id
        return response

    async def whoami(self) -> WhoamiResponse:
        response = await self._send_network_node_request(
            WhoamiRequest(actor_id=self.config.actor_id)
        )
        if not isinstance(response, WhoamiResponse):
            raise RuntimeError("Node did not return whoami response.")
        return response

    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
        timeout_s: float | None = None,
    ) -> InvokeApiEndpointResponse:
        operation = self._network_operation(
            operation_type=NetworkOperationType.api,
            api_operation=ApiOperation(
                request=InvokeApiEndpointRequest(
                    actor_id=self.config.actor_id,
                    endpoint_ref=endpoint_ref,
                    discriminant=discriminant,
                    request_payload=cast(JsonObject, dict(request_payload)),
                    invocation_context=(
                        cast(JsonObject, invocation_context)
                        if invocation_context is not None
                        else None
                    ),
                )
            ),
        )
        response_op = await self._send(operation, timeout_s=timeout_s)
        api_response = (
            response_op.api_operation.response
            if response_op.api_operation is not None
            else None
        )
        if not isinstance(api_response, InvokeApiEndpointResponse):
            raise RuntimeError(
                "Node API gateway did not return an API response payload."
            )
        return api_response

    async def open_api_endpoint_stream_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        timeout_s: float | None = None,
    ) -> AwareApiEndpointStreamHandle:
        operation = self._network_operation(
            operation_type=NetworkOperationType.api,
            api_operation=ApiOperation(
                request=StreamApiEndpointRequest(
                    actor_id=self.config.actor_id,
                    endpoint_ref=endpoint_ref,
                    discriminant=discriminant,
                    request_payload=cast(JsonObject, dict(request_payload)),
                )
            ),
        )
        duplex = await self._ensure_duplex()
        if not isinstance(duplex, _InterfaceApiEndpointDuplexClient):
            raise RuntimeError(
                "Interface Node API gateway does not support Product-A streaming."
            )
        return await duplex.open_api_endpoint_stream(
            connection_id=self._active_connection_id(),
            operation=operation,
            actor_id=self.config.actor_id,
            timeout_s=timeout_s or self.config.request_timeout,
        )

    async def _send_network_node_request(
        self,
        request: object,
        *,
        timeout_s: float | None = None,
    ) -> object:
        operation = self._network_operation(
            operation_type=NetworkOperationType.network_node,
            network_node_operation=NetworkNodeOperation(request=request),
        )
        response_op = await self._send(operation, timeout_s=timeout_s)
        network_node_operation = response_op.network_node_operation
        if network_node_operation is None or network_node_operation.response is None:
            raise RuntimeError("Node gateway response missing network_node_operation.")
        return network_node_operation.response

    async def _send(
        self,
        operation: NetworkOperation,
        *,
        timeout_s: float | None = None,
    ) -> NetworkOperation:
        raw_response = await (await self._ensure_duplex()).send_request(
            connection_id=self._active_connection_id(),
            data_serialized=operation.model_dump_json(),
            timeout_s=timeout_s or self.config.request_timeout,
        )
        response_op = _parse_network_operation_response(raw_response)
        network_response = response_op.network_response
        if (
            network_response is not None
            and network_response.status is NetworkRequestStatus.failed
        ):
            raise RuntimeError(network_response.error or "Node gateway request failed.")
        return response_op

    async def _ensure_duplex(self) -> ApiEndpointDuplexClient:
        if self._duplex is not None:
            return self._duplex
        duplex = _InterfaceApiEndpointDuplexClient(
            client_type=NetworkAppType.interface.value,
            server_type=NetworkAppType.network_node.value,
            endpoint=self.config.endpoint,
            connection_id=self.connection_id,
            request_timeout=self.config.request_timeout,
        )
        await duplex.ensure_connection(
            self.connection_id,
            external_url=self.config.endpoint,
        )
        self._duplex = duplex
        return duplex

    def _network_operation(
        self,
        *,
        operation_type: NetworkOperationType,
        api_operation: ApiOperation | None = None,
        network_node_operation: NetworkNodeOperation | None = None,
    ) -> NetworkOperation:
        return NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=operation_type,
            network_request=NetworkRequest(requester_id=self.config.actor_id),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.interface,
                    source_interface_id=self._active_connection_id(),
                    target_app_type=NetworkAppType.network_node,
                )
            ],
            api_operation=api_operation,
            network_node_operation=network_node_operation,
        )

    def _active_connection_id(self) -> UUID:
        return cast(UUID, getattr(self._duplex, "connection_id", self.connection_id))


def _parse_network_operation_response(raw_response: object) -> NetworkOperation:
    if raw_response is None:
        raise RuntimeError(
            "Node gateway returned no response before the request timed out or "
            "the transport closed."
        )
    if isinstance(raw_response, NetworkOperation):
        return raw_response
    if isinstance(raw_response, str):
        return NetworkOperation.model_validate_json(raw_response)
    if isinstance(raw_response, dict):
        return NetworkOperation.model_validate(raw_response)
    raise TypeError(
        "Node gateway returned unsupported NetworkOperation payload type: "
        f"{type(raw_response)}"
    )


def _callable_accepts_keyword(fn: Callable[..., object], keyword: str) -> bool:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    parameters = signature.parameters
    if keyword in parameters:
        return True
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_local_endpoint(endpoint: str | None) -> bool:
    if endpoint is None:
        return False
    parsed = urlparse(endpoint)
    host = (parsed.hostname or parsed.path or endpoint).strip().lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def _is_connection_refused_error(exc: Exception) -> bool:
    if isinstance(exc, ConnectionRefusedError):
        return True
    if isinstance(exc, OSError):
        message = str(exc).lower()
        return (
            "connection refused" in message
            or "connect call failed" in message
            or "errno 111" in message
        )
    return False


def _should_degrade_to_local_shell(
    *,
    endpoint: str | None,
    exc: Exception,
    allow_degraded_local_shell: bool,
) -> bool:
    return (
        allow_degraded_local_shell
        and _is_local_endpoint(endpoint)
        and _is_connection_refused_error(exc)
    )


def _validate_live_runtime_requirement(
    *,
    config: InterfaceHostServiceConfig,
    bundle: InterfaceHostServiceLiveBundle,
) -> InterfaceHostServiceLiveBundle:
    if not config.require_live_runtime:
        return bundle
    missing: list[str] = []
    if bundle.runtime.transport_session is None:
        missing.append("transport_session")
    if bundle.runtime.host_runtime is None:
        missing.append("host_runtime")
    if bundle.runtime.coordinator is None:
        missing.append("coordinator")
    if not missing:
        return bundle
    raise RuntimeError(
        "Interface service live runtime is required for namespace="
        f"{config.namespace!r}, but bootstrap produced a local shell missing "
        f"{', '.join(missing)}."
    )


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _resolve_optional_environment_config_id(repository_root: Path) -> UUID | None:
    try:
        return _resolve_environment_config_id(repository_root=repository_root)
    except Exception:
        return None


def _resolve_environment_config_id(*, repository_root: Path | None = None) -> UUID:
    raw = (
        os.getenv("AWARE_ENVIRONMENT_CONFIG_ID")
        or os.getenv("AWARE_ENV_CONFIG_ID")
        or ""
    ).strip()
    if raw:
        return UUID(raw)

    repo_root = repository_root
    if repo_root is None:
        repo_env = os.getenv("AWARE_REPO_ROOT") or os.getenv("AWARE_REPOSITORY_ROOT")
        repo_root = Path(repo_env).expanduser() if repo_env else Path.cwd()

    env_path = repo_root / ".aware" / "environment.json"
    if not env_path.exists():
        raise RuntimeError(
            "Environment config id missing. Set AWARE_ENVIRONMENT_CONFIG_ID "
            "or ensure `.aware/environment.json` exists."
        )
    try:
        payload = json.loads(env_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Invalid environment config at {env_path}: {exc}") from exc
    env_id = payload.get("id") if isinstance(payload, dict) else None
    if not isinstance(env_id, str) or not env_id.strip():
        raise RuntimeError(f"Missing `id` in {env_path}")
    return UUID(env_id)


def _sanitize_ws_endpoint(value: str) -> str:
    endpoint = value.strip().rstrip("/")
    for suffix in ("/interface/network_node", "/network_node/network_node"):
        if endpoint.endswith(suffix):
            endpoint = endpoint[: -len(suffix)].rstrip("/")
    if endpoint.endswith("/ws"):
        endpoint = endpoint[: -len("/ws")].rstrip("/")
    return endpoint


def _resolve_default_node_endpoint(repository_root: Path) -> str:
    endpoint = os.getenv("AWARE_NODE_WS_URL")
    if endpoint:
        return _sanitize_ws_endpoint(endpoint)
    base = os.getenv("AWARE_NODE_BASE_URL")
    if base:
        if base.startswith("http://"):
            return _sanitize_ws_endpoint("ws://" + base[len("http://") :])
        if base.startswith("https://"):
            return _sanitize_ws_endpoint("wss://" + base[len("https://") :])
        return _sanitize_ws_endpoint(base)

    node_cfg_path = repository_root / ".aware" / "network_node.json"
    if node_cfg_path.exists():
        try:
            payload = json.loads(node_cfg_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                f"Invalid node config at {node_cfg_path}: {exc}"
            ) from exc
        http_base_url = (
            payload.get("http_base_url") if isinstance(payload, dict) else None
        )
        if isinstance(http_base_url, str) and http_base_url.strip():
            base_url = http_base_url.strip()
            if base_url.startswith("http://"):
                return _sanitize_ws_endpoint("ws://" + base_url[len("http://") :])
            if base_url.startswith("https://"):
                return _sanitize_ws_endpoint("wss://" + base_url[len("https://") :])
            return _sanitize_ws_endpoint(base_url)
    raise RuntimeError(
        "Node endpoint missing. Set AWARE_NODE_WS_URL or AWARE_NODE_BASE_URL "
        "or provide `.aware/network_node.json` with http_base_url."
    )


def _resolve_node_endpoint(*, repository_root: Path | None = None) -> str:
    return _resolve_default_node_endpoint(repository_root or Path.cwd())


def _runtime_interface_package_ref(
    ref: InterfaceHostInterfacePackageRef,
) -> InterfaceRuntimePackageRef:
    return InterfaceRuntimePackageRef(
        family_key=ref.family_key,
        package_kind=ref.package_kind,
        package_name=ref.package_name,
        manifest_path=ref.manifest_path,
        workspace_package_id=ref.workspace_package_id,
        semantic_package_id=ref.semantic_package_id,
        semantic_head_commit_id=ref.semantic_head_commit_id,
        semantic_branch_id=ref.semantic_branch_id,
        semantic_root_kind=ref.semantic_root_kind,
        semantic_root_id=ref.semantic_root_id,
        semantic_root_object_instance_graph_commit_id=(
            ref.semantic_root_object_instance_graph_commit_id
        ),
        source_code_package_id=ref.source_code_package_id,
    )


async def _load_committed_interface_config_bundle_for_service(
    *,
    config: InterfaceHostServiceConfig,
    runtime_backend: InterfaceHostRuntime,
) -> InterfaceConfigBundle | None:
    package_refs = config.workspace_revision.interface_package_refs
    if not package_refs:
        return None
    materialized_workspace_root = config.workspace_revision.materialized_workspace_root
    if materialized_workspace_root is None:
        raise RuntimeError(
            "Interface Host committed package mount requires "
            "workspace_revision.materialized_workspace_root."
        )
    if len(package_refs) != 1:
        raise RuntimeError(
            "Interface Host committed package mount currently requires exactly "
            f"one Interface package ref; received {len(package_refs)}."
        )
    index = runtime_backend.build_runtime_index()
    return await load_committed_interface_config_bundle_from_package_ref(
        index=index,
        package_ref=_runtime_interface_package_ref(package_refs[0]),
        materialized_workspace_root=materialized_workspace_root,
    )


async def _build_interface_host_runtime_backend(
    *,
    config: InterfaceHostServiceConfig,
    environment_config_id: UUID | None = None,
) -> InterfaceHostRuntime:
    resolved_environment_config_id = (
        config.environment_config_id or environment_config_id
    )
    db_schema_registry_path = ensure_interface_service_local_state_registry(
        repository_root=config.repository_root,
        state_home=config.state_home,
        environment_id=resolved_environment_config_id,
        registry_path=config.local_state_registry_path,
    )
    if not config.runtime_artifact_refs:
        raise RuntimeError(
            "Interface live runtime boot requires ontology runtime artifact-set "
            "refs. Legacy Environment runtime manifest boot is retired."
        )
    if resolved_environment_config_id is None:
        raise RuntimeError(
            "Interface runtime artifact-set boot requires an Environment "
            "config id from host config or session target."
        )
    runtime_backend = InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=config.repository_root,
        state_home=config.state_home,
        namespace=config.namespace,
        environment_id=resolved_environment_config_id,
        runtime_artifact_refs=config.runtime_artifact_refs,
        db_schema_registry_path=db_schema_registry_path,
        allow_local_interface_config_bundle_fallback=False,
        local_interface_package_name=config.interface_package_name,
    )
    committed_bundle = await _load_committed_interface_config_bundle_for_service(
        config=config,
        runtime_backend=runtime_backend,
    )
    if committed_bundle is None:
        return runtime_backend
    return InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=config.repository_root,
        state_home=config.state_home,
        namespace=config.namespace,
        environment_id=resolved_environment_config_id,
        runtime_artifact_refs=config.runtime_artifact_refs,
        db_schema_registry_path=db_schema_registry_path,
        committed_interface_config_bundle=committed_bundle,
        allow_local_interface_config_bundle_fallback=False,
        local_interface_package_name=config.interface_package_name,
    )


def _load_local_interface_config_bundle_for_service(
    *,
    config: InterfaceHostServiceConfig,
) -> InterfaceConfigBundle | None:
    package_name = (config.interface_package_name or "").strip()
    if not package_name:
        return None
    return load_workspace_interface_config_bundle(
        repository_root=config.repository_root,
        interface_package_name=package_name,
    ).bundle


def _load_mock_interface_config_bundle_for_service(
    *,
    config: InterfaceHostServiceConfig,
) -> InterfaceConfigBundle | None:
    try:
        bundle = _load_local_interface_config_bundle_for_service(config=config)
    except Exception:
        bundle = None
    if bundle is not None:
        return bundle
    bundle_path = (
        config.repository_root
        / "interfaces"
        / "aware_control"
        / "bundles"
        / "interface.config.bundle.json"
    )
    if not bundle_path.exists():
        return None
    return InterfaceConfigBundle.model_validate_json(
        bundle_path.read_text(encoding="utf-8")
    )


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceLiveBundle:
    runtime: InterfaceHostServiceRuntime
    attachment: InterfaceAttachment | None
    bootstrap_result: InterfaceBootstrapResult | None
    endpoint: str
    interface_id: UUID | None
    authenticated: bool


class InterfaceHostServiceBundleFactory(Protocol):
    async def __call__(
        self,
        config: InterfaceHostServiceConfig,
    ) -> InterfaceHostServiceLiveBundle: ...


class _RawApiGatewayClient(Protocol):
    async def invoke_api_endpoint_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
        timeout_s: float | None = None,
    ) -> InvokeApiEndpointResponse: ...

    async def open_api_endpoint_stream_raw(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        timeout_s: float | None = None,
    ) -> AwareApiEndpointStreamHandle: ...


def _request_status_from_api_status(status: ApiRequestStatus) -> RequestStatus:
    if status is ApiRequestStatus.succeeded:
        return RequestStatus.succeeded
    if status is ApiRequestStatus.pending:
        return RequestStatus.pending
    return RequestStatus.failed


def _stream_lifecycle_from_api_lifecycle(
    lifecycle: ApiStreamLifecycle,
) -> StreamLifecycle:
    if lifecycle is ApiStreamLifecycle.started:
        return StreamLifecycle.started
    if lifecycle is ApiStreamLifecycle.closed:
        return StreamLifecycle.closed
    return StreamLifecycle.auto_close


def _service_response_from_api_response(
    response: InvokeApiEndpointResponse,
) -> ServiceOperationResponse:
    return ServiceOperationResponse(
        status=_request_status_from_api_status(response.status),
        error=response.error,
        response_payload=response.response_payload,
        stream_lifecycle=_stream_lifecycle_from_api_lifecycle(
            response.stream_lifecycle
        ),
    )


def _invocation_context_with_interface_namespace(
    invocation_context: JsonObject | dict[str, object] | None,
    *,
    namespace: str,
) -> JsonObject:
    payload: dict[str, object] = (
        dict(invocation_context) if invocation_context is not None else {}
    )
    interface_context = payload.get("interface")
    if isinstance(interface_context, dict):
        merged_interface_context = dict(interface_context)
    else:
        merged_interface_context = {}
    merged_interface_context["namespace"] = namespace
    payload["interface"] = merged_interface_context
    return cast(JsonObject, payload)


@dataclass(slots=True)
class InterfaceHostServiceApp:
    config: InterfaceHostServiceConfig
    runtime: InterfaceHostServiceRuntime
    attachment: InterfaceAttachment | None
    bootstrap_result: InterfaceBootstrapResult | None
    interface_id: UUID | None
    endpoint: str
    authenticated: bool
    _stop_event: asyncio.Event = field(init=False, default_factory=asyncio.Event)
    _heartbeat_task: asyncio.Task[None] | None = field(init=False, default=None)
    _refresh_task: asyncio.Task[None] | None = field(init=False, default=None)
    _lane_sync_task: asyncio.Task[None] | None = field(init=False, default=None)
    _lane_sync_include_initial: bool = field(init=False, default=False)
    _attention_runtime_mount_task: asyncio.Task[None] | None = field(
        init=False,
        default=None,
    )

    @classmethod
    async def create(
        cls,
        *,
        config: InterfaceHostServiceConfig | None = None,
        bundle_factory: InterfaceHostServiceBundleFactory | None = None,
    ) -> "InterfaceHostServiceApp":
        resolved_config = config or InterfaceHostServiceConfig.from_env()
        if interface_host_dev_adapter_selected(
            endpoint=resolved_config.endpoint,
            dev_adapter_specs=resolved_config.dev_adapter_specs,
        ):
            resolved_config = replace(resolved_config, lane_sync_enabled=False)
        resolved_bundle_factory = bundle_factory or build_live_service_bundle
        bundle = await resolved_bundle_factory(resolved_config)
        return cls(
            config=resolved_config,
            runtime=bundle.runtime,
            attachment=bundle.attachment,
            bootstrap_result=bundle.bootstrap_result,
            interface_id=bundle.interface_id,
            endpoint=bundle.endpoint,
            authenticated=bundle.authenticated,
        )

    def state(self) -> InterfaceHostServiceState:
        return self.runtime.state()

    def state_revision(self) -> int:
        runtime_state_revision = getattr(self.runtime, "state_revision", None)
        if callable(runtime_state_revision):
            return cast(Callable[[], int], runtime_state_revision)()
        return 0

    async def wait_for_state_change(
        self,
        *,
        after_revision: int,
        timeout_s: float,
    ) -> bool:
        runtime_wait_for_state_change = getattr(
            self.runtime, "wait_for_state_change", None
        )
        if callable(runtime_wait_for_state_change):
            return await cast(
                Callable[..., Awaitable[bool]],
                runtime_wait_for_state_change,
            )(
                after_revision=after_revision,
                timeout_s=timeout_s,
            )
        await asyncio.sleep(max(timeout_s, 0.0))
        return False

    async def start(self) -> InterfaceHostServiceState:
        state = await self.runtime.start(
            ensure_boot_graph=self.config.ensure_boot_graph,
            authenticated=self.authenticated,
        )
        if self.config.lane_sync_enabled and self.authenticated and self.config.once:
            await self.runtime.sync_focus_scope_lane_once(
                window_key=self.config.lane_sync_window_key,
                include_commit_payload=self.config.lane_sync_include_commit_payload,
            )
            state = self.runtime.state()
        if self.authenticated:
            self._lane_sync_include_initial = (
                self.config.lane_sync_enabled and not self.config.once
            )
            self._arm_background_tasks()
        return state

    async def run_until_stopped(self) -> InterfaceHostServiceState:
        state = await self.start()
        if self.config.once:
            return state
        await self._stop_event.wait()
        return self.runtime.state()

    def request_stop(self) -> None:
        self._stop_event.set()

    async def close(self) -> None:
        self.request_stop()
        await self._cancel_background_tasks()
        await self.runtime.close()

    async def perform_action(
        self,
        *,
        pane_ref: str | None = None,
        action_key: str,
        action_target: InterfaceActionTarget | None = None,
        payload: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        if action_target is not None:
            state = await self.runtime.perform_action(
                pane_ref=pane_ref,
                action_key=action_key,
                action_target=action_target,
                payload=payload,
            )
        else:
            state = await self.runtime.perform_action(
                pane_ref=pane_ref,
                action_key=action_key,
                payload=payload,
            )
        return state

    async def select_control_plane_step(
        self,
        *,
        step_id: str | None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.select_control_plane_step(step_id=step_id)

    async def select_control_plane_profile(
        self,
        *,
        profile_id: str,
    ) -> InterfaceHostServiceState:
        return await self.runtime.select_control_plane_profile(profile_id=profile_id)

    async def select_control_plane_workspace(
        self,
        *,
        workspace_root: str,
    ) -> InterfaceHostServiceState:
        return await self.runtime.select_control_plane_workspace(
            workspace_root=workspace_root
        )

    async def select_control_plane_semantic_package(
        self,
        *,
        selector_key: str | None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.select_control_plane_semantic_package(
            selector_key=selector_key
        )

    async def select_control_plane_runtime_layout(
        self,
        *,
        layout_config_id: UUID | str | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.select_control_plane_runtime_layout(
            layout_config_id=layout_config_id,
        )

    async def activate_control_plane_runtime_focus(
        self,
        *,
        representation_id: UUID | str | None = None,
        layout_config_id: UUID | str | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | str | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.activate_control_plane_runtime_focus(
            representation_id=representation_id,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
        )

    async def request_interface_window_layout(
        self,
        *,
        interface_package_id: UUID | str | None = None,
        interface_package_name: str | None = None,
        window_key: str | None = None,
        layout_config_id: UUID | str | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | str | None = None,
        representation_id: UUID | str | None = None,
        requested_by_service: str | None = None,
        requested_by_operation: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.request_interface_window_layout(
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
            window_key=window_key,
            layout_config_id=layout_config_id,
            layout_key=layout_key,
            section_key=section_key,
            observable_id=observable_id,
            representation_id=representation_id,
            requested_by_service=requested_by_service,
            requested_by_operation=requested_by_operation,
            reason=reason,
            idempotency_key=idempotency_key,
        )

    async def apply_attention_layout_transition(
        self,
        *,
        client_intent_id: str,
        expected_previous_layout_transition_id: UUID | str | None,
        topology_transition_id: UUID | str | None = None,
        section_states: Sequence[AttentionLayoutIntentSection],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTransitionResult:
        return await self.runtime.apply_attention_layout_transition(
            client_intent_id=client_intent_id,
            expected_previous_layout_transition_id=(
                expected_previous_layout_transition_id
            ),
            topology_transition_id=topology_transition_id,
            section_states=section_states,
            source_ref=source_ref,
            metadata=metadata,
        )

    async def apply_attention_layout_topology_transition(
        self,
        *,
        client_intent_id: str,
        expected_previous_topology_transition_id: UUID | str | None,
        section_states: Sequence[AttentionLayoutTopologyIntentSection],
        source_ref: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> InterfaceHostAttentionLayoutTopologyTransitionResult:
        return await self.runtime.apply_attention_layout_topology_transition(
            client_intent_id=client_intent_id,
            expected_previous_topology_transition_id=(
                expected_previous_topology_transition_id
            ),
            section_states=section_states,
            source_ref=source_ref,
            metadata=metadata,
        )

    async def admit_environment_actor(
        self,
        *,
        environment_profile_id: UUID,
        actor_config_id: UUID,
        class_instance_identity_id: UUID,
        environment_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: tuple[UUID, ...] = (),
        requested_role_config_names: tuple[str, ...] = (),
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.admit_environment_actor(
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            environment_id=environment_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            reason=reason,
            evidence=evidence,
        )

    async def enter_app_screen(
        self,
        *,
        app_package_id: UUID,
        app_package_branch_id: UUID,
        app_package_object_instance_graph_commit_id: UUID,
        app_config_screen_config_id: UUID,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
        committed_app_screen_resolver: object | None = None,
    ) -> InterfaceAppScreenEntryResult:
        return await self.runtime.enter_app_screen(
            app_package_id=app_package_id,
            app_package_branch_id=app_package_branch_id,
            app_package_object_instance_graph_commit_id=(
                app_package_object_instance_graph_commit_id
            ),
            app_config_screen_config_id=app_config_screen_config_id,
            reason=reason,
            evidence=evidence,
            committed_app_screen_resolver=committed_app_screen_resolver,
        )

    async def enter_environment(
        self,
        *,
        environment_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        actor_config_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        requested_role_config_ids: tuple[UUID, ...] = (),
        requested_role_config_names: tuple[str, ...] = (),
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        environment_session_id: UUID | None = None,
        environment_session_config_id: UUID | None = None,
        session_key: str | None = None,
        title: str | None = None,
        description: str | None = None,
        purpose: str | None = None,
        source_kind: str | None = None,
        source_ref: str | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentEntryResult:
        return await self.runtime.enter_environment(
            environment_id=environment_id,
            environment_profile_id=environment_profile_id,
            actor_config_id=actor_config_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            requested_role_config_ids=requested_role_config_ids,
            requested_role_config_names=requested_role_config_names,
            environment_admission_receipt=environment_admission_receipt,
            environment_session_id=environment_session_id,
            environment_session_config_id=environment_session_config_id,
            session_key=session_key,
            title=title,
            description=description,
            purpose=purpose,
            source_kind=source_kind,
            source_ref=source_ref,
            reason=reason,
            evidence=evidence,
        )

    async def join_environment_session(
        self,
        *,
        environment_session_id: UUID,
        environment_profile_id: UUID | None = None,
        environment_admission_receipt: EnvironmentActorAdmissionReceipt | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentSessionJoinResult:
        return await self.runtime.join_environment_session(
            environment_session_id=environment_session_id,
            environment_profile_id=environment_profile_id,
            environment_admission_receipt=environment_admission_receipt,
            reason=reason,
            evidence=evidence,
        )

    async def select_environment_navigation_target(
        self,
        *,
        environment_navigation_context_id: UUID | None = None,
        selected_process_id: UUID | None = None,
        selected_thread_id: UUID | None = None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceEnvironmentNavigationSelectResult:
        return await self.runtime.select_environment_navigation_target(
            environment_navigation_context_id=environment_navigation_context_id,
            selected_process_id=selected_process_id,
            selected_thread_id=selected_thread_id,
            reason=reason,
            evidence=evidence,
        )

    async def resolve_experience_lens(
        self,
        *,
        environment_session_join_receipt: EnvironmentSessionJoinReceipt | None,
        environment_navigation_context: EnvironmentNavigationContextView | None,
        experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None,
        experience_identity_session_config_id: UUID | None,
        reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.resolve_experience_lens(
            environment_session_join_receipt=environment_session_join_receipt,
            environment_navigation_context=environment_navigation_context,
            experience_actor_admission=experience_actor_admission,
            experience_identity_session_config_id=experience_identity_session_config_id,
            reason=reason,
            evidence=evidence,
        )

    async def ensure_selected_workspace_running(self) -> InterfaceHostServiceState:
        return await self.runtime.ensure_selected_workspace_running()

    async def join_selected_workspace(self) -> InterfaceHostServiceState:
        return await self.runtime.join_selected_workspace()

    async def leave_selected_workspace(self) -> InterfaceHostServiceState:
        return await self.runtime.leave_selected_workspace()

    async def recover_selected_workspace(self) -> InterfaceHostServiceState:
        return await self.runtime.recover_selected_workspace()

    async def stop_selected_workspace(self) -> InterfaceHostServiceState:
        return await self.runtime.stop_selected_workspace()

    async def report_renderer_capabilities(
        self,
        *,
        renderer_capabilities: InterfaceHostServiceRendererCapabilitiesState,
    ) -> InterfaceHostServiceState:
        return await self.runtime.report_renderer_capabilities(
            renderer_capabilities=renderer_capabilities,
        )

    async def apply_workspace_session(
        self,
        *,
        selected_workspace_root: Path | None,
        joined_workspace_root: Path | None,
        selected_runtime_focus_section_key: str | None = None,
        selected_runtime_focus_observable_id: UUID | str | None = None,
        attached_namespace_counts_by_workspace: dict[str, int] | None = None,
    ) -> InterfaceHostServiceState:
        return await self.runtime.apply_workspace_session(
            selected_workspace_root=selected_workspace_root,
            joined_workspace_root=joined_workspace_root,
            selected_runtime_focus_section_key=selected_runtime_focus_section_key,
            selected_runtime_focus_observable_id=selected_runtime_focus_observable_id,
            attached_namespace_counts_by_workspace=attached_namespace_counts_by_workspace,
        )

    async def refresh_state(self) -> InterfaceHostServiceState:
        return await self.runtime.refresh_runtime_state()

    async def invoke_api(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        invocation_context = _invocation_context_with_interface_namespace(
            invocation_context,
            namespace=self.config.namespace,
        )
        runtime_invoke_api = getattr(self.runtime, "invoke_api", None)
        if callable(runtime_invoke_api):
            invoke_api = cast(
                Callable[..., Awaitable[ServiceOperationResponse]],
                runtime_invoke_api,
            )
            return await invoke_api(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
                invocation_context=invocation_context,
            )
        node_response = await self._invoke_api_via_node_product_a(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            invocation_context=invocation_context,
        )
        if node_response is not None:
            return node_response
        return await self._invoke_api_via_local_service_host(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            invocation_context=invocation_context,
        )

    async def open_api_stream(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
    ) -> ServiceHostDuplexRequestHandle:
        runtime_open_api_stream = getattr(self.runtime, "open_api_stream", None)
        if callable(runtime_open_api_stream):
            open_api_stream = cast(
                Callable[..., Awaitable[ServiceHostDuplexRequestHandle]],
                runtime_open_api_stream,
            )
            return await open_api_stream(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
            )
        node_handle = await self._open_api_stream_via_node_product_a(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
        )
        if node_handle is not None:
            return node_handle
        return await self._open_api_stream_via_local_service_host(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
        )

    async def _invoke_api_via_node_product_a(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse | None:
        client = self._raw_api_gateway_client()
        if client is None:
            return None
        invoke_kwargs: dict[str, object] = {
            "endpoint_ref": endpoint_ref,
            "discriminant": discriminant,
            "request_payload": request_payload,
            "timeout_s": 10.0,
        }
        if invocation_context is not None and _callable_accepts_keyword(
            client.invoke_api_endpoint_raw,
            "invocation_context",
        ):
            invoke_kwargs["invocation_context"] = invocation_context
        response = await client.invoke_api_endpoint_raw(**invoke_kwargs)
        return _service_response_from_api_response(response)

    async def _open_api_stream_via_node_product_a(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
    ) -> ServiceHostDuplexRequestHandle | None:
        client = self._raw_api_gateway_client()
        if client is None:
            return None
        handle = await client.open_api_endpoint_stream_raw(
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            timeout_s=10.0,
        )
        return self._service_host_duplex_handle_from_api_stream(
            handle=handle,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
        )

    async def _invoke_api_via_local_service_host(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceOperationResponse:
        client = await self._build_local_service_host_duplex_client()
        return await client.send_api_ingress_request(
            request=self._build_service_host_api_ingress_request(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
                invocation_context=invocation_context,
                stream_requested=False,
            ),
            timeout_s=10.0,
        )

    async def _open_api_stream_via_local_service_host(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
    ) -> ServiceHostDuplexRequestHandle:
        client = await self._build_local_service_host_duplex_client()
        return client.open_api_ingress_stream(
            request=self._build_service_host_api_ingress_request(
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
                stream_requested=True,
            ),
            timeout_s=None,
        )

    async def _build_local_service_host_duplex_client(self) -> ServiceHostDuplexClient:
        local_runtime = getattr(self.runtime, "local_runtime", None)
        if local_runtime is None:
            raise RuntimeError(
                "Interface host API gateway is unavailable because this runtime "
                "does not expose local service-host routing."
            )
        snapshot = await local_runtime.ensure_service_host_ready()
        service_host = snapshot.service_host
        if not service_host.managed:
            raise RuntimeError(
                "Interface host API gateway currently supports only locally managed Service host routing."
            )
        if not service_host.ready:
            raise RuntimeError(
                service_host.error
                or "Interface host API gateway could not reach a ready local Service host."
            )
        return ServiceHostDuplexClient(
            endpoint=DuplexIpcEndpoint.unix_socket(
                socket_path=str(local_runtime.resolve_service_host_socket_path())
            )
        )

    def _raw_api_gateway_client(self) -> _RawApiGatewayClient | None:
        transport_session = getattr(self.runtime, "transport_session", None)
        if transport_session is None:
            return None
        client = getattr(transport_session, "client", None)
        if client is None:
            return None
        if not callable(getattr(client, "invoke_api_endpoint_raw", None)):
            return None
        if not callable(getattr(client, "open_api_endpoint_stream_raw", None)):
            return None
        return cast(_RawApiGatewayClient, client)

    def _service_host_duplex_handle_from_api_stream(
        self,
        *,
        handle: AwareApiEndpointStreamHandle,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
    ) -> ServiceHostDuplexRequestHandle:
        terminal_response = asyncio.create_task(
            self._service_response_from_api_stream_terminal(handle.response)
        )

        async def _events() -> AsyncIterator[ServiceDuplexStreamEvent]:
            sequence = 0
            async for response in handle.events:
                if response.status is ApiRequestStatus.failed:
                    raise RuntimeError(response.error or "API stream request failed")
                if response.stream_lifecycle is ApiStreamLifecycle.closed:
                    break
                if response.stream_lifecycle is not ApiStreamLifecycle.started:
                    continue
                if response.response_payload is None:
                    continue
                sequence += 1
                yield ServiceDuplexStreamEvent.response_event(
                    ServiceOperationResponse(
                        status=_request_status_from_api_status(response.status),
                        response_payload=self._api_stream_event_envelope_payload(
                            endpoint_ref=endpoint_ref,
                            discriminant=discriminant,
                            request_payload=request_payload,
                            sequence=sequence,
                            payload=response.response_payload,
                        ),
                        stream_lifecycle=StreamLifecycle.started,
                    )
                )

        return ServiceHostDuplexRequestHandle(
            events=_events(),
            response=terminal_response,
            close=handle.close,
        )

    async def _service_response_from_api_stream_terminal(
        self,
        response: Awaitable[InvokeApiEndpointResponse],
    ) -> ServiceOperationResponse:
        return _service_response_from_api_response(await response)

    def _api_stream_event_envelope_payload(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        sequence: int,
        payload: object,
    ) -> JsonValue:
        context_id = uuid4()
        actor_id = self.state().transport.actor_id
        request = ServiceOperationRequest(
            context=ServiceOperationContext(
                actor_id=actor_id,
                environment_id=context_id,
                process_id=context_id,
                thread_id=context_id,
                branch_id=context_id,
                projection_hash="interface-node-product-a-gateway",
            ),
            service="interface_api_gateway",
            operation={
                "endpoint_ref": endpoint_ref,
                "discriminant": discriminant,
                "request_payload": request_payload,
            },
            network_request_id=context_id,
        )
        envelope = ServiceStreamEventEnvelope(
            session=ServiceStreamSession(
                session_id=context_id,
                request=request,
                publisher_id="node_product_a",
                subscriber_id="interface_host",
            ),
            sequence=sequence,
            kind=ServiceStreamEventKind.DELTA,
            item_key=str(sequence),
            payload=payload,
        )
        return cast(
            JsonValue,
            ServiceDuplexStreamEventEnvelope.from_contract(envelope).model_dump(
                mode="json"
            ),
        )

    def _build_service_host_api_ingress_request(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject | dict[str, object],
        stream_requested: bool,
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ServiceHostApiIngressRequest:
        return ServiceHostApiIngressRequest(
            actor_id=self.state().transport.actor_id,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=cast(JsonObject, request_payload),
            invocation_context=(
                cast(JsonObject, invocation_context)
                if invocation_context is not None
                else None
            ),
            network_request_id=uuid4(),
            stream_requested=stream_requested,
        )

    def _arm_background_tasks(self) -> None:
        if self.config.once:
            return
        if self._heartbeat_task is None and self.config.heartbeat_interval_s > 0:
            self._heartbeat_task = asyncio.create_task(
                self._run_periodic_loop(
                    interval_s=self.config.heartbeat_interval_s,
                    label="heartbeat",
                    runner=self.runtime.heartbeat,
                )
            )
        if self._refresh_task is None and self.config.refresh_interval_s > 0:
            self._refresh_task = asyncio.create_task(
                self._run_periodic_loop(
                    interval_s=self.config.refresh_interval_s,
                    label="refresh",
                    runner=self.runtime.refresh_runtime_state,
                )
            )
        if self._lane_sync_task is None and self.config.lane_sync_enabled:
            self._lane_sync_task = asyncio.create_task(self._run_lane_sync_loop())
        if self._attention_runtime_mount_task is None:
            self._attention_runtime_mount_task = asyncio.create_task(
                self._run_attention_runtime_mount_loop()
            )

    async def _cancel_background_tasks(self) -> None:
        tasks = tuple(
            task
            for task in (
                self._heartbeat_task,
                self._refresh_task,
                self._lane_sync_task,
                self._attention_runtime_mount_task,
            )
            if task is not None
        )
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task
        self._heartbeat_task = None
        self._refresh_task = None
        self._lane_sync_task = None
        self._attention_runtime_mount_task = None

    async def _run_periodic_loop(
        self,
        *,
        interval_s: float,
        label: str,
        runner: Callable[..., Awaitable[Any]],
    ) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_s)
                break
            except asyncio.TimeoutError:
                pass
            try:
                await runner()
            except Exception as exc:
                logger.warning("aware_interface_service %s loop failed: %s", label, exc)

    async def _run_lane_sync_loop(self) -> None:
        try:
            await self.runtime.watch_focus_scope_lane(
                window_key=self.config.lane_sync_window_key,
                include_initial=self._lane_sync_include_initial,
                include_commit_payload=self.config.lane_sync_include_commit_payload,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("aware_interface_service lane-sync loop failed: %s", exc)

    async def _run_attention_runtime_mount_loop(self) -> None:
        try:
            await self.runtime.watch_attention_runtime_mount()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "aware_interface_service attention runtime-mount loop failed: %s",
                exc,
            )


def build_bootstrap_snapshot(
    *,
    repository_root: Path,
    host_label: str = DEFAULT_HOST_LABEL,
    state_home: Path | None = None,
) -> dict[str, object]:
    resolved_root = repository_root.resolve()
    resolved_state_home = state_home.resolve() if state_home is not None else None
    config = InterfaceHostServiceConfig(
        repository_root=resolved_root,
        state_home=resolved_state_home or resolve_state_home(),
        host_label=host_label,
    )
    return {
        "host_kind": "interface_service",
        "service_package": "workspaces/aware_network/modules/interface/services/interface",
        "runtime_owner": "workspaces/aware_network/modules/interface/ontology/runtime/python",
        "attachment_owner": "workspaces/aware_network/modules/interface/sdks/interface",
        "transport_owner": "workspaces/aware_network/modules/interface/sdks/interface",
        "status": "bootstrap_only_service",
        "host_label": config.host_label,
        "repository_root": str(config.repository_root),
        "state_home": str(config.state_home),
        "consumer_apps": ["apps/interface_textual"],
    }


def _build_degraded_local_shell_bundle(
    *,
    config: InterfaceHostServiceConfig,
    resolved_endpoint: str,
    resolved_environment_config_id: UUID | None,
    attachment: InterfaceAttachment | None,
) -> InterfaceHostServiceLiveBundle:
    interface_config_bundle = _load_local_interface_config_bundle_for_service(
        config=config,
    )
    local_runtime = InterfaceLocalRuntimeController(
        repository_root=config.repository_root,
        state_home=config.state_home,
        namespace=config.namespace,
        endpoint=resolved_endpoint,
        service_host_bootstrap_config_path=(
            config.local_service_host_bootstrap_config_path
        ),
        service_host_implementation_toml_paths=(
            config.local_service_host_implementation_toml_paths
        ),
    )
    runtime = InterfaceHostServiceRuntime(
        repository_root=config.repository_root,
        host_label=config.host_label,
        state_home=config.state_home,
        namespace=config.namespace,
        endpoint=resolved_endpoint,
        environment_id=None,
        environment_config_id=resolved_environment_config_id,
        transport_session=None,
        host_runtime=None,
        coordinator=None,
        local_runtime=local_runtime,
        workspace_client_provider=None,
        interface_config_bundle=interface_config_bundle,
        bundle_window_layout_enabled=interface_config_bundle is not None,
    )
    return InterfaceHostServiceLiveBundle(
        runtime=runtime,
        attachment=attachment,
        bootstrap_result=None,
        endpoint=resolved_endpoint,
        interface_id=attachment.interface_id if attachment is not None else None,
        authenticated=False,
    )


def build_namespaced_service_config(
    base_config: InterfaceHostServiceConfig,
    *,
    namespace: str,
    host_label: str | None = None,
    endpoint: str | None = None,
    auth_token: str | None = None,
    environment_config_id: UUID | None = None,
    interface_package_name: str | None = None,
) -> InterfaceHostServiceConfig:
    namespace_value = str(namespace or "").strip()
    if not namespace_value:
        raise ValueError("namespace is required")

    host_label_value = (
        host_label.strip()
        if host_label is not None and host_label.strip()
        else f"{base_config.host_label}-{namespace_value}"
    )
    return replace(
        base_config,
        namespace=namespace_value,
        host_label=host_label_value,
        endpoint=endpoint if endpoint is not None else base_config.endpoint,
        auth_token=auth_token,
        environment_config_id=(
            environment_config_id
            if environment_config_id is not None
            else base_config.environment_config_id
        ),
        interface_package_name=(
            interface_package_name
            if interface_package_name is not None and interface_package_name.strip()
            else base_config.interface_package_name
        ),
        once=False,
    )


async def build_live_service_bundle(
    config: InterfaceHostServiceConfig,
) -> InterfaceHostServiceLiveBundle:
    state_home_raw = str(config.state_home)
    resolved_endpoint = config.endpoint or _resolve_node_endpoint(
        repository_root=config.repository_root
    )
    resolved_environment_config_id = (
        config.environment_config_id
        or _resolve_optional_environment_config_id(config.repository_root)
    )
    if interface_host_dev_adapter_selected(
        endpoint=resolved_endpoint,
        dev_adapter_specs=config.dev_adapter_specs,
    ):
        return _build_dev_adapter_bundle(
            config=config,
            resolved_endpoint=resolved_endpoint,
            resolved_environment_config_id=resolved_environment_config_id,
        )
    persisted_auth = load_interface_auth_session(
        endpoint=resolved_endpoint,
        namespace=config.namespace,
        state_home=state_home_raw,
    )
    if (
        config.require_live_runtime
        and persisted_auth is None
        and config.auth_token is None
    ):
        raise RuntimeError(
            "Interface service live runtime is required for namespace="
            f"{config.namespace!r}, but no auth token or persisted auth session "
            "is available; refusing unauthenticated local shell bootstrap."
        )
    if persisted_auth is None and config.auth_token is None:
        client = AwareApiClient(
            AwareApiConfig(
                endpoint=resolved_endpoint,
                actor_id=_UNAUTHENTICATED_ACTOR_ID,
                context=None,
                request_timeout=config.request_timeout_s,
            )
        )
        attachment = await create_interface_attachment(
            client=client,
            state_home=config.state_home,
            namespace=config.namespace,
            endpoint=resolved_endpoint,
            host_label=config.host_label,
            capabilities=config.capabilities,
            persist_interface_id=False,
        )
        try:
            await attachment.transport_session.ensure_registered()
        except Exception as exc:
            if not _should_degrade_to_local_shell(
                endpoint=resolved_endpoint,
                exc=exc,
                allow_degraded_local_shell=config.allow_degraded_local_shell,
            ):
                raise
            logger.warning(
                "aware_interface_service degrading namespace=%s to local bootstrap "
                "shell after transport registration failed at %s: %s",
                config.namespace,
                resolved_endpoint,
                exc,
            )
            return _validate_live_runtime_requirement(
                config=config,
                bundle=_build_degraded_local_shell_bundle(
                    config=config,
                    resolved_endpoint=resolved_endpoint,
                    resolved_environment_config_id=resolved_environment_config_id,
                    attachment=attachment,
                ),
            )
        interface_config_bundle = _load_local_interface_config_bundle_for_service(
            config=config,
        )
        local_runtime = InterfaceLocalRuntimeController(
            repository_root=config.repository_root,
            state_home=config.state_home,
            namespace=config.namespace,
            endpoint=resolved_endpoint,
            service_host_bootstrap_config_path=(
                config.local_service_host_bootstrap_config_path
            ),
            service_host_implementation_toml_paths=(
                config.local_service_host_implementation_toml_paths
            ),
        )
        runtime = InterfaceHostServiceRuntime(
            repository_root=config.repository_root,
            host_label=config.host_label,
            state_home=config.state_home,
            namespace=config.namespace,
            endpoint=resolved_endpoint,
            environment_id=None,
            environment_config_id=resolved_environment_config_id,
            transport_session=attachment.transport_session,
            host_runtime=None,
            coordinator=None,
            local_runtime=local_runtime,
            workspace_client_provider=None,
            interface_config_bundle=interface_config_bundle,
            bundle_window_layout_enabled=interface_config_bundle is not None,
        )
        return _validate_live_runtime_requirement(
            config=config,
            bundle=InterfaceHostServiceLiveBundle(
                runtime=runtime,
                attachment=attachment,
                bootstrap_result=None,
                endpoint=resolved_endpoint,
                interface_id=attachment.interface_id,
                authenticated=False,
            ),
        )

    if persisted_auth is None and config.auth_token is not None:
        target_coordinates = resolve_interface_session_target_coordinates(
            repository_root=config.repository_root,
            endpoint=resolved_endpoint,
            environment_config_id=resolved_environment_config_id,
        )
        target = InterfaceSessionTarget(
            endpoint=target_coordinates.endpoint,
            environment_config_id=target_coordinates.environment_config_id,
            actor_id=_UNAUTHENTICATED_ACTOR_ID,
            agent_identity_id=None,
            environment_target_reason=target_coordinates.environment_target_reason,
        )
    else:
        target = resolve_interface_session_target(
            repository_root=config.repository_root,
            endpoint=resolved_endpoint,
            environment_config_id=resolved_environment_config_id,
            auth_actor_id=(
                persisted_auth.actor_id if persisted_auth is not None else None
            ),
        )
    actor_id = (
        persisted_auth.actor_id
        if persisted_auth is not None
        else (
            _UNAUTHENTICATED_ACTOR_ID
            if config.auth_token is not None
            else target.actor_id
        )
    )

    client = AwareApiClient(
        AwareApiConfig(
            endpoint=target.endpoint,
            actor_id=actor_id,
            context=None,
            request_timeout=config.request_timeout_s,
        )
    )
    persist_interface_id = not (
        config.auth_token is not None and persisted_auth is None
    )
    attachment = await create_interface_attachment(
        client=client,
        state_home=config.state_home,
        namespace=config.namespace,
        endpoint=target.endpoint,
        host_label=config.host_label,
        capabilities=config.capabilities,
        persist_interface_id=persist_interface_id,
    )
    try:
        await attachment.transport_session.ensure_registered()

        authenticated = persisted_auth is not None
        if config.auth_token is not None:
            login = await attachment.transport_session.login_with_token(
                token=config.auth_token
            )
            authenticated = login.actor_id is not None
            persisted_auth = save_interface_auth_session(
                InterfaceAuthSession(
                    endpoint=target.endpoint,
                    actor_id=client.config.actor_id,
                    public_key=login.public_key,
                    method="auth_token",
                    token_id=login.token_id,
                    token_type=login.token_type,
                    scopes=tuple(login.scopes or []),
                    context_environment_id=login.context_environment_id,
                    context_process_id=login.context_process_id,
                    context_thread_id=login.context_thread_id,
                    saved_at=_utc_now(),
                ),
                namespace=config.namespace,
                state_home=state_home_raw,
            )
            await attachment.persist_interface_id_for_actor(
                actor_id=client.config.actor_id,
            )

        runtime_backend = await _build_interface_host_runtime_backend(
            config=config,
            environment_config_id=target.environment_config_id,
        )
        session_port = InterfaceRuntimeSessionPort(
            client=client,
            interface_id=attachment.interface_id,
            endpoint=target.endpoint,
            state_store=InterfaceRuntimeSessionStateStore(
                state_root=config.state_home,
                namespace=config.namespace,
            ),
            boot_program_ref=_AWARE_CONTROL_BOOT_PROGRAM_REF,
        )
        bootstrap = await session_port.bootstrap(
            environment_config_id=target.environment_config_id,
        )
        bootstrap_context = bootstrap.context
        navigation_context_layout_port = ServiceApiInterfaceNavigationContextLayoutPort(
            transport_session=attachment.transport_session,
            context_environment_id=(
                (
                    persisted_auth.context_environment_id
                    if persisted_auth is not None
                    else None
                )
                or bootstrap.environment_id
            ),
            context_process_id=(
                (
                    persisted_auth.context_process_id
                    if persisted_auth is not None
                    else None
                )
                or bootstrap_context.process_id
            ),
            context_thread_id=(
                (
                    persisted_auth.context_thread_id
                    if persisted_auth is not None
                    else None
                )
                or bootstrap_context.thread_id
            ),
            context_branch_id=bootstrap_context.branch_id,
            context_projection_hash=bootstrap_context.projection_hash,
        )
        coordinator = runtime_backend.build_coordinator(
            session_port=session_port,
            gate_port=EnvironmentInterfaceGatePort(
                repository_root=config.repository_root,
                state_home=config.state_home,
                namespace=config.namespace,
                endpoint=target.endpoint,
                actor_id=client.config.actor_id,
                environment_config_id=bootstrap.environment_config_id,
                auth_session_available=persisted_auth is not None,
                auth_actor_id=(
                    persisted_auth.actor_id if persisted_auth is not None else None
                ),
            ),
            navigation_context_layout_port=navigation_context_layout_port,
        )
        local_runtime = InterfaceLocalRuntimeController(
            repository_root=config.repository_root,
            state_home=config.state_home,
            namespace=config.namespace,
            endpoint=target.endpoint,
            service_host_bootstrap_config_path=(
                config.local_service_host_bootstrap_config_path
            ),
            service_host_implementation_toml_paths=(
                config.local_service_host_implementation_toml_paths
            ),
        )
        runtime = InterfaceHostServiceRuntime(
            repository_root=config.repository_root,
            host_label=config.host_label,
            state_home=config.state_home,
            namespace=config.namespace,
            endpoint=target.endpoint,
            environment_id=bootstrap.environment_id,
            environment_config_id=bootstrap.environment_config_id,
            transport_session=attachment.transport_session,
            host_runtime=runtime_backend,
            coordinator=coordinator,
            local_runtime=local_runtime,
            workspace_client_provider=None,
            interface_config_bundle=runtime_backend.interface_config_bundle,
            bundle_window_layout_enabled=runtime_backend.interface_config_bundle
            is not None,
        )
        return _validate_live_runtime_requirement(
            config=config,
            bundle=InterfaceHostServiceLiveBundle(
                runtime=runtime,
                attachment=attachment,
                bootstrap_result=bootstrap,
                endpoint=target.endpoint,
                interface_id=attachment.interface_id,
                authenticated=authenticated,
            ),
        )
    except Exception as exc:
        if not _should_degrade_to_local_shell(
            endpoint=target.endpoint,
            exc=exc,
            allow_degraded_local_shell=config.allow_degraded_local_shell,
        ):
            raise
        logger.warning(
            "aware_interface_service degrading namespace=%s to local bootstrap "
            "shell after live bundle bootstrap failed at %s: %s",
            config.namespace,
            target.endpoint,
            exc,
        )
        return _validate_live_runtime_requirement(
            config=config,
            bundle=_build_degraded_local_shell_bundle(
                config=config,
                resolved_endpoint=target.endpoint,
                resolved_environment_config_id=target.environment_config_id,
                attachment=attachment,
            ),
        )


def _build_dev_adapter_bundle(
    *,
    config: InterfaceHostServiceConfig,
    resolved_endpoint: str,
    resolved_environment_config_id: UUID | None,
) -> InterfaceHostServiceLiveBundle:
    interface_config_bundle = _load_mock_interface_config_bundle_for_service(
        config=config,
    )
    selection = build_interface_host_dev_adapter_selection(
        endpoint=resolved_endpoint,
        dev_adapter_specs=config.dev_adapter_specs,
        namespace=config.namespace,
        host_label=config.host_label,
        repository_root=config.repository_root,
        state_home=config.state_home,
        interface_config_bundle=interface_config_bundle,
    )
    if selection is None:
        raise RuntimeError(
            "Interface Host dev adapter bundle requested but no adapter was selected."
        )
    adapter = selection.adapter
    runtime = InterfaceHostServiceRuntime(
        repository_root=config.repository_root,
        host_label=config.host_label,
        state_home=config.state_home,
        namespace=config.namespace,
        endpoint=resolved_endpoint,
        environment_id=None,
        environment_config_id=resolved_environment_config_id,
        transport_session=adapter.transport_session,
        host_runtime=adapter,
        coordinator=adapter,
        local_runtime=None,
        workspace_client_provider=None,
        interface_config_bundle=interface_config_bundle,
        bundle_window_layout_enabled=interface_config_bundle is not None,
        mock_service_adapter=adapter,
    )
    return _validate_live_runtime_requirement(
        config=config,
        bundle=InterfaceHostServiceLiveBundle(
            runtime=runtime,
            attachment=None,
            bootstrap_result=None,
            endpoint=resolved_endpoint,
            interface_id=selection.interface_id,
            authenticated=selection.authenticated,
        ),
    )


async def _serve() -> int:
    app = await InterfaceHostServiceApp.create()
    state = await app.start()
    if app.config.once:
        print(json.dumps(_jsonable(state), indent=2, sort_keys=True))
        await app.close()
        return 0

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    logger.info(
        "aware_interface_service ready endpoint=%s actor_id=%s interface_id=%s environment_id=%s",
        app.endpoint,
        state.transport.actor_id,
        state.transport.interface_id,
        state.environment_id,
    )
    try:
        await stop_event.wait()
    finally:
        await app.close()
    return 0


def main() -> int:
    try:
        return asyncio.run(_serve())
    except KeyboardInterrupt:
        return 0


__all__ = [
    "InterfaceHostServiceApp",
    "InterfaceHostServiceBundleFactory",
    "InterfaceHostServiceConfig",
    "InterfaceHostServiceLiveBundle",
    "build_namespaced_service_config",
    "build_bootstrap_snapshot",
    "build_live_service_bundle",
    "main",
]
