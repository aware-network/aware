# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_service_service_dto.comms.models.service import ServiceOperationRequest, ServiceOperationResponse

API_PACKAGE_NAME: Final[str] = "service-service-api"
API_FQN_PREFIX: Final[str] = "aware_service_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_service_service_api"


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


async def invoke_service__operation__invoke(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ServiceOperationResponse:
    typed_handler = cast(AwareServiceServiceProtocol, handler)
    typed_request = ServiceOperationRequest.model_validate(request)
    return await typed_handler.service.operation.invoke(typed_request)


SERVICE__OPERATION__INVOKE_ENDPOINT_REF: Final[str] = "service.operation.invoke"
SERVICE__OPERATION__INVOKE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=SERVICE__OPERATION__INVOKE_ENDPOINT_REF,
    api_name="service",
    capability_name="operation",
    endpoint_name="invoke",
    request_type_ref="aware_service_service_dto.comms.models.ServiceOperationRequest",
    response_type_ref="aware_service_service_dto.comms.models.ServiceOperationResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_service__operation__invoke,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    SERVICE__OPERATION__INVOKE_ENDPOINT_REF: SERVICE__OPERATION__INVOKE_PROTOCOL_BINDING,
}


class ServiceOperationCapabilityServiceProtocol(Protocol):

    async def invoke(self, request: ServiceOperationRequest) -> ServiceOperationResponse: ...


class ServiceApiServiceProtocol(Protocol):
    operation: ServiceOperationCapabilityServiceProtocol


class AwareServiceServiceProtocol(Protocol):
    service: ServiceApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:a2b5a6491cf3453a518dee2798f0fd5a5772c312ca3dcee9706aa4a15f23bdbf",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 10,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:23b167299e734c223cf0f53a3409fbf562a3dff0265f670284be5ac4b5504007",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:service.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f662a6a8dda3ac9c57d540f2fc114ae8dcdd5adfb03bd58350c49e7e2197bb9e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:service.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:05e0480da20c0b8dc3738c74820328793d96e6e06255e778e8b18542bb82126b",'
    '      "section_key": "api.service_protocol.endpoint_binding:service.operation.invoke",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:19869ed94c767d47d2331499eeba11c1d66935aee3abb3bfc3ca35f70650ac56",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:841d2e46ad9518b59ce217f4ba470c5a7cdeba1ee67db5464243ba91965aa6c7",'
    '      "section_key": "api.service_protocol.capability_protocol:service.operation",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:ee1c9a0908700ee02e3b14927e5864bb32ab4192c640cac7a2f8b97408863b34",'
    '      "section_key": "api.service_protocol.api_protocol:service",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:41d9f27adb7d378c1b08eba0c55a279e0a17c8a0143735c8e177e359f7cd18f4",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:4236eb87bca8145b7f574d6c41bdcd0b8a41fdb57064e55b6d22336eb0a649ec",'
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
    "AwareServiceServiceProtocol",
    "ServiceApiServiceProtocol",
    "ServiceOperationCapabilityServiceProtocol",
    "SERVICE__OPERATION__INVOKE_ENDPOINT_REF",
    "SERVICE__OPERATION__INVOKE_PROTOCOL_BINDING",
    "invoke_service__operation__invoke",
]
