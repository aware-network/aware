# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_api_service_dto.comms.models.api import ApiOperationRequest, ApiOperationResponse

API_PACKAGE_NAME: Final[str] = "api-service-api"
API_FQN_PREFIX: Final[str] = "aware_api_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_api_service_api"


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


async def invoke_api__operation__invoke(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApiOperationResponse:
    typed_handler = cast(AwareApiServiceProtocol, handler)
    typed_request = ApiOperationRequest.model_validate(request)
    return await typed_handler.api.operation.invoke(typed_request)


API__OPERATION__INVOKE_ENDPOINT_REF: Final[str] = "api.operation.invoke"
API__OPERATION__INVOKE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=API__OPERATION__INVOKE_ENDPOINT_REF,
    api_name="api",
    capability_name="operation",
    endpoint_name="invoke",
    request_type_ref="aware_api_service_dto.comms.models.ApiOperationRequest",
    response_type_ref="aware_api_service_dto.comms.models.ApiOperationResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_api__operation__invoke,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    API__OPERATION__INVOKE_ENDPOINT_REF: API__OPERATION__INVOKE_PROTOCOL_BINDING,
}


class ApiOperationCapabilityServiceProtocol(Protocol):

    async def invoke(self, request: ApiOperationRequest) -> ApiOperationResponse: ...


class ApiApiServiceProtocol(Protocol):
    operation: ApiOperationCapabilityServiceProtocol


class AwareApiServiceProtocol(Protocol):
    api: ApiApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:59e2187a27ffb40a53efdfa9447748929da5af474f9ec82f3084d18965ec664a",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 10,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:79c96ae0d9502108dd31606540b860b673db78c62bb9f1c921c35a03ce37ca8c",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:api.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f58243dee0e6eee4be69ced25e8de5600469e993d070dd9a6d6c79e27ca47760",'
    '      "section_key": "api.service_protocol.endpoint_invoker:api.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:dfb5c018925e809a1cb96b795526792a5dcd9b98a88d14b47bcf64d603801aa6",'
    '      "section_key": "api.service_protocol.endpoint_binding:api.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ad5e29ad904da9824a2d1f04e91f7ada8a3493f3090f714cf24f50c3f0c1abc2",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:fffe12216cd88abda6c3fbdd827df69e5f48b35cf0d2c1163402c9a4d8d2bed4",'
    '      "section_key": "api.service_protocol.capability_protocol:api.operation",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:bbbd245c8f7ac29e36c847d3b24e9fd594e61a528b18d1b9b10f8723570ea82b",'
    '      "section_key": "api.service_protocol.api_protocol:api",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:29ca9e34aa18199e0b5c713d04f5889f354931a8726bd462a5f16264e454fb6c",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:b694a0f25bbc7fd5da2ad2a97fe2895bde35d34be8bd9ca5ca3e3b050dc20183",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 9'
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
    "AwareApiServiceProtocol",
    "ApiApiServiceProtocol",
    "ApiOperationCapabilityServiceProtocol",
    "API__OPERATION__INVOKE_ENDPOINT_REF",
    "API__OPERATION__INVOKE_PROTOCOL_BINDING",
    "invoke_api__operation__invoke",
]
