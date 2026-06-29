# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_meta_service_dto.diagnostics.completeness import (
    MetaCompletenessAnalyzeRequest,
    MetaCompletenessAnalyzeResponse,
)
from aware_meta_service_dto.graph.config.package_compile import (
    MetaObjectConfigGraphPackageEnsureRequest,
    MetaObjectConfigGraphPackageEnsureResponse,
)
from aware_meta_service_dto.graph.instance.commit_event import (
    MetaCommitEventEnvelope,
    MetaCommitSubscriptionRequest,
    MetaCommitSubscriptionResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphGetLaneHeadRequest,
    MetaGraphGetLaneHeadResponse,
    MetaGraphGetObjectInstanceGraphCommitRequest,
    MetaGraphGetObjectInstanceGraphCommitResponse,
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
    MetaGraphInvokeTemporalFunctionRequest,
    MetaGraphInvokeTemporalFunctionResponse,
    MetaGraphResolveProjectionRequest,
    MetaGraphResolveProjectionResponse,
)
from aware_meta_service_dto.graph.view.graph_view import (
    MetaGraphResolveGraphViewRequest,
    MetaGraphResolveGraphViewResponse,
)
from aware_meta_service_dto.persistence.database_readiness import (
    MetaPersistenceEnsureDatabaseReadyRequest,
    MetaPersistenceEnsureDatabaseReadyResponse,
)
from aware_meta_service_dto.runtime.read_model import MetaRuntimeReadModelRequest, MetaRuntimeReadModelResponse

API_PACKAGE_NAME: Final[str] = "meta-service-api"
API_FQN_PREFIX: Final[str] = "aware_meta_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_meta_service_api"


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


MetaCommitSubscribeStreamEvent: TypeAlias = MetaCommitEventEnvelope


async def invoke_meta__commit__subscribe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaCommitSubscriptionResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaCommitSubscriptionRequest.model_validate(request)
    return await typed_handler.meta.commit.subscribe(typed_request)


def stream_invoke_meta__commit__subscribe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[MetaCommitSubscribeStreamEvent]:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaCommitSubscriptionRequest.model_validate(request)
    _ = execution
    return typed_handler.meta.commit.stream_subscribe(typed_request)


META__COMMIT__SUBSCRIBE_ENDPOINT_REF: Final[str] = "meta.commit.subscribe"
META__COMMIT__SUBSCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=META__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    api_name="meta",
    capability_name="commit",
    endpoint_name="subscribe",
    request_type_ref="aware_meta_service_dto.graph.instance.MetaCommitSubscriptionRequest",
    response_type_ref="aware_meta_service_dto.graph.instance.MetaCommitSubscriptionResponse",
    stream_event_type_refs=("aware_meta_service_dto.graph.instance.MetaCommitEventEnvelope",),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_meta__commit__subscribe,
    fulfillment_bindings=(),
    invoke=invoke_meta__commit__subscribe,
)


async def invoke_meta__diagnostics__analyze_object_config_graph_completeness(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaCompletenessAnalyzeResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaCompletenessAnalyzeRequest.model_validate(request)
    return await typed_handler.meta.diagnostics.analyze_object_config_graph_completeness(typed_request)


META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF: Final[str] = (
    "meta.diagnostics.analyze_object_config_graph_completeness"
)
META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF,
        api_name="meta",
        capability_name="diagnostics",
        endpoint_name="analyze_object_config_graph_completeness",
        request_type_ref="aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeRequest",
        response_type_ref="aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__diagnostics__analyze_object_config_graph_completeness,
    )
)


async def invoke_meta__graph__get_lane_head(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphGetLaneHeadResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphGetLaneHeadRequest.model_validate(request)
    return await typed_handler.meta.graph.get_lane_head(typed_request)


META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "meta.graph.get_lane_head"
META__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    api_name="meta",
    capability_name="graph",
    endpoint_name="get_lane_head",
    request_type_ref="aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadRequest",
    response_type_ref="aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_meta__graph__get_lane_head,
)


async def invoke_meta__graph__get_object_instance_graph_commit(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphGetObjectInstanceGraphCommitResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphGetObjectInstanceGraphCommitRequest.model_validate(request)
    return await typed_handler.meta.graph.get_object_instance_graph_commit(typed_request)


META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = "meta.graph.get_object_instance_graph_commit"
META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
        api_name="meta",
        capability_name="graph",
        endpoint_name="get_object_instance_graph_commit",
        request_type_ref="aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitRequest",
        response_type_ref="aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__graph__get_object_instance_graph_commit,
    )
)


async def invoke_meta__graph__invoke_function(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphInvokeFunctionResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphInvokeFunctionRequest.model_validate(request)
    return await typed_handler.meta.graph.invoke_function(typed_request)


META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "meta.graph.invoke_function"
META__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
    api_name="meta",
    capability_name="graph",
    endpoint_name="invoke_function",
    request_type_ref="aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionRequest",
    response_type_ref="aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_meta__graph__invoke_function,
)


