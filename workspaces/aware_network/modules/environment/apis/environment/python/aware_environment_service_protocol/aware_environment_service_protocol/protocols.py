# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_environment_service_dto.environment.environment import (
    AdmitEnvironmentActorRequest,
    AdmitEnvironmentActorResponse,
    AttachEnvironmentOntologyRequest,
    AttachEnvironmentOntologyResponse,
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    CreateEnvironmentNavigationContextRequest,
    CreateEnvironmentNavigationContextResponse,
    DescribeEnvironmentConfigRequest,
    DescribeEnvironmentConfigResponse,
    DescribeEnvironmentNavigationContextRequest,
    DescribeEnvironmentNavigationContextResponse,
    DescribeEnvironmentRequest,
    DescribeEnvironmentResponse,
    DescribeEnvironmentSessionRequest,
    DescribeEnvironmentSessionResponse,
    DescribeEnvironmentStatusRequest,
    DescribeEnvironmentStatusResponse,
    DescribeEnvironmentTopologyRequest,
    DescribeEnvironmentTopologyResponse,
    EnsureEnvironmentOntologyRuntimeRequest,
    EnsureEnvironmentOntologyRuntimeResponse,
    EnsureReadyRequest,
    EnsureReadyResponse,
    FetchCapabilitiesRequest,
    FetchCapabilitiesResponse,
    GetLaneHeadRequest,
    GetLaneHeadResponse,
    GetObjectInstanceGraphCommitRequest,
    GetObjectInstanceGraphCommitResponse,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
    JoinEnvironmentSessionRequest,
    JoinEnvironmentSessionResponse,
    ListEnvironmentNavigationContextsRequest,
    ListEnvironmentNavigationContextsResponse,
    ListEnvironmentOntologiesRequest,
    ListEnvironmentOntologiesResponse,
    MaterializeCommittedProjectionDtoRequest,
    MaterializeCommittedProjectionDtoResponse,
    MountEnvironmentSessionAttentionRequest,
    MountEnvironmentSessionAttentionResponse,
    ProvisionEnvironmentProfileRequest,
    ProvisionEnvironmentProfileResponse,
    ResolveEnvironmentSessionAttentionRequest,
    ResolveEnvironmentSessionAttentionResponse,
    ResolveRuntimeRefsRequest,
    ResolveRuntimeRefsResponse,
    SelectEnvironmentNavigationTargetRequest,
    SelectEnvironmentNavigationTargetResponse,
    StartEnvironmentSessionRequest,
    StartEnvironmentSessionResponse,
    UpsertEnvironmentProfileRequest,
    UpsertEnvironmentProfileResponse,
)

API_PACKAGE_NAME: Final[str] = "environment-service-api"
API_FQN_PREFIX: Final[str] = "aware_environment_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_environment_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_environment__actor_admission__admit_actor(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AdmitEnvironmentActorResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = AdmitEnvironmentActorRequest.model_validate(request)
    return await typed_handler.environment.actor_admission.admit_actor(typed_request)


ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF: Final[str] = "environment.actor_admission.admit_actor"
ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF,
        api_name="environment",
        capability_name="actor_admission",
        endpoint_name="admit_actor",
        request_type_ref="aware_environment_service_dto.environment.AdmitEnvironmentActorRequest",
        response_type_ref="aware_environment_service_dto.environment.AdmitEnvironmentActorResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__actor_admission__admit_actor,
    )
)


async def invoke_environment__capabilities__fetch_capabilities(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> FetchCapabilitiesResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = FetchCapabilitiesRequest.model_validate(request)
    return await typed_handler.environment.capabilities.fetch_capabilities(typed_request)


ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF: Final[str] = "environment.capabilities.fetch_capabilities"
ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF,
        api_name="environment",
        capability_name="capabilities",
        endpoint_name="fetch_capabilities",
        request_type_ref="aware_environment_service_dto.environment.FetchCapabilitiesRequest",
        response_type_ref="aware_environment_service_dto.environment.FetchCapabilitiesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__capabilities__fetch_capabilities,
    )
)


async def invoke_environment__committed_projection_dto__materialize_committed_projection_dto(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MaterializeCommittedProjectionDtoResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = MaterializeCommittedProjectionDtoRequest.model_validate(request)
    return await typed_handler.environment.committed_projection_dto.materialize_committed_projection_dto(typed_request)


ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF: Final[str] = (
    "environment.committed_projection_dto.materialize_committed_projection_dto"
)
ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF,
    api_name="environment",
    capability_name="committed_projection_dto",
    endpoint_name="materialize_committed_projection_dto",
    request_type_ref="aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoRequest",
    response_type_ref="aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_environment__committed_projection_dto__materialize_committed_projection_dto,
)


async def invoke_environment__describe__describe_environment(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentRequest.model_validate(request)
    return await typed_handler.environment.describe.describe_environment(typed_request)


ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF: Final[str] = "environment.describe.describe_environment"
ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF,
        api_name="environment",
        capability_name="describe",
        endpoint_name="describe_environment",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__describe__describe_environment,
    )
)


async def invoke_environment__describe_config__describe_environment_config(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentConfigResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentConfigRequest.model_validate(request)
    return await typed_handler.environment.describe_config.describe_environment_config(typed_request)


ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF: Final[str] = (
    "environment.describe_config.describe_environment_config"
)
ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF,
        api_name="environment",
        capability_name="describe_config",
        endpoint_name="describe_environment_config",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentConfigRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentConfigResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__describe_config__describe_environment_config,
    )
)


