from __future__ import annotations

# pyright: reportMissingImports=false, reportAttributeAccessIssue=false

from collections.abc import AsyncIterator
from typing import Any, Protocol, cast
from uuid import UUID

from pydantic import BaseModel
from aware_interface_ontology.stable_ids import (
    stable_interface_session_experience_session_id,
    stable_interface_session_id,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    require_service_ontology_replica_query,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    DescribeExperienceSessionRequest,
)
from aware_identity_service_dto.session.session import SessionDescribeRequest
from aware_types import JsonArray, JsonObject

from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActivateRuntimeFocusRequest as ControlInterfaceActivateRuntimeFocusRequest,
    InterfaceActionRequest as ControlInterfaceActionRequest,
    InterfaceApiEventNotification as ControlInterfaceApiEventNotification,
    InterfaceApiStreamClosedNotification as ControlInterfaceApiStreamClosedNotification,
    InterfaceAdmitEnvironmentActorRequest as ControlInterfaceAdmitEnvironmentActorRequest,
    InterfaceApplyAttentionLayoutTransitionRequest as ControlInterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionRequest as ControlInterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceEnterAppScreenRequest as ControlInterfaceEnterAppScreenRequest,
    InterfaceEnterEnvironmentRequest as ControlInterfaceEnterEnvironmentRequest,
    InterfaceControlPlaneRequest as ControlInterfaceControlPlaneRequest,
    InterfaceControlPlaneResponse as ControlInterfaceControlPlaneResponse,
    InterfaceFollowRequest as ControlInterfaceFollowRequest,
    InterfaceInvokeApiRequest as ControlInterfaceInvokeApiRequest,
    InterfaceJoinEnvironmentSessionRequest as ControlInterfaceJoinEnvironmentSessionRequest,
    InterfaceReportRendererCapabilitiesRequest as ControlInterfaceReportRendererCapabilitiesRequest,
    InterfaceRequestWindowLayoutRequest as ControlInterfaceRequestWindowLayoutRequest,
    InterfaceResolveExperienceLensRequest as ControlInterfaceResolveExperienceLensRequest,
    InterfaceSelectEnvironmentNavigationTargetRequest as ControlInterfaceSelectEnvironmentNavigationTargetRequest,
    InterfaceSelectProfileRequest as ControlInterfaceSelectProfileRequest,
    InterfaceSelectRuntimeLayoutRequest as ControlInterfaceSelectRuntimeLayoutRequest,
    InterfaceSelectStepRequest as ControlInterfaceSelectStepRequest,
    InterfaceStatusRequest as ControlInterfaceStatusRequest,
    InterfaceStopRequest as ControlInterfaceStopRequest,
    InterfaceStreamApiRequest as ControlInterfaceStreamApiRequest,
    InterfaceSyncViewStateCursorRequest as ControlInterfaceSyncViewStateCursorRequest,
    NamespaceEnsureRequest as ControlNamespaceEnsureRequest,
    NamespaceListRequest as ControlNamespaceListRequest,
    PingRequest as ControlPingRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActivateRuntimeFocusRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActivateRuntimeFocusResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTransitionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceAdmitEnvironmentActorRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceAdmitEnvironmentActorResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterEnvironmentRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterEnvironmentResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApiEventNotification,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceApiStreamClosedNotification,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceFollowRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceFollowResponse,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceHostState,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceInvokeApiRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceInvokeApiResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceJoinEnvironmentSessionRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceJoinEnvironmentSessionResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceExperienceSessionMountRequest,
    InterfaceExperienceSessionMountResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSessionDescribeRequest,
    InterfaceSessionDescribeResponse,
    InterfaceSessionExperienceSessionView,
    InterfaceSessionView,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSessionStartRequest,
    InterfaceSessionStartResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectEnvironmentNavigationTargetRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectEnvironmentNavigationTargetResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceReportRendererCapabilitiesRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceReportRendererCapabilitiesResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceRequestWindowLayoutRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceRequestWindowLayoutResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceResolveExperienceLensRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceResolveExperienceLensResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectProfileRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectProfileResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectRuntimeLayoutRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectRuntimeLayoutResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectStepRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSelectStepResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStateNotification,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStatusRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStatusResponse,
)
from aware_interface_service_dto.comms.models.control_plane import InterfaceStopRequest
from aware_interface_service_dto.comms.models.control_plane import InterfaceStopResponse
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStreamApiRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceStreamApiResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSyncViewStateCursorRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceSyncViewStateCursorResponse,
)
from aware_interface_service_dto.comms.models.control_plane import (
    NamespaceEnsureRequest,
)
from aware_interface_service_dto.comms.models.control_plane import (
    NamespaceEnsureResponse,
)
from aware_interface_service_dto.comms.models.control_plane import NamespaceListRequest
from aware_interface_service_dto.comms.models.control_plane import NamespaceListResponse
from aware_interface_service_dto.comms.models.control_plane import PingRequest
from aware_interface_service_dto.comms.models.control_plane import PingResponse
from aware_interface_service_protocol.protocols import (
    ENDPOINT_BINDINGS as INTERFACE_SERVICE_PROTOCOL_ENDPOINT_BINDINGS,
)