async def invoke_meta__graph__invoke_temporal_function(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphInvokeTemporalFunctionResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphInvokeTemporalFunctionRequest.model_validate(request)
    return await typed_handler.meta.graph.invoke_temporal_function(typed_request)


META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF: Final[str] = "meta.graph.invoke_temporal_function"
META__GRAPH__INVOKE_TEMPORAL_FUNCTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF,
        api_name="meta",
        capability_name="graph",
        endpoint_name="invoke_temporal_function",
        request_type_ref="aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionRequest",
        response_type_ref="aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__graph__invoke_temporal_function,
    )
)


async def invoke_meta__graph__resolve_graph_view(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphResolveGraphViewResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphResolveGraphViewRequest.model_validate(request)
    return await typed_handler.meta.graph.resolve_graph_view(typed_request)


META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF: Final[str] = "meta.graph.resolve_graph_view"
META__GRAPH__RESOLVE_GRAPH_VIEW_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF,
        api_name="meta",
        capability_name="graph",
        endpoint_name="resolve_graph_view",
        request_type_ref="aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewRequest",
        response_type_ref="aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__graph__resolve_graph_view,
    )
)


async def invoke_meta__graph__resolve_projection(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaGraphResolveProjectionResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaGraphResolveProjectionRequest.model_validate(request)
    return await typed_handler.meta.graph.resolve_projection(typed_request)


META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: Final[str] = "meta.graph.resolve_projection"
META__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
        api_name="meta",
        capability_name="graph",
        endpoint_name="resolve_projection",
        request_type_ref="aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionRequest",
        response_type_ref="aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__graph__resolve_projection,
    )
)


async def invoke_meta__package__ensure_object_config_graph_package(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaObjectConfigGraphPackageEnsureResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaObjectConfigGraphPackageEnsureRequest.model_validate(request)
    return await typed_handler.meta.package.ensure_object_config_graph_package(typed_request)


META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: Final[str] = (
    "meta.package.ensure_object_config_graph_package"
)
META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
        api_name="meta",
        capability_name="package",
        endpoint_name="ensure_object_config_graph_package",
        request_type_ref="aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureRequest",
        response_type_ref="aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__package__ensure_object_config_graph_package,
    )
)


async def invoke_meta__persistence__ensure_database_ready(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaPersistenceEnsureDatabaseReadyResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaPersistenceEnsureDatabaseReadyRequest.model_validate(request)
    return await typed_handler.meta.persistence.ensure_database_ready(typed_request)


META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF: Final[str] = "meta.persistence.ensure_database_ready"
META__PERSISTENCE__ENSURE_DATABASE_READY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF,
        api_name="meta",
        capability_name="persistence",
        endpoint_name="ensure_database_ready",
        request_type_ref="aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyRequest",
        response_type_ref="aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__persistence__ensure_database_ready,
    )
)


async def invoke_meta__runtime_read_model__describe_workspace(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MetaRuntimeReadModelResponse:
    typed_handler = cast(AwareMetaServiceProtocol, handler)
    typed_request = MetaRuntimeReadModelRequest.model_validate(request)
    return await typed_handler.meta.runtime_read_model.describe_workspace(typed_request)


META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF: Final[str] = "meta.runtime_read_model.describe_workspace"
META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF,
        api_name="meta",
        capability_name="runtime_read_model",
        endpoint_name="describe_workspace",
        request_type_ref="aware_meta_service_dto.runtime.MetaRuntimeReadModelRequest",
        response_type_ref="aware_meta_service_dto.runtime.MetaRuntimeReadModelResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_meta__runtime_read_model__describe_workspace,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    META__COMMIT__SUBSCRIBE_ENDPOINT_REF: META__COMMIT__SUBSCRIBE_PROTOCOL_BINDING,
    META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF: META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_PROTOCOL_BINDING,
    META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: META__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING,
    META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING,
    META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: META__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING,
    META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF: META__GRAPH__INVOKE_TEMPORAL_FUNCTION_PROTOCOL_BINDING,
    META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF: META__GRAPH__RESOLVE_GRAPH_VIEW_PROTOCOL_BINDING,
    META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: META__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING,
    META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING,
    META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF: META__PERSISTENCE__ENSURE_DATABASE_READY_PROTOCOL_BINDING,
    META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF: META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_PROTOCOL_BINDING,
}


class MetaCommitCapabilityServiceProtocol(Protocol):

    async def subscribe(self, request: MetaCommitSubscriptionRequest) -> MetaCommitSubscriptionResponse: ...

    def stream_subscribe(
        self, request: MetaCommitSubscriptionRequest
    ) -> AsyncIterator[MetaCommitSubscribeStreamEvent]: ...