async def invoke_environment__function_call__invoke_function(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InvokeFunctionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = InvokeFunctionRequest.model_validate(request)
    return await typed_handler.environment.function_call.invoke_function(typed_request)


ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "environment.function_call.invoke_function"
ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF,
        api_name="environment",
        capability_name="function_call",
        endpoint_name="invoke_function",
        request_type_ref="aware_environment_service_dto.environment.InvokeFunctionRequest",
        response_type_ref="aware_environment_service_dto.environment.InvokeFunctionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__function_call__invoke_function,
    )
)


async def invoke_environment__lane_head__get_lane_head(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetLaneHeadResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = GetLaneHeadRequest.model_validate(request)
    return await typed_handler.environment.lane_head.get_lane_head(typed_request)


ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "environment.lane_head.get_lane_head"
ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF,
        api_name="environment",
        capability_name="lane_head",
        endpoint_name="get_lane_head",
        request_type_ref="aware_environment_service_dto.environment.GetLaneHeadRequest",
        response_type_ref="aware_environment_service_dto.environment.GetLaneHeadResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__lane_head__get_lane_head,
    )
)


async def invoke_environment__navigation__create_navigation_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> CreateEnvironmentNavigationContextResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = CreateEnvironmentNavigationContextRequest.model_validate(request)
    return await typed_handler.environment.navigation.create_navigation_context(typed_request)


ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "environment.navigation.create_navigation_context"
)
ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF,
        api_name="environment",
        capability_name="navigation",
        endpoint_name="create_navigation_context",
        request_type_ref="aware_environment_service_dto.environment.CreateEnvironmentNavigationContextRequest",
        response_type_ref="aware_environment_service_dto.environment.CreateEnvironmentNavigationContextResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__navigation__create_navigation_context,
    )
)


async def invoke_environment__navigation__describe_navigation_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentNavigationContextResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentNavigationContextRequest.model_validate(request)
    return await typed_handler.environment.navigation.describe_navigation_context(typed_request)


ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "environment.navigation.describe_navigation_context"
)
ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF,
        api_name="environment",
        capability_name="navigation",
        endpoint_name="describe_navigation_context",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__navigation__describe_navigation_context,
    )
)


async def invoke_environment__navigation__list_navigation_contexts(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ListEnvironmentNavigationContextsResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ListEnvironmentNavigationContextsRequest.model_validate(request)
    return await typed_handler.environment.navigation.list_navigation_contexts(typed_request)


ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF: Final[str] = (
    "environment.navigation.list_navigation_contexts"
)
ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF,
        api_name="environment",
        capability_name="navigation",
        endpoint_name="list_navigation_contexts",
        request_type_ref="aware_environment_service_dto.environment.ListEnvironmentNavigationContextsRequest",
        response_type_ref="aware_environment_service_dto.environment.ListEnvironmentNavigationContextsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__navigation__list_navigation_contexts,
    )
)


async def invoke_environment__navigation__select_navigation_target(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SelectEnvironmentNavigationTargetResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = SelectEnvironmentNavigationTargetRequest.model_validate(request)
    return await typed_handler.environment.navigation.select_navigation_target(typed_request)


ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF: Final[str] = (
    "environment.navigation.select_navigation_target"
)
ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF,
        api_name="environment",
        capability_name="navigation",
        endpoint_name="select_navigation_target",
        request_type_ref="aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetRequest",
        response_type_ref="aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__navigation__select_navigation_target,
    )
)


async def invoke_environment__object_instance_graph_commit__get_object_instance_graph_commit(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetObjectInstanceGraphCommitResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = GetObjectInstanceGraphCommitRequest.model_validate(request)
    return await typed_handler.environment.object_instance_graph_commit.get_object_instance_graph_commit(typed_request)


ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = (
    "environment.object_instance_graph_commit.get_object_instance_graph_commit"
)
ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    api_name="environment",
    capability_name="object_instance_graph_commit",
    endpoint_name="get_object_instance_graph_commit",
    request_type_ref="aware_environment_service_dto.environment.GetObjectInstanceGraphCommitRequest",
    response_type_ref="aware_environment_service_dto.environment.GetObjectInstanceGraphCommitResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_environment__object_instance_graph_commit__get_object_instance_graph_commit,
)


async def invoke_environment__ontology__attach_environment_ontology(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AttachEnvironmentOntologyResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = AttachEnvironmentOntologyRequest.model_validate(request)
    return await typed_handler.environment.ontology.attach_environment_ontology(typed_request)


ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF: Final[str] = (
    "environment.ontology.attach_environment_ontology"
)
ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF,
        api_name="environment",
        capability_name="ontology",
        endpoint_name="attach_environment_ontology",
        request_type_ref="aware_environment_service_dto.environment.AttachEnvironmentOntologyRequest",
        response_type_ref="aware_environment_service_dto.environment.AttachEnvironmentOntologyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__ontology__attach_environment_ontology,
    )
)


async def invoke_environment__ontology__ensure_environment_ontology_runtime(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EnsureEnvironmentOntologyRuntimeResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = EnsureEnvironmentOntologyRuntimeRequest.model_validate(request)
    return await typed_handler.environment.ontology.ensure_environment_ontology_runtime(typed_request)


ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF: Final[str] = (
    "environment.ontology.ensure_environment_ontology_runtime"
)
ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF,
        api_name="environment",
        capability_name="ontology",
        endpoint_name="ensure_environment_ontology_runtime",
        request_type_ref="aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeRequest",
        response_type_ref="aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__ontology__ensure_environment_ontology_runtime,
    )
)