from aware_interface_service.control_plane import (
    _host_state_model,
)
from aware_interface_service.host.capabilities.app_screen import (
    MetaCommittedAppScreenResolver,
)


class _InterfaceControlPlanePort(Protocol):
    async def handle_request(
        self,
        request: ControlInterfaceControlPlaneRequest,
        *,
        committed_app_screen_resolver: object | None = None,
    ) -> ControlInterfaceControlPlaneResponse: ...

    async def initial_follow_state(
        self,
        request: ControlInterfaceFollowRequest,
    ) -> Any: ...

    def follow_notifications(
        self,
        request: ControlInterfaceFollowRequest,
        *,
        last_state: object,
        should_stop: object,
    ) -> AsyncIterator[object]: ...

    async def open_api_stream(
        self,
        request: ControlInterfaceStreamApiRequest,
    ) -> Any: ...

    def api_stream_notifications(
        self,
        request: ControlInterfaceStreamApiRequest,
        *,
        handle: object,
        should_stop: object,
    ) -> AsyncIterator[object]: ...


def build_aware_interface_service_protocol_handler(
    *,
    control_plane: _InterfaceControlPlanePort,
    experience_api_client: Any | None = None,
    identity_api_client: Any | None = None,
) -> object:
    return _AwareInterfaceServiceProtocolHandler(
        control_plane=control_plane,
        experience_api_client=experience_api_client,
        identity_api_client=identity_api_client,
    )


