# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_ontology_service_dto.graph.config.package_compile import (
    OntologyObjectConfigGraphPackageEnsureRequest,
    OntologyObjectConfigGraphPackageEnsureResponse,
)
from aware_ontology_service_dto.graph.instance.commit_event import (
    OntologyCommitEventEnvelope,
    OntologyCommitSubscriptionRequest,
    OntologyCommitSubscriptionResponse,
)
from aware_ontology_service_dto.graph.instance.function_call import (
    OntologyGraphGetLaneHeadRequest,
    OntologyGraphGetLaneHeadResponse,
    OntologyGraphGetObjectInstanceGraphCommitRequest,
    OntologyGraphGetObjectInstanceGraphCommitResponse,
    OntologyGraphInvokeFunctionRequest,
    OntologyGraphInvokeFunctionResponse,
    OntologyGraphResolveProjectionRequest,
    OntologyGraphResolveProjectionResponse,
)
from aware_ontology_service_dto.persistence.readiness import (
    OntologyPersistenceEnsureReadyRequest,
    OntologyPersistenceEnsureReadyResponse,
)
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSetResolveRequest,
    OntologyRuntimeArtifactSetResolveResponse,
)

API_PACKAGE_NAME: Final[str] = "ontology-service-api"
API_FQN_PREFIX: Final[str] = "aware_ontology_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_ontology_service_api"


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


OntologyCommitSubscribeStreamEvent: TypeAlias = OntologyCommitEventEnvelope


async def invoke_ontology__commit__subscribe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyCommitSubscriptionResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyCommitSubscriptionRequest.model_validate(request)
    return await typed_handler.ontology.commit.subscribe(typed_request)


def stream_invoke_ontology__commit__subscribe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[OntologyCommitSubscribeStreamEvent]:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyCommitSubscriptionRequest.model_validate(request)
    _ = execution
    return typed_handler.ontology.commit.stream_subscribe(typed_request)


ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF: Final[str] = "ontology.commit.subscribe"
ONTOLOGY__COMMIT__SUBSCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    api_name="ontology",
    capability_name="commit",
    endpoint_name="subscribe",
    request_type_ref="aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionRequest",
    response_type_ref="aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionResponse",
    stream_event_type_refs=("aware_ontology_service_dto.graph.instance.OntologyCommitEventEnvelope",),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_ontology__commit__subscribe,
    fulfillment_bindings=(),
    invoke=invoke_ontology__commit__subscribe,
)


async def invoke_ontology__graph__get_lane_head(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyGraphGetLaneHeadResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyGraphGetLaneHeadRequest.model_validate(request)
    return await typed_handler.ontology.graph.get_lane_head(typed_request)


ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "ontology.graph.get_lane_head"
ONTOLOGY__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    api_name="ontology",
    capability_name="graph",
    endpoint_name="get_lane_head",
    request_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadRequest",
    response_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_ontology__graph__get_lane_head,
)


async def invoke_ontology__graph__get_object_instance_graph_commit(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyGraphGetObjectInstanceGraphCommitResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyGraphGetObjectInstanceGraphCommitRequest.model_validate(request)
    return await typed_handler.ontology.graph.get_object_instance_graph_commit(typed_request)


ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = (
    "ontology.graph.get_object_instance_graph_commit"
)
ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
        api_name="ontology",
        capability_name="graph",
        endpoint_name="get_object_instance_graph_commit",
        request_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitRequest",
        response_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__graph__get_object_instance_graph_commit,
    )
)


async def invoke_ontology__graph__invoke_function(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyGraphInvokeFunctionResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyGraphInvokeFunctionRequest.model_validate(request)
    return await typed_handler.ontology.graph.invoke_function(typed_request)


ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "ontology.graph.invoke_function"
ONTOLOGY__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
        api_name="ontology",
        capability_name="graph",
        endpoint_name="invoke_function",
        request_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionRequest",
        response_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__graph__invoke_function,
    )
)


async def invoke_ontology__graph__resolve_projection(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyGraphResolveProjectionResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyGraphResolveProjectionRequest.model_validate(request)
    return await typed_handler.ontology.graph.resolve_projection(typed_request)


ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: Final[str] = "ontology.graph.resolve_projection"
ONTOLOGY__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
        api_name="ontology",
        capability_name="graph",
        endpoint_name="resolve_projection",
        request_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionRequest",
        response_type_ref="aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__graph__resolve_projection,
    )
)


async def invoke_ontology__package__ensure_object_config_graph_package(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyObjectConfigGraphPackageEnsureResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyObjectConfigGraphPackageEnsureRequest.model_validate(request)
    return await typed_handler.ontology.package.ensure_object_config_graph_package(typed_request)


ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: Final[str] = (
    "ontology.package.ensure_object_config_graph_package"
)
ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
        api_name="ontology",
        capability_name="package",
        endpoint_name="ensure_object_config_graph_package",
        request_type_ref="aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureRequest",
        response_type_ref="aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__package__ensure_object_config_graph_package,
    )
)