async def invoke_environment__ontology__list_environment_ontologies(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ListEnvironmentOntologiesResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ListEnvironmentOntologiesRequest.model_validate(request)
    return await typed_handler.environment.ontology.list_environment_ontologies(typed_request)


ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF: Final[str] = (
    "environment.ontology.list_environment_ontologies"
)
ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF,
        api_name="environment",
        capability_name="ontology",
        endpoint_name="list_environment_ontologies",
        request_type_ref="aware_environment_service_dto.environment.ListEnvironmentOntologiesRequest",
        response_type_ref="aware_environment_service_dto.environment.ListEnvironmentOntologiesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__ontology__list_environment_ontologies,
    )
)


async def invoke_environment__profile__provision_environment_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ProvisionEnvironmentProfileResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ProvisionEnvironmentProfileRequest.model_validate(request)
    return await typed_handler.environment.profile.provision_environment_profile(typed_request)


ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "environment.profile.provision_environment_profile"
)
ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF,
        api_name="environment",
        capability_name="profile",
        endpoint_name="provision_environment_profile",
        request_type_ref="aware_environment_service_dto.environment.ProvisionEnvironmentProfileRequest",
        response_type_ref="aware_environment_service_dto.environment.ProvisionEnvironmentProfileResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__profile__provision_environment_profile,
    )
)


async def invoke_environment__profile__upsert_environment_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> UpsertEnvironmentProfileResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = UpsertEnvironmentProfileRequest.model_validate(request)
    return await typed_handler.environment.profile.upsert_environment_profile(typed_request)


ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "environment.profile.upsert_environment_profile"
)
ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF,
        api_name="environment",
        capability_name="profile",
        endpoint_name="upsert_environment_profile",
        request_type_ref="aware_environment_service_dto.environment.UpsertEnvironmentProfileRequest",
        response_type_ref="aware_environment_service_dto.environment.UpsertEnvironmentProfileResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__profile__upsert_environment_profile,
    )
)


async def invoke_environment__ready__ensure_ready(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EnsureReadyResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = EnsureReadyRequest.model_validate(request)
    return await typed_handler.environment.ready.ensure_ready(typed_request)


ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF: Final[str] = "environment.ready.ensure_ready"
ENVIRONMENT__READY__ENSURE_READY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF,
        api_name="environment",
        capability_name="ready",
        endpoint_name="ensure_ready",
        request_type_ref="aware_environment_service_dto.environment.EnsureReadyRequest",
        response_type_ref="aware_environment_service_dto.environment.EnsureReadyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__ready__ensure_ready,
    )
)


async def invoke_environment__runtime_ref__resolve_runtime_refs(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveRuntimeRefsResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ResolveRuntimeRefsRequest.model_validate(request)
    return await typed_handler.environment.runtime_ref.resolve_runtime_refs(typed_request)


ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF: Final[str] = "environment.runtime_ref.resolve_runtime_refs"
ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF,
        api_name="environment",
        capability_name="runtime_ref",
        endpoint_name="resolve_runtime_refs",
        request_type_ref="aware_environment_service_dto.environment.ResolveRuntimeRefsRequest",
        response_type_ref="aware_environment_service_dto.environment.ResolveRuntimeRefsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__runtime_ref__resolve_runtime_refs,
    )
)


async def invoke_environment__service_routes__configure_service_api_dependency_routes(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ConfigureServiceApiDependencyRoutesResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ConfigureServiceApiDependencyRoutesRequest.model_validate(request)
    return await typed_handler.environment.service_routes.configure_service_api_dependency_routes(typed_request)


ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: Final[str] = (
    "environment.service_routes.configure_service_api_dependency_routes"
)
ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
    api_name="environment",
    capability_name="service_routes",
    endpoint_name="configure_service_api_dependency_routes",
    request_type_ref="aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesRequest",
    response_type_ref="aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_environment__service_routes__configure_service_api_dependency_routes,
)


async def invoke_environment__session__describe_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentSessionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentSessionRequest.model_validate(request)
    return await typed_handler.environment.session.describe_session(typed_request)


ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF: Final[str] = "environment.session.describe_session"
ENVIRONMENT__SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
        api_name="environment",
        capability_name="session",
        endpoint_name="describe_session",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentSessionRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentSessionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__session__describe_session,
    )
)


async def invoke_environment__session__join_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> JoinEnvironmentSessionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = JoinEnvironmentSessionRequest.model_validate(request)
    return await typed_handler.environment.session.join_session(typed_request)


ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF: Final[str] = "environment.session.join_session"
ENVIRONMENT__SESSION__JOIN_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF,
        api_name="environment",
        capability_name="session",
        endpoint_name="join_session",
        request_type_ref="aware_environment_service_dto.environment.JoinEnvironmentSessionRequest",
        response_type_ref="aware_environment_service_dto.environment.JoinEnvironmentSessionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__session__join_session,
    )
)


async def invoke_environment__session__mount_attention_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MountEnvironmentSessionAttentionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = MountEnvironmentSessionAttentionRequest.model_validate(request)
    return await typed_handler.environment.session.mount_attention_session(typed_request)


ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = "environment.session.mount_attention_session"
ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF,
        api_name="environment",
        capability_name="session",
        endpoint_name="mount_attention_session",
        request_type_ref="aware_environment_service_dto.environment.MountEnvironmentSessionAttentionRequest",
        response_type_ref="aware_environment_service_dto.environment.MountEnvironmentSessionAttentionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__session__mount_attention_session,
    )
)