class _InterfaceProtocolSupport:
    def __init__(
        self,
        *,
        control_plane: _InterfaceControlPlanePort,
        experience_api_client: Any | None = None,
        identity_api_client: Any | None = None,
    ) -> None:
        self.control_plane = control_plane
        self.experience_api_client = experience_api_client
        self.identity_api_client = identity_api_client

    def identity_session_api_client(self) -> Any:
        if self.identity_api_client is not None:
            return self.identity_api_client
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "InterfaceSession start requires an active host context."
            )
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name="identity-service-api",
            actor_id=host_context.operation_context.actor_id,
            invocation_context=cast(JsonObject | None, host_context.invocation_context),
        )
        if invoker is None:
            raise RuntimeError(
                "InterfaceSession start requires the Identity service API route."
            )
        from aware_identity_service_api import AwareIdentityServiceApiClient

        return AwareIdentityServiceApiClient(invoker)

    def experience_session_api_client(self) -> Any:
        if self.experience_api_client is not None:
            return self.experience_api_client
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires an active host context."
            )
        invoker = build_service_api_client_for_api_package(
            host_context.service_api_dependency_routes,
            api_package_name="experience-service-api",
            actor_id=host_context.operation_context.actor_id,
            invocation_context=cast(JsonObject | None, host_context.invocation_context),
        )
        if invoker is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires the Experience service API route."
            )
        from aware_experience_service_api import AwareExperienceServiceApiClient

        return AwareExperienceServiceApiClient(invoker)

    async def handle_request(
        self,
        request: BaseModel,
        *,
        legacy_request_cls: type[ControlInterfaceControlPlaneRequest],
        response_cls: type[BaseModel],
    ) -> Any:
        legacy_request = _convert_model(request, model_cls=legacy_request_cls)
        legacy_response = await self.control_plane.handle_request(legacy_request)
        if (
            isinstance(legacy_response, ControlInterfaceControlPlaneResponse)
            and not legacy_response.success
        ):
            raise RuntimeError(legacy_response.error or "Interface request failed")
        return _convert_model(legacy_response, model_cls=response_cls)

    async def handle_app_screen_request(
        self,
        request: BaseModel,
        *,
        legacy_request_cls: type[ControlInterfaceControlPlaneRequest],
        response_cls: type[BaseModel],
    ) -> Any:
        legacy_request = _convert_model(request, model_cls=legacy_request_cls)
        legacy_response = await self.control_plane.handle_request(
            legacy_request,
            committed_app_screen_resolver=await self.committed_app_screen_resolver(),
        )
        if (
            isinstance(legacy_response, ControlInterfaceControlPlaneResponse)
            and not legacy_response.success
        ):
            raise RuntimeError(legacy_response.error or "Interface request failed")
        return _convert_model(legacy_response, model_cls=response_cls)

    async def committed_app_screen_resolver(self) -> MetaCommittedAppScreenResolver:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Interface App screen entry requires an active Service API host context."
            )
        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        elif host_context.graph_gateway is not None:
            resolve_graph_context = getattr(
                host_context.graph_gateway,
                "resolve_graph_context",
                None,
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "Interface App screen entry Service graph gateway cannot "
                    "resolve graph context."
                )
            graph_context = await resolve_graph_context()
        else:
            raise RuntimeError(
                "Interface App screen entry requires a committed Service graph context."
            )
        runtime_index = getattr(graph_context, "index", graph_context)
        if not isinstance(runtime_index, MetaGraphRuntimeIndex):
            raise RuntimeError(
                "Interface App screen entry graph context has no Meta runtime index."
            )
        return MetaCommittedAppScreenResolver(index=runtime_index)

    async def start_interface_session(
        self,
        request: InterfaceSessionStartRequest,
    ) -> InterfaceSessionStartResponse:
        name = request.name.strip()
        state = request.state.strip().lower()
        if not name:
            raise ValueError("InterfaceSession name must not be blank.")
        if state != "active":
            raise ValueError(
                "InterfaceSession start currently requires state='active'."
            )

        identity_client = self.identity_session_api_client()
        identity_result = (
            await identity_client.identity.describe_session.describe_session(
                SessionDescribeRequest(session_id=request.identity_session_id)
            )
        )
        identity_session = identity_result.session
        if (
            identity_session is None
            or identity_session.session_id != request.identity_session_id
        ):
            raise RuntimeError(
                "InterfaceSession start requires a committed Identity Session."
            )

        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "InterfaceSession start requires an active Service API host context."
            )
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "InterfaceSession start requires a Service graph gateway."
            )
        actor_id = host_context.operation_context.actor_id
        if actor_id is None:
            raise RuntimeError("InterfaceSession start requires an admitted actor id.")

        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            resolve_graph_context = getattr(
                graph_gateway, "resolve_graph_context", None
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "InterfaceSession graph gateway cannot resolve graph context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        if not hasattr(runtime_index_value, "class_configs_by_id") or not hasattr(
            runtime_index_value, "opg_by_hash"
        ):
            raise RuntimeError(
                "InterfaceSession graph context has no Meta runtime index."
            )
        runtime_index = cast(MetaGraphRuntimeIndex, runtime_index_value)

        projection, class_config = _resolve_interface_session_projection(runtime_index)
        interface_session_id = stable_interface_session_id(
            interface_id=request.interface_id,
            identity_session_id=request.identity_session_id,
            name=name,
        )
        response = await graph_gateway.invoke_function(
            request=MetaGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=interface_session_id,
                domain_projection_hash=str(projection.projection_hash),
                call_target=MetaGraphFunctionCallTarget.opg_constructor,
                object_projection_graph_id=UUID(str(projection.id)),
                function_id=_resolve_interface_session_constructor_id(class_config),
                args=cast(JsonArray, []),
                kwargs=cast(
                    JsonObject,
                    {
                        "interface_id": str(request.interface_id),
                        "identity_session_id": str(request.identity_session_id),
                        "name": name,
                        "state": state,
                    },
                ),
                commit=True,
                publish=False,
            ),
            graph_context=runtime_index,
        )
        result = MetaGraphInvokeFunctionResponse.model_validate(response)
        if result.status.strip().lower() != "succeeded":
            raise RuntimeError(
                f"InterfaceSession constructor failed: {result.error or result.status}"
            )
        if result.root_object_id != interface_session_id:
            raise RuntimeError(
                "InterfaceSession constructor returned a non-canonical root id."
            )
        if result.object_instance_graph_commit_id is None:
            raise RuntimeError(
                "InterfaceSession constructor returned no graph commit id."
            )
        if not result.graph_hash_post:
            raise RuntimeError("InterfaceSession constructor returned no graph hash.")
        return InterfaceSessionStartResponse(
            request_id=request.request_id,
            success=True,
            interface_session_id=interface_session_id,
            interface_id=request.interface_id,
            identity_session_id=request.identity_session_id,
            name=name,
            state=state,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=result.object_instance_graph_commit_id,
            graph_hash_post=result.graph_hash_post,
        )

    async def describe_interface_session(
        self,
        request: InterfaceSessionDescribeRequest,
    ) -> InterfaceSessionDescribeResponse:
        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "InterfaceSession describe requires an active Service API host context."
            )
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "InterfaceSession describe requires a Service graph gateway."
            )

        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            resolve_graph_context = getattr(
                graph_gateway, "resolve_graph_context", None
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "InterfaceSession describe graph gateway cannot resolve graph context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        if not hasattr(runtime_index_value, "class_configs_by_id") or not hasattr(
            runtime_index_value, "opg_by_hash"
        ):
            raise RuntimeError(
                "InterfaceSession describe graph context has no Meta runtime index."
            )
        runtime_index = cast(MetaGraphRuntimeIndex, runtime_index_value)

        interface_projection, interface_class_config = (
            _resolve_interface_session_projection(runtime_index)
        )
        portal_projection, portal_class_config = (
            _resolve_interface_experience_session_projection(runtime_index)
        )
        replica = require_service_ontology_replica_query()
        record = replica.get_class_instance(instance_id=request.interface_session_id)
        if record is None:
            return InterfaceSessionDescribeResponse(
                request_id=request.request_id,
                status="not_found",
                session=None,
            )
        if (
            record.class_config_id != UUID(str(interface_class_config.id))
            or record.projection_hash != str(interface_projection.projection_hash)
            or record.root_object_id != request.interface_session_id
        ):
            raise RuntimeError(
                "InterfaceSession describe found mismatched projection evidence."
            )

        portal_records = replica.find_by_attribute(
            key="interface_session_id",
            value=str(request.interface_session_id),
            class_config_id=UUID(str(portal_class_config.id)),
            projection_hash=str(portal_projection.projection_hash),
        )
        portal_views: list[InterfaceSessionExperienceSessionView] = []
        for portal_record in portal_records:
            if (
                portal_record.class_config_id != UUID(str(portal_class_config.id))
                or portal_record.projection_hash
                != str(portal_projection.projection_hash)
                or portal_record.root_object_id != portal_record.class_instance_id
            ):
                raise RuntimeError(
                    "InterfaceSession describe found mismatched portal projection evidence."
                )
            portal_attributes = portal_record.attributes
            portal_views.append(
                InterfaceSessionExperienceSessionView(
                    interface_session_experience_session_id=(
                        portal_record.class_instance_id
                    ),
                    experience_session_id=UUID(
                        str(portal_attributes["experience_session_id"])
                    ),
                    status=str(portal_attributes["status"]),
                    metadata_json=cast(
                        JsonObject,
                        dict(portal_attributes.get("metadata_json") or {}),
                    ),
                    domain_commit_id=portal_record.updated_commit_id,
                )
            )
        portal_views.sort(
            key=lambda view: str(view.interface_session_experience_session_id)
        )

        attributes = record.attributes
        return InterfaceSessionDescribeResponse(
            request_id=request.request_id,
            status="found",
            session=InterfaceSessionView(
                interface_session_id=request.interface_session_id,
                interface_id=UUID(str(attributes["interface_id"])),
                identity_session_id=UUID(str(attributes["identity_session_id"])),
                name=str(attributes["name"]),
                state=str(attributes["state"]),
                domain_commit_id=record.updated_commit_id,
                experience_sessions=portal_views,
            ),
        )

    async def mount_interface_experience_session(
        self,
        request: InterfaceExperienceSessionMountRequest,
    ) -> InterfaceExperienceSessionMountResponse:
        status = request.status.strip().lower()
        if not status:
            raise ValueError(
                "Interface ExperienceSession mount status must not be blank."
            )
        metadata_json = cast(JsonObject, dict(request.metadata_json or {}))

        host_context = current_service_api_host_context()
        if host_context is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires an active Service API "
                "host context."
            )
        graph_gateway = host_context.graph_gateway
        if graph_gateway is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires a Service graph gateway."
            )
        actor_id = host_context.operation_context.actor_id
        if actor_id is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires an admitted actor id."
            )

        graph_context: object
        if host_context.materialization is not None:
            graph_context = host_context.materialization.graph_context
        elif host_context.graph_context_provider is not None:
            graph_context = (
                await host_context.graph_context_provider.resolve_graph_context()
            )
        else:
            resolve_graph_context = getattr(
                graph_gateway, "resolve_graph_context", None
            )
            if not callable(resolve_graph_context):
                raise RuntimeError(
                    "Interface ExperienceSession graph gateway cannot resolve graph "
                    "context."
                )
            graph_context = await resolve_graph_context()
        runtime_index_value = getattr(graph_context, "index", graph_context)
        if not hasattr(runtime_index_value, "class_configs_by_id") or not hasattr(
            runtime_index_value, "opg_by_hash"
        ):
            raise RuntimeError(
                "Interface ExperienceSession graph context has no Meta runtime index."
            )
        runtime_index = cast(MetaGraphRuntimeIndex, runtime_index_value)

        interface_projection, interface_class_config = (
            _resolve_interface_session_projection(runtime_index)
        )
        interface_record = require_service_ontology_replica_query().get_class_instance(
            instance_id=request.interface_session_id
        )
        if interface_record is None:
            raise RuntimeError(
                "Interface ExperienceSession mount requires a committed InterfaceSession."
            )
        if (
            interface_record.class_config_id != UUID(str(interface_class_config.id))
            or interface_record.projection_hash
            != str(interface_projection.projection_hash)
            or interface_record.root_object_id != request.interface_session_id
        ):
            raise RuntimeError(
                "Interface ExperienceSession mount found mismatched InterfaceSession evidence."
            )

        experience_client = self.experience_session_api_client()
        experience_result = await experience_client.experience.describe_experience_session.describe_experience_session(
            DescribeExperienceSessionRequest(
                experience_session_id=request.experience_session_id
            )
        )
        experience_session = experience_result.session
        if (
            experience_session is None
            or experience_session.experience_session_id != request.experience_session_id
        ):
            raise RuntimeError(
                "Interface ExperienceSession mount requires a committed ExperienceSession."
            )
        interface_identity_session_id = UUID(
            str(interface_record.attributes["identity_session_id"])
        )
        if experience_session.identity_session_id != interface_identity_session_id:
            raise RuntimeError(
                "Interface ExperienceSession mount requires matching Identity Session provenance."
            )

        projection, class_config = _resolve_interface_experience_session_projection(
            runtime_index
        )
        mount_id = stable_interface_session_experience_session_id(
            interface_session_id=request.interface_session_id,
            experience_session_id=request.experience_session_id,
        )
        response = await graph_gateway.invoke_function(
            request=MetaGraphInvokeFunctionRequest(
                actor_id=actor_id,
                domain_branch_id=mount_id,
                domain_projection_hash=str(projection.projection_hash),
                call_target=MetaGraphFunctionCallTarget.opg_constructor,
                object_projection_graph_id=UUID(str(projection.id)),
                function_id=_resolve_interface_experience_session_constructor_id(
                    class_config
                ),
                args=cast(JsonArray, []),
                kwargs=cast(
                    JsonObject,
                    {
                        "interface_session_id": str(request.interface_session_id),
                        "experience_session_id": str(request.experience_session_id),
                        "status": status,
                        "metadata_json": metadata_json,
                    },
                ),
                commit=True,
                publish=False,
            ),
            graph_context=runtime_index,
        )
        result = MetaGraphInvokeFunctionResponse.model_validate(response)
        if result.status.strip().lower() != "succeeded":
            raise RuntimeError(
                "Interface ExperienceSession mount constructor failed: "
                f"{result.error or result.status}"
            )
        if result.root_object_id != mount_id:
            raise RuntimeError(
                "Interface ExperienceSession mount constructor returned a "
                "non-canonical root id."
            )
        if result.object_instance_graph_commit_id is None:
            raise RuntimeError(
                "Interface ExperienceSession mount constructor returned no graph "
                "commit id."
            )
        if not result.graph_hash_post:
            raise RuntimeError(
                "Interface ExperienceSession mount constructor returned no graph hash."
            )
        return InterfaceExperienceSessionMountResponse(
            request_id=request.request_id,
            success=True,
            interface_session_experience_session_id=mount_id,
            interface_session_id=request.interface_session_id,
            experience_session_id=request.experience_session_id,
            status=status,
            metadata_json=metadata_json,
            domain_commit_id=result.domain_commit_id,
            object_instance_graph_commit_id=result.object_instance_graph_commit_id,
            graph_hash_post=result.graph_hash_post,
        )