class MetaDiagnosticsCapabilityServiceProtocol(Protocol):

    async def analyze_object_config_graph_completeness(
        self, request: MetaCompletenessAnalyzeRequest
    ) -> MetaCompletenessAnalyzeResponse: ...


class MetaGraphCapabilityServiceProtocol(Protocol):

    async def get_lane_head(self, request: MetaGraphGetLaneHeadRequest) -> MetaGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self, request: MetaGraphGetObjectInstanceGraphCommitRequest
    ) -> MetaGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(self, request: MetaGraphInvokeFunctionRequest) -> MetaGraphInvokeFunctionResponse: ...

    async def invoke_temporal_function(
        self, request: MetaGraphInvokeTemporalFunctionRequest
    ) -> MetaGraphInvokeTemporalFunctionResponse: ...

    async def resolve_graph_view(
        self, request: MetaGraphResolveGraphViewRequest
    ) -> MetaGraphResolveGraphViewResponse: ...

    async def resolve_projection(
        self, request: MetaGraphResolveProjectionRequest
    ) -> MetaGraphResolveProjectionResponse: ...


class MetaPackageCapabilityServiceProtocol(Protocol):

    async def ensure_object_config_graph_package(
        self, request: MetaObjectConfigGraphPackageEnsureRequest
    ) -> MetaObjectConfigGraphPackageEnsureResponse: ...


class MetaPersistenceCapabilityServiceProtocol(Protocol):

    async def ensure_database_ready(
        self, request: MetaPersistenceEnsureDatabaseReadyRequest
    ) -> MetaPersistenceEnsureDatabaseReadyResponse: ...


class MetaRuntimeReadModelCapabilityServiceProtocol(Protocol):

    async def describe_workspace(self, request: MetaRuntimeReadModelRequest) -> MetaRuntimeReadModelResponse: ...


class MetaApiServiceProtocol(Protocol):
    commit: MetaCommitCapabilityServiceProtocol
    diagnostics: MetaDiagnosticsCapabilityServiceProtocol
    graph: MetaGraphCapabilityServiceProtocol
    package: MetaPackageCapabilityServiceProtocol
    persistence: MetaPersistenceCapabilityServiceProtocol
    runtime_read_model: MetaRuntimeReadModelCapabilityServiceProtocol