async def invoke_environment__session__resolve_attention(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveEnvironmentSessionAttentionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = ResolveEnvironmentSessionAttentionRequest.model_validate(request)
    return await typed_handler.environment.session.resolve_attention(typed_request)


ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF: Final[str] = "environment.session.resolve_attention"
ENVIRONMENT__SESSION__RESOLVE_ATTENTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
        api_name="environment",
        capability_name="session",
        endpoint_name="resolve_attention",
        request_type_ref="aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionRequest",
        response_type_ref="aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__session__resolve_attention,
    )
)


async def invoke_environment__session__start_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> StartEnvironmentSessionResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = StartEnvironmentSessionRequest.model_validate(request)
    return await typed_handler.environment.session.start_session(typed_request)


ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF: Final[str] = "environment.session.start_session"
ENVIRONMENT__SESSION__START_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF,
        api_name="environment",
        capability_name="session",
        endpoint_name="start_session",
        request_type_ref="aware_environment_service_dto.environment.StartEnvironmentSessionRequest",
        response_type_ref="aware_environment_service_dto.environment.StartEnvironmentSessionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__session__start_session,
    )
)


async def invoke_environment__status__describe_environment_status(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentStatusResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentStatusRequest.model_validate(request)
    return await typed_handler.environment.status.describe_environment_status(typed_request)


ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF: Final[str] = (
    "environment.status.describe_environment_status"
)
ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF,
        api_name="environment",
        capability_name="status",
        endpoint_name="describe_environment_status",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentStatusRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentStatusResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__status__describe_environment_status,
    )
)


async def invoke_environment__topology__describe_environment_topology(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeEnvironmentTopologyResponse:
    typed_handler = cast(AwareEnvironmentServiceProtocol, handler)
    typed_request = DescribeEnvironmentTopologyRequest.model_validate(request)
    return await typed_handler.environment.topology.describe_environment_topology(typed_request)


ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF: Final[str] = (
    "environment.topology.describe_environment_topology"
)
ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF,
        api_name="environment",
        capability_name="topology",
        endpoint_name="describe_environment_topology",
        request_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentTopologyRequest",
        response_type_ref="aware_environment_service_dto.environment.DescribeEnvironmentTopologyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_environment__topology__describe_environment_topology,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF: ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_PROTOCOL_BINDING,
    ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF: ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_PROTOCOL_BINDING,
    ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF: ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_PROTOCOL_BINDING,
    ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF: ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_PROTOCOL_BINDING,
    ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF: ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_PROTOCOL_BINDING,
    ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF: ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_PROTOCOL_BINDING,
    ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF: ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_PROTOCOL_BINDING,
    ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF: ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_PROTOCOL_BINDING,
    ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF: ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_PROTOCOL_BINDING,
    ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF: ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_PROTOCOL_BINDING,
    ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF: ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_PROTOCOL_BINDING,
    ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING,
    ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF: ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_PROTOCOL_BINDING,
    ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF: ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_PROTOCOL_BINDING,
    ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF: ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_PROTOCOL_BINDING,
    ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF: ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_PROTOCOL_BINDING,
    ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF: ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_PROTOCOL_BINDING,
    ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF: ENVIRONMENT__READY__ENSURE_READY_PROTOCOL_BINDING,
    ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF: ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_PROTOCOL_BINDING,
    ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING,
    ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF: ENVIRONMENT__SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING,
    ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF: ENVIRONMENT__SESSION__JOIN_SESSION_PROTOCOL_BINDING,
    ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF: ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_PROTOCOL_BINDING,
    ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF: ENVIRONMENT__SESSION__RESOLVE_ATTENTION_PROTOCOL_BINDING,
    ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF: ENVIRONMENT__SESSION__START_SESSION_PROTOCOL_BINDING,
    ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF: ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_PROTOCOL_BINDING,
    ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF: ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_PROTOCOL_BINDING,
}


class EnvironmentActorAdmissionCapabilityServiceProtocol(Protocol):

    async def admit_actor(self, request: AdmitEnvironmentActorRequest) -> AdmitEnvironmentActorResponse: ...


class EnvironmentCapabilitiesCapabilityServiceProtocol(Protocol):

    async def fetch_capabilities(self, request: FetchCapabilitiesRequest) -> FetchCapabilitiesResponse: ...


class EnvironmentCommittedProjectionDtoCapabilityServiceProtocol(Protocol):

    async def materialize_committed_projection_dto(
        self, request: MaterializeCommittedProjectionDtoRequest
    ) -> MaterializeCommittedProjectionDtoResponse: ...


class EnvironmentDescribeCapabilityServiceProtocol(Protocol):

    async def describe_environment(self, request: DescribeEnvironmentRequest) -> DescribeEnvironmentResponse: ...


class EnvironmentDescribeConfigCapabilityServiceProtocol(Protocol):

    async def describe_environment_config(
        self, request: DescribeEnvironmentConfigRequest
    ) -> DescribeEnvironmentConfigResponse: ...


class EnvironmentFunctionCallCapabilityServiceProtocol(Protocol):

    async def invoke_function(self, request: InvokeFunctionRequest) -> InvokeFunctionResponse: ...


class EnvironmentLaneHeadCapabilityServiceProtocol(Protocol):

    async def get_lane_head(self, request: GetLaneHeadRequest) -> GetLaneHeadResponse: ...