def _resolve_interface_session_projection(
    runtime_index: MetaGraphRuntimeIndex,
) -> tuple[Any, Any]:
    class_configs_by_id = cast(Any, runtime_index.class_configs_by_id)
    projections = list(cast(Any, runtime_index.opg_by_hash).values())
    matches: list[tuple[Any, Any]] = []
    for projection in projections:
        if (getattr(projection, "name", "") or "").strip() != "InterfaceSession":
            continue
        for node in projection.object_projection_graph_nodes or []:
            if not node.is_root:
                continue
            class_config = class_configs_by_id.get(node.class_config_id)
            if class_config is not None and (
                (getattr(class_config, "name", "") or "").strip() == "InterfaceSession"
            ):
                matches.append((projection, class_config))
    if len(matches) != 1:
        raise RuntimeError(
            "InterfaceSession projection root is missing or ambiguous: "
            f"matches={len(matches)}"
        )
    return matches[0]


def _resolve_interface_session_constructor_id(class_config: Any) -> UUID:
    matches = [
        function_config.id
        for link in class_config.class_config_function_configs or []
        for function_config in [link.function_config]
        if function_config is not None
        and (function_config.name or "").strip() == "build_via_interface"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "InterfaceSession build_via_interface constructor is missing or ambiguous: "
            f"matches={len(matches)}"
        )
    return UUID(str(matches[0]))