async def invoke_ontology__persistence__ensure_ready(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyPersistenceEnsureReadyResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyPersistenceEnsureReadyRequest.model_validate(request)
    return await typed_handler.ontology.persistence.ensure_ready(typed_request)


ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF: Final[str] = "ontology.persistence.ensure_ready"
ONTOLOGY__PERSISTENCE__ENSURE_READY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF,
        api_name="ontology",
        capability_name="persistence",
        endpoint_name="ensure_ready",
        request_type_ref="aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyRequest",
        response_type_ref="aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__persistence__ensure_ready,
    )
)


async def invoke_ontology__runtime__resolve_runtime_artifact_set(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> OntologyRuntimeArtifactSetResolveResponse:
    typed_handler = cast(AwareOntologyServiceProtocol, handler)
    typed_request = OntologyRuntimeArtifactSetResolveRequest.model_validate(request)
    return await typed_handler.ontology.runtime.resolve_runtime_artifact_set(typed_request)


ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF: Final[str] = (
    "ontology.runtime.resolve_runtime_artifact_set"
)
ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF,
        api_name="ontology",
        capability_name="runtime",
        endpoint_name="resolve_runtime_artifact_set",
        request_type_ref="aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveRequest",
        response_type_ref="aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_ontology__runtime__resolve_runtime_artifact_set,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF: ONTOLOGY__COMMIT__SUBSCRIBE_PROTOCOL_BINDING,
    ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: ONTOLOGY__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING,
    ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING,
    ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: ONTOLOGY__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING,
    ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: ONTOLOGY__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING,
    ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING,
    ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF: ONTOLOGY__PERSISTENCE__ENSURE_READY_PROTOCOL_BINDING,
    ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF: ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_PROTOCOL_BINDING,
}


class OntologyCommitCapabilityServiceProtocol(Protocol):

    async def subscribe(self, request: OntologyCommitSubscriptionRequest) -> OntologyCommitSubscriptionResponse: ...

    def stream_subscribe(
        self, request: OntologyCommitSubscriptionRequest
    ) -> AsyncIterator[OntologyCommitSubscribeStreamEvent]: ...


class OntologyGraphCapabilityServiceProtocol(Protocol):

    async def get_lane_head(self, request: OntologyGraphGetLaneHeadRequest) -> OntologyGraphGetLaneHeadResponse: ...

    async def get_object_instance_graph_commit(
        self, request: OntologyGraphGetObjectInstanceGraphCommitRequest
    ) -> OntologyGraphGetObjectInstanceGraphCommitResponse: ...

    async def invoke_function(
        self, request: OntologyGraphInvokeFunctionRequest
    ) -> OntologyGraphInvokeFunctionResponse: ...

    async def resolve_projection(
        self, request: OntologyGraphResolveProjectionRequest
    ) -> OntologyGraphResolveProjectionResponse: ...


class OntologyPackageCapabilityServiceProtocol(Protocol):

    async def ensure_object_config_graph_package(
        self, request: OntologyObjectConfigGraphPackageEnsureRequest
    ) -> OntologyObjectConfigGraphPackageEnsureResponse: ...


class OntologyPersistenceCapabilityServiceProtocol(Protocol):

    async def ensure_ready(
        self, request: OntologyPersistenceEnsureReadyRequest
    ) -> OntologyPersistenceEnsureReadyResponse: ...


class OntologyRuntimeCapabilityServiceProtocol(Protocol):

    async def resolve_runtime_artifact_set(
        self, request: OntologyRuntimeArtifactSetResolveRequest
    ) -> OntologyRuntimeArtifactSetResolveResponse: ...


class OntologyApiServiceProtocol(Protocol):
    commit: OntologyCommitCapabilityServiceProtocol
    graph: OntologyGraphCapabilityServiceProtocol
    package: OntologyPackageCapabilityServiceProtocol
    persistence: OntologyPersistenceCapabilityServiceProtocol
    runtime: OntologyRuntimeCapabilityServiceProtocol