class EnvironmentNavigationCapabilityServiceProtocol(Protocol):

    async def create_navigation_context(
        self, request: CreateEnvironmentNavigationContextRequest
    ) -> CreateEnvironmentNavigationContextResponse: ...

    async def describe_navigation_context(
        self, request: DescribeEnvironmentNavigationContextRequest
    ) -> DescribeEnvironmentNavigationContextResponse: ...

    async def list_navigation_contexts(
        self, request: ListEnvironmentNavigationContextsRequest
    ) -> ListEnvironmentNavigationContextsResponse: ...

    async def select_navigation_target(
        self, request: SelectEnvironmentNavigationTargetRequest
    ) -> SelectEnvironmentNavigationTargetResponse: ...


class EnvironmentObjectInstanceGraphCommitCapabilityServiceProtocol(Protocol):

    async def get_object_instance_graph_commit(
        self, request: GetObjectInstanceGraphCommitRequest
    ) -> GetObjectInstanceGraphCommitResponse: ...


class EnvironmentOntologyCapabilityServiceProtocol(Protocol):

    async def attach_environment_ontology(
        self, request: AttachEnvironmentOntologyRequest
    ) -> AttachEnvironmentOntologyResponse: ...

    async def ensure_environment_ontology_runtime(
        self, request: EnsureEnvironmentOntologyRuntimeRequest
    ) -> EnsureEnvironmentOntologyRuntimeResponse: ...

    async def list_environment_ontologies(
        self, request: ListEnvironmentOntologiesRequest
    ) -> ListEnvironmentOntologiesResponse: ...


class EnvironmentProfileCapabilityServiceProtocol(Protocol):

    async def provision_environment_profile(
        self, request: ProvisionEnvironmentProfileRequest
    ) -> ProvisionEnvironmentProfileResponse: ...

    async def upsert_environment_profile(
        self, request: UpsertEnvironmentProfileRequest
    ) -> UpsertEnvironmentProfileResponse: ...


class EnvironmentReadyCapabilityServiceProtocol(Protocol):

    async def ensure_ready(self, request: EnsureReadyRequest) -> EnsureReadyResponse: ...


class EnvironmentRuntimeRefCapabilityServiceProtocol(Protocol):

    async def resolve_runtime_refs(self, request: ResolveRuntimeRefsRequest) -> ResolveRuntimeRefsResponse: ...


class EnvironmentServiceRoutesCapabilityServiceProtocol(Protocol):

    async def configure_service_api_dependency_routes(
        self, request: ConfigureServiceApiDependencyRoutesRequest
    ) -> ConfigureServiceApiDependencyRoutesResponse: ...


class EnvironmentSessionCapabilityServiceProtocol(Protocol):

    async def describe_session(
        self, request: DescribeEnvironmentSessionRequest
    ) -> DescribeEnvironmentSessionResponse: ...

    async def join_session(self, request: JoinEnvironmentSessionRequest) -> JoinEnvironmentSessionResponse: ...

    async def mount_attention_session(
        self, request: MountEnvironmentSessionAttentionRequest
    ) -> MountEnvironmentSessionAttentionResponse: ...

    async def resolve_attention(
        self, request: ResolveEnvironmentSessionAttentionRequest
    ) -> ResolveEnvironmentSessionAttentionResponse: ...

    async def start_session(self, request: StartEnvironmentSessionRequest) -> StartEnvironmentSessionResponse: ...


class EnvironmentStatusCapabilityServiceProtocol(Protocol):

    async def describe_environment_status(
        self, request: DescribeEnvironmentStatusRequest
    ) -> DescribeEnvironmentStatusResponse: ...


class EnvironmentTopologyCapabilityServiceProtocol(Protocol):

    async def describe_environment_topology(
        self, request: DescribeEnvironmentTopologyRequest
    ) -> DescribeEnvironmentTopologyResponse: ...


class EnvironmentApiServiceProtocol(Protocol):
    actor_admission: EnvironmentActorAdmissionCapabilityServiceProtocol
    capabilities: EnvironmentCapabilitiesCapabilityServiceProtocol
    committed_projection_dto: EnvironmentCommittedProjectionDtoCapabilityServiceProtocol
    describe: EnvironmentDescribeCapabilityServiceProtocol
    describe_config: EnvironmentDescribeConfigCapabilityServiceProtocol
    function_call: EnvironmentFunctionCallCapabilityServiceProtocol
    lane_head: EnvironmentLaneHeadCapabilityServiceProtocol
    navigation: EnvironmentNavigationCapabilityServiceProtocol
    object_instance_graph_commit: EnvironmentObjectInstanceGraphCommitCapabilityServiceProtocol
    ontology: EnvironmentOntologyCapabilityServiceProtocol
    profile: EnvironmentProfileCapabilityServiceProtocol
    ready: EnvironmentReadyCapabilityServiceProtocol
    runtime_ref: EnvironmentRuntimeRefCapabilityServiceProtocol
    service_routes: EnvironmentServiceRoutesCapabilityServiceProtocol
    session: EnvironmentSessionCapabilityServiceProtocol
    status: EnvironmentStatusCapabilityServiceProtocol
    topology: EnvironmentTopologyCapabilityServiceProtocol