def _resolve_interface_experience_session_projection(
    runtime_index: MetaGraphRuntimeIndex,
) -> tuple[Any, Any]:
    class_configs_by_id = cast(Any, runtime_index.class_configs_by_id)
    projections = list(cast(Any, runtime_index.opg_by_hash).values())
    matches: list[tuple[Any, Any]] = []
    for projection in projections:
        if (
            getattr(projection, "name", "") or ""
        ).strip() != "InterfaceSessionExperienceSession":
            continue
        for node in projection.object_projection_graph_nodes or []:
            if not node.is_root:
                continue
            class_config = class_configs_by_id.get(node.class_config_id)
            if class_config is not None and (
                (getattr(class_config, "name", "") or "").strip()
                == "InterfaceSessionExperienceSession"
            ):
                matches.append((projection, class_config))
    if len(matches) != 1:
        raise RuntimeError(
            "InterfaceSessionExperienceSession projection root is missing or "
            f"ambiguous: matches={len(matches)}"
        )
    return matches[0]


def _resolve_interface_experience_session_constructor_id(
    class_config: Any,
) -> UUID:
    matches = [
        function_config.id
        for link in class_config.class_config_function_configs or []
        for function_config in [link.function_config]
        if function_config is not None
        and (function_config.name or "").strip() == "build_via_interface_session"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "InterfaceSessionExperienceSession build_via_interface_session "
            f"constructor is missing or ambiguous: matches={len(matches)}"
        )
    return UUID(str(matches[0]))