class AwareOntologyServiceProtocol(Protocol):
    ontology: OntologyApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:a566c25fe5c63fb02ed178403f4ff99b764606f95f09f99cfc684e846b289f3e",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 35,'
    '  "sections": ['
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:7477bf52edc3728ebdb694be70cec0b83756253d6f2f4d8df266cafa0c1d4236",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.persistence.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:ontology.runtime.resolve_runtime_artifact_set",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:aac0f38c3376be410213dd0ef9f478a12653d3a13e096327db1c784ea244847b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:6dbb57ac0a6ae31a8924e2e749d25fa57e1529426902b0b0582dede7d81a6a42",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.commit.subscribe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:3f7144f1deff1c71ed9d24451e451bb0f17dc5b8cfee0d0f02745a704142ee82",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:ac3537d48c85085c15121efb3c4861c17043958742fffae3415bbf73f7b1bea3",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.graph.get_lane_head",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4199f4fed0ddb74ec41921d091423c468108d618bd0307bbec4093cefb4e4a7c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d3e7df351e5e52dc4919895791a13d15922b7e2e0d49faaaae097905c2fa60d9",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.graph.get_object_instance_graph_commit",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ba21ff0e7cb48bcaadee1e656f6599a0b587c83f93fe2b033bcf3ac8ddd71e0d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0ee224dfb49992044b23288d5e3bcc947e6e6de155ca4e8e6647382b0ac3d2dd",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.graph.invoke_function",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:49f19d8e459ee660e30059bbee9e297ed491eeab26f7e03f2ce986058391b357",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:3a8942ef89b58821e58f1bfdd02a7cb9c6ce2e7fb706e09d0a58cf9e5d21f643",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.graph.resolve_projection",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:6a8e48a7fd5da48b40d2e12093f7f305ce19f297f1165f307e68ef6f77282a36",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:31896ce8891a269f25e6459de5b277174cd5559c6fd53638212ab17ecbbb175d",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.package.ensure_object_config_graph_package",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dbe96d23ce59b018976298a9ef1d5e7e250c84d2f60fcba1a01b7c7d582d2e6d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.persistence.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d8a2e20f05fb2b93a90b2520661780316a81cca8221d293f8a73ebfc5e95eacf",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.persistence.ensure_ready",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:8cc2327f3fe36cc5c74f34d4aea4c1df147033de514195a6736e2aaf846279f6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:ontology.runtime.resolve_runtime_artifact_set",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6967a40d68fdbefbc4bb6cee13525b238d1bc9c03b2ef613ad2ff6e85fddecfc",'
    '      "section_key": "api.service_protocol.endpoint_binding:ontology.runtime.resolve_runtime_artifact_set",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 11,'
    '      "rendered_text_digest": "sha256:af449967682512f13b9f1243211a6d8807824dab3fb0b02ac4e03fffdf0274fc",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:efb919040da59ff950bd691fdbf4debe444bcf22ec073c8dc3d54bb6b18f1387",'
    '      "section_key": "api.service_protocol.capability_protocol:ontology.commit",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:22f09e3de29de02d1db33a10d0a29e6e08b30c3e55eacf9c3094455b45963daa",'
    '      "section_key": "api.service_protocol.capability_protocol:ontology.graph",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:18408c85d2d3b07d8f0908b140851bcd5112421ab5b88740a31b8d9621bcf96b",'
    '      "section_key": "api.service_protocol.capability_protocol:ontology.package",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:61a42cfd418dba3a55f7be2a5e1ae57e68e1241810d6b34a087fa892a00ee768",'
    '      "section_key": "api.service_protocol.capability_protocol:ontology.persistence",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:07c0785325709c5793f1f2226e92cd88825cc27583e1ad96e391e31041987abb",'
    '      "section_key": "api.service_protocol.capability_protocol:ontology.runtime",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 7,'
    '      "rendered_text_digest": "sha256:7a38925d299602d9f9c39d3883b92aa3b6786e1cefa4f14495f47ea66566a762",'
    '      "section_key": "api.service_protocol.api_protocol:ontology",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:34fb371ec5a432964db79854d62159328878ee79b549844da27d2a8ef1b46655",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 47,'
    '      "rendered_text_digest": "sha256:45db831ffaff29638116ff89a990916fe77ac0308d73b1de4908cb05a62e6362",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 34'
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
    "AwareOntologyServiceProtocol",
    "OntologyApiServiceProtocol",
    "OntologyCommitCapabilityServiceProtocol",
    "OntologyGraphCapabilityServiceProtocol",
    "OntologyPackageCapabilityServiceProtocol",
    "OntologyPersistenceCapabilityServiceProtocol",
    "OntologyRuntimeCapabilityServiceProtocol",
    "OntologyCommitSubscribeStreamEvent",
    "ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF",
    "ONTOLOGY__COMMIT__SUBSCRIBE_PROTOCOL_BINDING",
    "invoke_ontology__commit__subscribe",
    "stream_invoke_ontology__commit__subscribe",
    "ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__GET_LANE_HEAD_PROTOCOL_BINDING",
    "invoke_ontology__graph__get_lane_head",
    "ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_PROTOCOL_BINDING",
    "invoke_ontology__graph__get_object_instance_graph_commit",
    "ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__INVOKE_FUNCTION_PROTOCOL_BINDING",
    "invoke_ontology__graph__invoke_function",
    "ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__RESOLVE_PROJECTION_PROTOCOL_BINDING",
    "invoke_ontology__graph__resolve_projection",
    "ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF",
    "ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_PROTOCOL_BINDING",
    "invoke_ontology__package__ensure_object_config_graph_package",
    "ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF",
    "ONTOLOGY__PERSISTENCE__ENSURE_READY_PROTOCOL_BINDING",
    "invoke_ontology__persistence__ensure_ready",
    "ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF",
    "ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_PROTOCOL_BINDING",
    "invoke_ontology__runtime__resolve_runtime_artifact_set",
]