class AwareEnvironmentServiceProtocol(Protocol):
    environment: EnvironmentApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:e6c10b20924d73d80c0060a57e4cb5fcf51a7d4a1e8ab8a5bdec88f45b13dae0",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 104,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:635830b60025237476a4777eb49faf7eb7590a5cdd535aa75e61f1d0b5ee462b",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.actor_admission.admit_actor",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.capabilities.fetch_capabilities",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.committed_projection_dto.materialize_committed_projection_dto",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.describe.describe_environment",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.describe_config.describe_environment_config",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.function_call.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.lane_head.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.navigation.create_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.navigation.describe_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.navigation.list_navigation_contexts",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.navigation.select_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.object_instance_graph_commit.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.ontology.attach_environment_ontology",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.ontology.ensure_environment_ontology_runtime",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.ontology.list_environment_ontologies",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.profile.provision_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.profile.upsert_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.ready.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.runtime_ref.resolve_runtime_refs",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.service_routes.configure_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.session.join_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.session.mount_attention_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.session.resolve_attention",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.session.start_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.status.describe_environment_status",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:environment.topology.describe_environment_topology",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a128cf2ea49b376c0b00ede07d9c05d323af0ca3a71673fa7568fae8ab3277a4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.actor_admission.admit_actor",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7eb7e624be1f4b1afb96263ace14c9890d0c7c59971de00f6a6deb51510c0a99",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.actor_admission.admit_actor",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ccce40db0dee8b4aa8a8fca3c656d45f3d21104ef35058f431c164b7d27a7fca",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.capabilities.fetch_capabilities",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e70798bd569d0d2ce9219f1223aa4f2df081a1923699ca242676a82abbb5be02",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.capabilities.fetch_capabilities",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:26bbbd06a8054e1b0adf93241ff19b74f0f6d6bbaa6813bba51f886e24a70dc5",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.committed_projection_dto.materialize_committed_projection_dto",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:537606ecf112a8a2c6c0e855f9c9e45273832d96e11952d49f5cca076f9e5aff",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.committed_projection_dto.materialize_committed_projection_dto",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:97b4c13bad93e6b5d48f2cb942f6289b48fd3c212a9d92050e9eea60e635504c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.describe.describe_environment",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:78038a27b18955c3500c2b1fd045ea7035349dc895e985d97f8bb354ece2fb0e",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.describe.describe_environment",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:131b1759624006e7d0501b687de86fa0bdb2e2adc4d807acfd0fb29bd7b314cf",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.describe_config.describe_environment_config",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b9673e7dbe87bcb3b5f2d0b85ad94b5c9468ae310950563471cc832bc21f8b63",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.describe_config.describe_environment_config",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:7528e02be2cf648b80772c8dda3931320d6ae4d376366481e6352454f92b0fc8",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.function_call.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:62d9c3bd1529c192a76a48c28779452c27ff9ff44eb34da1351660249e0d2940",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.function_call.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:45144023b0141c44198b4da9e1074705c3262545466a1bc20f34b0bf7ffc808e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.lane_head.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:913c9c68d72d163871e6319bd4285736247c3b39aeae12452fee5ab9ef3ff672",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.lane_head.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1aa7be1efdba7f85705fbf45221d6cc059614205397bb91af2109d06b5f03eab",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.navigation.create_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:75c3b8df85ce420737a4912b36e43fac1bbd7bdeda473f2555232855f07d1a45",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.navigation.create_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:53347c80b20ad39f788d04f24eafe5f038ce7c7f5036035001d7b2490b1bf7eb",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.navigation.describe_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7aee0ea3d6050a8a3060cd330c8a1f6cff932a3ffe164931d632eff66dbcc7ad",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.navigation.describe_navigation_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c264f5b8128af2c7fd3ee00b303dd338c8ecf3f7c8d6440d0cc887d578a3de9a",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.navigation.list_navigation_contexts",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:ef5187fca3d9164970484561b9dca52b09027b533185ab06dde006dd18a62e7d",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.navigation.list_navigation_contexts",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:3e3050159413b010b2144a8effd55766221a30f0810d126d11466d36e7ffce19",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.navigation.select_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d53810ce00702a4de2b09f678cf1cf4f02db85dca6e2d5d6ab194c65ea08d0ad",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.navigation.select_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1a6c0c26d008ae36cd15ab5e03272f270ee7908c262d70c48ea6573277249644",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.object_instance_graph_commit.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6dbda5fbbfdea192d34e84f0959de89f7b00a5cac3a2273978cd19c0aea0ac8d",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.object_instance_graph_commit.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ae90f15ba8409524e289b04ad26d3c4df90540b59ff1e018b4783a294fa140f5",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.ontology.attach_environment_ontology",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:709770b173a0051e48aff745934145ef7f0070f05656a24513d634f61cee28d9",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.ontology.attach_environment_ontology",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2acc912ffb6b80ed713cad816ba9ed3538b4978e3957d4a1a70ea79a611211da",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.ontology.ensure_environment_ontology_runtime",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d7c3576b4be7d09f248682f088892810d5a7a61ba2d161220b414cb4fb3a699a",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.ontology.ensure_environment_ontology_runtime",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:83abc87960d63c18b7fbb58633a5ff739b102c22925e2bbfbeab4df25053fc12",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.ontology.list_environment_ontologies",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:86ced6e7eedbf8094e22b3689e151f673eb6ae91c4ce65852cff184744e03875",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.ontology.list_environment_ontologies",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2779019741b28ab7c97b4c37c7ea384c042f404029de179dfe25e2cedaf9406e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.profile.provision_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7acc050a737ce297b24b66283c6b26436e770de36f906dc79060247a9fe31e41",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.profile.provision_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c9d3605f623e5ef2af907dbe23a184c8711cce83a6fcf24e20c890f7a9a22902",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.profile.upsert_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0fd0f41f6a323f97562c19691f553980f0319b51a92260b1a7e672dc324d2d9f",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.profile.upsert_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d75a169a27b6539471c1e9a6f233bba7fa0d864bf7f406984835c2ccfa4616cd",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.ready.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:4edf4c40ac341ba5afffff719163b052ec471c9c12b94c3700158938b0d214e7",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.ready.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9b6b476d7c8c8e0b67756d325b353a411fbe5b8a922a481cfe3fd6e103408ac3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.runtime_ref.resolve_runtime_refs",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:471d97c2f9693bfd1cb258937beb7b48eef594fa00d04ca271de56d6e72b9972",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.runtime_ref.resolve_runtime_refs",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2067226ee879334bfac75d2b82f0de65a76fc365a62e368c18067c789a6b2ba0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.service_routes.configure_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a05b82ceb9ff05ad3ef5b996901c2015e254725044d5ef46bacd99002fc118a6",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.service_routes.configure_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:7fd1e185b82cb8be7f68031181fb6465fac28cccd9bfc1d16cc8219a1cb01392",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 69'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:dd467913f97dce264c6ded83699a29e672ef2cac1e94ced3ffb32d5a93d5dd0e",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.session.describe_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 70'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5d4fc0008cdfe7ee965244bb5c91a67340a6f77d7381bbb1e19614bd551a6e6e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.session.join_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 71'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:04f66f23c88a3fbf8b32d475b8422a8fefbb09f470b70beb3f5ad262ee58da61",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.session.join_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 72'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5bf4bd7bfe00ede46bea655ff9110ba65130281fe5c53ba31efc77f8b9e081e2",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.session.mount_attention_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 73'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7e5253bfa5eba2785ad26facb141b62036faf134d34a3c6dc2ebf8c6253aa5c5",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.session.mount_attention_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 74'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:007ef074b8a9bd8ec772a81e3bccc49b53d8e8a2e3db82fa4a2402d64ab17e3b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.session.resolve_attention",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 75'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5b96e289888f808dffdf54a34c77ac441a0c0fdd5002b6e1771b34c4259778f6",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.session.resolve_attention",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 76'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0b866e183602b8a1b730df516a13c540b7870f69bc03ff10737c037129ce3f25",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.session.start_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 77'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6b59877a8a5694962075823e004108104483e4b1afb8e3a9587101bb7dcc8d06",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.session.start_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 78'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:8afd0a468d3b0fd2f819a1eb4ebc34d43d350b141549540085b295b7e56a088f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.status.describe_environment_status",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 79'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:fdcf24980a011d90353337ddf84f1231d03fe558d6c82e42e689cd5eb8558a8e",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.status.describe_environment_status",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 80'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1f14107e9e9e5318303fb2c2c8de540b365f1cf98049e16b27469bd1ec3d0d8c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:environment.topology.describe_environment_topology",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 81'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:99fd66ec09255a869a29a4ae23f3947a9bf36bd5f229207bb591cb73e701ca64",'
    '      "section_key": "api.service_protocol.endpoint_binding:environment.topology.describe_environment_topology",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 82'
    "    },"
    "    {"
    '      "line_count": 30,'
    '      "rendered_text_digest": "sha256:250a0058f95f7c8f67970724686fb264f1c17c0965a874e25140d4db9648ec3b",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 83'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ca301a06c04253cdbf4d72f8908023596fcd2c2ebe112ac071267da4eadcf7bf",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.actor_admission",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 84'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ecc41093592afa4c2cb8eada468a7fe45f7981bd887b28450157649667b5d98c",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.capabilities",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 85'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:827f3b2d7a2993bf6d2a4250dfcdc1610fc9cff7cf1cef3b876a29bab81f2b11",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.committed_projection_dto",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 86'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6613d7bc9a2e929b48fa93572d37cc152ab3cd0bc227177053781d3123cbab91",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.describe",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 87'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:54154a7155fcb921a06f40f62ed1535b22de532b86a935e3da47c20b1da467a0",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.describe_config",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 88'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d7b7c02a7a89222b5e1bd8f2e7f06abdc992b229e18cf9838da40bcdfd5ebe0e",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.function_call",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 89'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2f91f12c1113cb39efd75489a51d8c818be77563660423a0682e615f8561ecf4",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.lane_head",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 90'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:84f979e732bb05172e78450c6fd4472044e71d188c714ed4ecee563cb74c21eb",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.navigation",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 91'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:25d885ceb18871cca81dbad32d1b6f633cc8513386d6564c1652e96eaea1c937",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.object_instance_graph_commit",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 92'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:331b2a1cbbee4c7d4a6e750d3f7c0e37366779ee9fd4459078c3269d7d12320c",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.ontology",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 93'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:b00fa3dabce777aa9b625a024e46fafdb30eba7266c32df670f1c5d2bd93fa4b",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 94'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1c03070085a6f3d4a6488d0892e6a059ec402332002e766cdc73e40518aa0669",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.ready",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 95'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:cfd0b4dc08b4e280fbaf09a72f5c66141d21c340a103978706d41fc7cf780f4a",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.runtime_ref",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 96'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:8d73f52458f9b3a6dffa72fce8653337049ede278381ca1557d26e7c68e7f9dd",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.service_routes",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 97'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:6cf24cc17cea7485727cb6514f2177e106ca3733381d5ae20e7924202952726f",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 98'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ede5227dd222ab7fb1b0d26867c950579bf26f595a82f3638e7f86af83597694",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.status",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 99'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1b2222239e58bcecbbcf860f5cf85954b54c29fe21bc50b91dde9baffddf04e6",'
    '      "section_key": "api.service_protocol.capability_protocol:environment.topology",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 100'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:f1ecec104aff205c0e8b000e263ce9a22292bcd648c58a8667f100c18a89d2ed",'
    '      "section_key": "api.service_protocol.api_protocol:environment",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 101'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:7da3915f78278fff2ff1941b8a701ea22835589cf33c9821f6ece49f053ac0ad",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 102'
    "    },"
    "    {"
    '      "line_count": 114,'
    '      "rendered_text_digest": "sha256:8e2df7043e9378cb4927e7109465cb68ccd196ee6bff6d9406bceeea1e9e4aa4",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 103'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareEnvironmentServiceProtocol",
    "EnvironmentApiServiceProtocol",
    "EnvironmentActorAdmissionCapabilityServiceProtocol",
    "EnvironmentCapabilitiesCapabilityServiceProtocol",
    "EnvironmentCommittedProjectionDtoCapabilityServiceProtocol",
    "EnvironmentDescribeCapabilityServiceProtocol",
    "EnvironmentDescribeConfigCapabilityServiceProtocol",
    "EnvironmentFunctionCallCapabilityServiceProtocol",
    "EnvironmentLaneHeadCapabilityServiceProtocol",
    "EnvironmentNavigationCapabilityServiceProtocol",
    "EnvironmentObjectInstanceGraphCommitCapabilityServiceProtocol",
    "EnvironmentOntologyCapabilityServiceProtocol",
    "EnvironmentProfileCapabilityServiceProtocol",
    "EnvironmentReadyCapabilityServiceProtocol",
    "EnvironmentRuntimeRefCapabilityServiceProtocol",
    "EnvironmentServiceRoutesCapabilityServiceProtocol",
    "EnvironmentSessionCapabilityServiceProtocol",
    "EnvironmentStatusCapabilityServiceProtocol",
    "EnvironmentTopologyCapabilityServiceProtocol",
    "ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF",
    "ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_PROTOCOL_BINDING",
    "invoke_environment__actor_admission__admit_actor",
    "ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF",
    "ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_PROTOCOL_BINDING",
    "invoke_environment__capabilities__fetch_capabilities",
    "ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF",
    "ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_PROTOCOL_BINDING",
    "invoke_environment__committed_projection_dto__materialize_committed_projection_dto",
    "ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF",
    "ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_PROTOCOL_BINDING",
    "invoke_environment__describe__describe_environment",
    "ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF",
    "ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_PROTOCOL_BINDING",
    "invoke_environment__describe_config__describe_environment_config",
    "ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF",
    "ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_PROTOCOL_BINDING",
    "invoke_environment__function_call__invoke_function",
    "ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF",
    "ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_PROTOCOL_BINDING",
    "invoke_environment__lane_head__get_lane_head",
    "ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_PROTOCOL_BINDING",
    "invoke_environment__navigation__create_navigation_context",
    "ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_PROTOCOL_BINDING",
    "invoke_environment__navigation__describe_navigation_context",
    "ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_PROTOCOL_BINDING",
    "invoke_environment__navigation__list_navigation_contexts",
    "ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_PROTOCOL_BINDING",
    "invoke_environment__navigation__select_navigation_target",
    "ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING",
    "invoke_environment__object_instance_graph_commit__get_object_instance_graph_commit",
    "ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_PROTOCOL_BINDING",
    "invoke_environment__ontology__attach_environment_ontology",
    "ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_PROTOCOL_BINDING",
    "invoke_environment__ontology__ensure_environment_ontology_runtime",
    "ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_PROTOCOL_BINDING",
    "invoke_environment__ontology__list_environment_ontologies",
    "ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_PROTOCOL_BINDING",
    "invoke_environment__profile__provision_environment_profile",
    "ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_PROTOCOL_BINDING",
    "invoke_environment__profile__upsert_environment_profile",
    "ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF",
    "ENVIRONMENT__READY__ENSURE_READY_PROTOCOL_BINDING",
    "invoke_environment__ready__ensure_ready",
    "ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF",
    "ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_PROTOCOL_BINDING",
    "invoke_environment__runtime_ref__resolve_runtime_refs",
    "ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF",
    "ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING",
    "invoke_environment__service_routes__configure_service_api_dependency_routes",
    "ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__DESCRIBE_SESSION_PROTOCOL_BINDING",
    "invoke_environment__session__describe_session",
    "ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__JOIN_SESSION_PROTOCOL_BINDING",
    "invoke_environment__session__join_session",
    "ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_PROTOCOL_BINDING",
    "invoke_environment__session__mount_attention_session",
    "ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__RESOLVE_ATTENTION_PROTOCOL_BINDING",
    "invoke_environment__session__resolve_attention",
    "ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__START_SESSION_PROTOCOL_BINDING",
    "invoke_environment__session__start_session",
    "ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF",
    "ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_PROTOCOL_BINDING",
    "invoke_environment__status__describe_environment_status",
    "ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF",
    "ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_PROTOCOL_BINDING",
    "invoke_environment__topology__describe_environment_topology",
]