class _AdmitInterfaceCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def admit_interface(
        self,
        request: NamespaceEnsureRequest,
    ) -> NamespaceEnsureResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlNamespaceEnsureRequest,
            response_cls=NamespaceEnsureResponse,
        )


class _StartInterfaceSessionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def start_interface_session(
        self,
        request: InterfaceSessionStartRequest,
    ) -> InterfaceSessionStartResponse:
        return await self._support.start_interface_session(request)


class _DescribeInterfaceSessionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def describe_interface_session(
        self,
        request: InterfaceSessionDescribeRequest,
    ) -> InterfaceSessionDescribeResponse:
        return await self._support.describe_interface_session(request)


class _MountInterfaceExperienceSessionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def mount_interface_experience_session(
        self,
        request: InterfaceExperienceSessionMountRequest,
    ) -> InterfaceExperienceSessionMountResponse:
        return await self._support.mount_interface_experience_session(request)


class _GetInterfaceStateCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def get_interface_state(
        self,
        request: InterfaceStatusRequest,
    ) -> InterfaceStatusResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceStatusRequest,
            response_cls=InterfaceStatusResponse,
        )


class _AdmitEnvironmentActorCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def admit_environment_actor(
        self,
        request: InterfaceAdmitEnvironmentActorRequest,
    ) -> InterfaceAdmitEnvironmentActorResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceAdmitEnvironmentActorRequest,
            response_cls=InterfaceAdmitEnvironmentActorResponse,
        )


class _JoinEnvironmentSessionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def join_environment_session(
        self,
        request: InterfaceJoinEnvironmentSessionRequest,
    ) -> InterfaceJoinEnvironmentSessionResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceJoinEnvironmentSessionRequest,
            response_cls=InterfaceJoinEnvironmentSessionResponse,
        )


class _SelectEnvironmentNavigationTargetCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def select_environment_navigation_target(
        self,
        request: InterfaceSelectEnvironmentNavigationTargetRequest,
    ) -> InterfaceSelectEnvironmentNavigationTargetResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceSelectEnvironmentNavigationTargetRequest,
            response_cls=InterfaceSelectEnvironmentNavigationTargetResponse,
        )


class _EnterEnvironmentCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def enter_environment(
        self,
        request: InterfaceEnterEnvironmentRequest,
    ) -> InterfaceEnterEnvironmentResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceEnterEnvironmentRequest,
            response_cls=InterfaceEnterEnvironmentResponse,
        )


class _EnterAppScreenCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def enter_app_screen(
        self,
        request: InterfaceEnterAppScreenRequest,
    ) -> InterfaceEnterAppScreenResponse:
        return await self._support.handle_app_screen_request(
            request,
            legacy_request_cls=ControlInterfaceEnterAppScreenRequest,
            response_cls=InterfaceEnterAppScreenResponse,
        )


class _ResolveExperienceLensCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def resolve_experience_lens(
        self,
        request: InterfaceResolveExperienceLensRequest,
    ) -> InterfaceResolveExperienceLensResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceResolveExperienceLensRequest,
            response_cls=InterfaceResolveExperienceLensResponse,
        )


class _WatchInterfaceStateCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def watch_interface_state(
        self,
        request: InterfaceFollowRequest,
    ) -> InterfaceFollowResponse:
        legacy_request = _convert_model(
            request,
            model_cls=ControlInterfaceFollowRequest,
        )
        state = await self._support.control_plane.initial_follow_state(legacy_request)
        return InterfaceFollowResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            host_state=_convert_model(
                _host_state_model(state),
                model_cls=InterfaceHostState,
            ),
        )

    async def stream_watch_interface_state(
        self,
        request: InterfaceFollowRequest,
    ) -> AsyncIterator[InterfaceStateNotification]:
        legacy_request = _convert_model(
            request,
            model_cls=ControlInterfaceFollowRequest,
        )
        initial_state = await self._support.control_plane.initial_follow_state(
            legacy_request,
        )
        async for notification in self._support.control_plane.follow_notifications(
            legacy_request,
            last_state=initial_state,
            should_stop=lambda: False,
        ):
            yield _convert_model(
                notification,
                model_cls=InterfaceStateNotification,
            )