class AwareMetaServiceProtocol(Protocol):
    meta: MetaApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:ab258af8be4bfbd2d765fa3bc7afe4eb2415a2e18688b45efa85b4f4f70cd773",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 45,'
    '  "sections": ['
    "    {"
    '      "line_count": 22,'
    '      "rendered_text_digest": "sha256:f96a5cbfca921bfdbb31c854e1afa6ebf20c593ac58e413d66f0893980501a64",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:meta.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.diagnostics.analyze_object_config_graph_completeness",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.invoke_temporal_function",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.resolve_graph_view",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.persistence.ensure_database_ready",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:meta.runtime_read_model.describe_workspace",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:f710ca9e501b55f78571d37767a1351cd2fe8f8e556db02cda8152665acbb843",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:8d52284a34ab8800eab0d9a915cd25e790ae778262b2ee26cf8161de6bbf8787",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b52f0ef6e41d0d12e1d9258e614d5ba42517842a5cf729e34a897ec7ef20a1f3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.diagnostics.analyze_object_config_graph_completeness",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:87832cf49081c11e5db71403a320678d103116733a6234082426f3a31ee9c4c7",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.diagnostics.analyze_object_config_graph_completeness",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d5c44214cee2b881d0d3377c18d879f11fa479ed7179af1769885bd7240ea54e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:ffee7a637cac63c20ad7e4cb8f5c784e6f9bc60416e8c6cd6082a548203d733a",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:90f737e8542131fdac1ac97afcff02ab703362187003006a88f98fa97a3c81a9",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:fbdf779ec9d768a3fa5e8aac4aef10cc2a0e88554327ce6f2a822f66be48369c",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:10d0978100bbcdeb94998b4c4bbd04d715a4ef361a98bcc47611a4cd5b603abd",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:818996a6aca9323e6289ea3eefc63a809afef1dd576644d4df40ab149bd82f14",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c6cd4b056c0f9541ffa4ad5eeecbc1a3482cbcb49b4ead679b2d4497902fa6c7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.invoke_temporal_function",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:af35bd252276a56622344bcfef693d8fa6fe801743e39ab982a55a1c63a2b281",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.invoke_temporal_function",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4918b921d06d0df75a517e60b44916efbd09db8bbbadd5d7b2ea6ead92b3bb9f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.resolve_graph_view",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7ab244ad1796c95f8adffcf503e3c29ebbec13481ea34e6b777cedbb1cb57ff6",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.resolve_graph_view",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:828d855135a7a6a306550ff439994ca7d94c39a0ca63dc97209cf6b47235a8c5",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:da11080f713c9076c0ba5e488196c3d06811ca9bb6e9e5a2b244c0d515c1a34c",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a2f1957d1b67894ef551b2392ab4d7185e41f6a5f69714c20965d9d08322dcf2",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b773aad1ddaf31bec4ac92f7a1b1304238ecd8028388c83416e030383a54fda1",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2cfab89b4c56966955e90480e0b591d90eadd57e2ee6f2a9455c97b71f00c574",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.persistence.ensure_database_ready",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:023c099b40aca0a2890cd90714d638273e96c31fa05590b1de3a13423efaec51",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.persistence.ensure_database_ready",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:86d2db346e838e44dbce3c3637c48aa70b9ead32fb4a038b4e9b874d0e67a8a3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:meta.runtime_read_model.describe_workspace",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:003315e8b3c5660679c16a66325c29889decfff8a44f361f734cf47e4527a457",'
    '      "section_key": "api.service_protocol.endpoint_binding:meta.runtime_read_model.describe_workspace",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 14,'
    '      "rendered_text_digest": "sha256:1c478a83bea633655a42f57802b3bd72e2657f619d868af672f989f34ef24f65",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:89118b15c3bb38b846f91bb8f6b3b606e8e2bdc9e6797783e39891a1bbad8030",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.commit",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ec9b8ca1669316280c03e10190e6770fb29e280486e06192886b2ad527315ffb",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.diagnostics",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 14,'
    '      "rendered_text_digest": "sha256:1d0ea7ac55d0a5ea1c1989e8e3c59b28ac9e6ffb2a5d2b10a8c75665177aefc0",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.graph",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:13ef0ddb177356fb67f5e5207aa771d3a093534578ea2de00eb098d8a82be5c5",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.package",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:f5e0ea1dc6319c0e690b936c68c59f470848bc20cb3fe4e86bd71ba541b42e78",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.persistence",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:612b37a1ebabf52a525c4dbf01fbbf27a636cccc57b95d2e4d64760011c853c8",'
    '      "section_key": "api.service_protocol.capability_protocol:meta.runtime_read_model",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:daa4b89d60509464dca6c7a232a3fddf62e9a43763d3dc7cec0b62a54a7a63c8",'
    '      "section_key": "api.service_protocol.api_protocol:meta",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:c609824fa331ec13ec4f652d104121506b4942cfe068256e9bb7c1dbfee5b147",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 57,'
    '      "rendered_text_digest": "sha256:a62ea9373fe363f5cc546b3115cf65a7fd899a0e750a1f35f45099027f2ff9ac",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 44'
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
    "AwareMetaServiceProtocol",
    "MetaApiServiceProtocol",
    "MetaCommitCapabilityServiceProtocol",
    "MetaDiagnosticsCapabilityServiceProtocol",
    "MetaGraphCapabilityServiceProtocol",
    "MetaPackageCapabilityServiceProtocol",
    "MetaPersistenceCapabilityServiceProtocol",
    "MetaRuntimeReadModelCapabilityServiceProtocol",
    "MetaCommitSubscribeStreamEvent",
    "META__COMMIT__SUBSCRIBE_ENDPOINT_REF",
    "META__COMMIT__SUBSCRIBE_PROTOCOL_BINDING",
    "invoke_meta__commit__subscribe",
    "stream_invoke_meta__commit__subscribe",
    "META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF",
    "META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_PROTOCOL_BINDING",
    "invoke_meta__diagnostics__analyze_object_config_graph_completeness",
    "META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF",
    "META__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING",
    "invoke_meta__graph__get_lane_head",
    "META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING",
    "invoke_meta__graph__get_object_instance_graph_commit",
    "META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF",
    "META__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING",
    "invoke_meta__graph__invoke_function",
    "META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF",
    "META__GRAPH__INVOKE_TEMPORAL_FUNCTION_PROTOCOL_BINDING",
    "invoke_meta__graph__invoke_temporal_function",
    "META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF",
    "META__GRAPH__RESOLVE_GRAPH_VIEW_PROTOCOL_BINDING",
    "invoke_meta__graph__resolve_graph_view",
    "META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF",
    "META__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING",
    "invoke_meta__graph__resolve_projection",
    "META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF",
    "META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING",
    "invoke_meta__package__ensure_object_config_graph_package",
    "META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF",
    "META__PERSISTENCE__ENSURE_DATABASE_READY_PROTOCOL_BINDING",
    "invoke_meta__persistence__ensure_database_ready",
    "META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF",
    "META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_PROTOCOL_BINDING",
    "invoke_meta__runtime_read_model__describe_workspace",
]