class _PerformInterfaceActionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def perform_interface_action(
        self,
        request: InterfaceActionRequest,
    ) -> InterfaceActionResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceActionRequest,
            response_cls=InterfaceActionResponse,
        )


class _SelectInterfaceStepCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def select_interface_step(
        self,
        request: InterfaceSelectStepRequest,
    ) -> InterfaceSelectStepResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceSelectStepRequest,
            response_cls=InterfaceSelectStepResponse,
        )


class _SelectInterfaceProfileCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def select_interface_profile(
        self,
        request: InterfaceSelectProfileRequest,
    ) -> InterfaceSelectProfileResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceSelectProfileRequest,
            response_cls=InterfaceSelectProfileResponse,
        )


class _SelectInterfaceRuntimeLayoutCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def select_interface_runtime_layout(
        self,
        request: InterfaceSelectRuntimeLayoutRequest,
    ) -> InterfaceSelectRuntimeLayoutResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceSelectRuntimeLayoutRequest,
            response_cls=InterfaceSelectRuntimeLayoutResponse,
        )


class _ActivateInterfaceRuntimeFocusCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def activate_interface_runtime_focus(
        self,
        request: InterfaceActivateRuntimeFocusRequest,
    ) -> InterfaceActivateRuntimeFocusResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceActivateRuntimeFocusRequest,
            response_cls=InterfaceActivateRuntimeFocusResponse,
        )


class _RequestInterfaceWindowLayoutCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def request_interface_window_layout(
        self,
        request: InterfaceRequestWindowLayoutRequest,
    ) -> InterfaceRequestWindowLayoutResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceRequestWindowLayoutRequest,
            response_cls=InterfaceRequestWindowLayoutResponse,
        )


class _ApplyAttentionLayoutTransitionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def apply_attention_layout_transition(
        self,
        request: InterfaceApplyAttentionLayoutTransitionRequest,
    ) -> InterfaceApplyAttentionLayoutTransitionResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceApplyAttentionLayoutTransitionRequest,
            response_cls=InterfaceApplyAttentionLayoutTransitionResponse,
        )


class _ApplyAttentionLayoutTopologyTransitionCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def apply_attention_layout_topology_transition(
        self,
        request: InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=(
                ControlInterfaceApplyAttentionLayoutTopologyTransitionRequest
            ),
            response_cls=InterfaceApplyAttentionLayoutTopologyTransitionResponse,
        )


class _InvokeInterfaceApiCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def invoke_interface_api(
        self,
        request: InterfaceInvokeApiRequest,
    ) -> InterfaceInvokeApiResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceInvokeApiRequest,
            response_cls=InterfaceInvokeApiResponse,
        )


class _StreamInterfaceApiCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def stream_interface_api(
        self,
        request: InterfaceStreamApiRequest,
    ) -> InterfaceStreamApiResponse:
        legacy_request = _convert_model(
            request,
            model_cls=ControlInterfaceStreamApiRequest,
        )
        handle = await self._support.control_plane.open_api_stream(legacy_request)
        await handle.close()
        return InterfaceStreamApiResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            endpoint_ref=request.endpoint_ref,
            discriminant=request.discriminant,
        )

    async def stream_stream_interface_api(
        self,
        request: InterfaceStreamApiRequest,
    ) -> AsyncIterator[
        InterfaceApiStreamClosedNotification | InterfaceApiEventNotification
    ]:
        legacy_request = _convert_model(
            request,
            model_cls=ControlInterfaceStreamApiRequest,
        )
        handle = await self._support.control_plane.open_api_stream(legacy_request)
        async for notification in self._support.control_plane.api_stream_notifications(
            legacy_request,
            handle=handle,
            should_stop=lambda: False,
        ):
            if isinstance(notification, ControlInterfaceApiEventNotification):
                yield _convert_model(
                    notification,
                    model_cls=InterfaceApiEventNotification,
                )
            elif isinstance(notification, ControlInterfaceApiStreamClosedNotification):
                yield _convert_model(
                    notification,
                    model_cls=InterfaceApiStreamClosedNotification,
                )


class _ReportRendererCapabilitiesCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def report_renderer_capabilities(
        self,
        request: InterfaceReportRendererCapabilitiesRequest,
    ) -> InterfaceReportRendererCapabilitiesResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceReportRendererCapabilitiesRequest,
            response_cls=InterfaceReportRendererCapabilitiesResponse,
        )


class _SyncViewStateCursorCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def sync_view_state_cursor(
        self,
        request: InterfaceSyncViewStateCursorRequest,
    ) -> InterfaceSyncViewStateCursorResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceSyncViewStateCursorRequest,
            response_cls=InterfaceSyncViewStateCursorResponse,
        )


class _PingInterfaceHostCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def ping_interface_host(self, request: PingRequest) -> PingResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlPingRequest,
            response_cls=PingResponse,
        )


class _ListInterfaceNamespacesCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def list_interface_namespaces(
        self,
        request: NamespaceListRequest,
    ) -> NamespaceListResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlNamespaceListRequest,
            response_cls=NamespaceListResponse,
        )


class _StopInterfaceNamespaceCapabilityHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self._support = support

    async def stop_interface_namespace(
        self,
        request: InterfaceStopRequest,
    ) -> InterfaceStopResponse:
        return await self._support.handle_request(
            request,
            legacy_request_cls=ControlInterfaceStopRequest,
            response_cls=InterfaceStopResponse,
        )


class _InterfaceApiServiceProtocolHandler:
    def __init__(self, *, support: _InterfaceProtocolSupport) -> None:
        self.admit_interface = _AdmitInterfaceCapabilityHandler(support=support)
        self.start_interface_session = _StartInterfaceSessionCapabilityHandler(
            support=support,
        )
        self.describe_interface_session = _DescribeInterfaceSessionCapabilityHandler(
            support=support,
        )
        self.mount_interface_experience_session = (
            _MountInterfaceExperienceSessionCapabilityHandler(support=support)
        )
        self.get_interface_state = _GetInterfaceStateCapabilityHandler(
            support=support,
        )
        self.admit_environment_actor = _AdmitEnvironmentActorCapabilityHandler(
            support=support,
        )
        self.join_environment_session = _JoinEnvironmentSessionCapabilityHandler(
            support=support,
        )
        self.select_environment_navigation_target = (
            _SelectEnvironmentNavigationTargetCapabilityHandler(support=support)
        )
        self.enter_environment = _EnterEnvironmentCapabilityHandler(
            support=support,
        )
        self.enter_app_screen = _EnterAppScreenCapabilityHandler(
            support=support,
        )
        self.resolve_experience_lens = _ResolveExperienceLensCapabilityHandler(
            support=support,
        )
        self.watch_interface_state = _WatchInterfaceStateCapabilityHandler(
            support=support,
        )
        self.perform_interface_action = _PerformInterfaceActionCapabilityHandler(
            support=support,
        )
        self.select_interface_step = _SelectInterfaceStepCapabilityHandler(
            support=support,
        )
        self.select_interface_profile = _SelectInterfaceProfileCapabilityHandler(
            support=support,
        )
        self.select_interface_runtime_layout = (
            _SelectInterfaceRuntimeLayoutCapabilityHandler(support=support)
        )
        self.activate_interface_runtime_focus = (
            _ActivateInterfaceRuntimeFocusCapabilityHandler(support=support)
        )
        self.request_interface_window_layout = (
            _RequestInterfaceWindowLayoutCapabilityHandler(support=support)
        )
        self.apply_attention_layout_transition = (
            _ApplyAttentionLayoutTransitionCapabilityHandler(support=support)
        )
        self.apply_attention_layout_topology_transition = (
            _ApplyAttentionLayoutTopologyTransitionCapabilityHandler(support=support)
        )
        self.invoke_interface_api = _InvokeInterfaceApiCapabilityHandler(
            support=support,
        )
        self.stream_interface_api = _StreamInterfaceApiCapabilityHandler(
            support=support,
        )
        self.report_renderer_capabilities = (
            _ReportRendererCapabilitiesCapabilityHandler(support=support)
        )
        self.sync_view_state_cursor = _SyncViewStateCursorCapabilityHandler(
            support=support,
        )
        self.ping_interface_host = _PingInterfaceHostCapabilityHandler(
            support=support,
        )
        self.list_interface_namespaces = _ListInterfaceNamespacesCapabilityHandler(
            support=support,
        )
        self.stop_interface_namespace = _StopInterfaceNamespaceCapabilityHandler(
            support=support,
        )


class _AwareInterfaceServiceProtocolHandler:
    def __init__(
        self,
        *,
        control_plane: _InterfaceControlPlanePort,
        experience_api_client: Any | None = None,
        identity_api_client: Any | None = None,
    ) -> None:
        support = _InterfaceProtocolSupport(
            control_plane=control_plane,
            experience_api_client=experience_api_client,
            identity_api_client=identity_api_client,
        )
        self.interface = _InterfaceApiServiceProtocolHandler(support=support)


def _convert_model(value: object, *, model_cls: type[BaseModel]) -> Any:
    payload = value
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=True)
    return model_cls.model_validate(payload)


__all__ = [
    "INTERFACE_SERVICE_PROTOCOL_ENDPOINT_BINDINGS",
    "build_aware_interface_service_protocol_handler",
]
