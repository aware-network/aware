# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_storage_service_dto.storage.service_operation import (
    DescribeStorageBlobRequest,
    DescribeStorageBlobResponse,
    RegisterStorageBlobRequest,
    RegisterStorageBlobResponse,
    ResolveStorageMediaRequest,
    ResolveStorageMediaResponse,
)

API_PACKAGE_NAME: Final[str] = "storage-service-api"
API_FQN_PREFIX: Final[str] = "aware_storage_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_storage_service_api"


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


async def invoke_storage__blob__describe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeStorageBlobResponse:
    typed_handler = cast(AwareStorageServiceProtocol, handler)
    typed_request = DescribeStorageBlobRequest.model_validate(request)
    return await typed_handler.storage.blob.describe(typed_request)


STORAGE__BLOB__DESCRIBE_ENDPOINT_REF: Final[str] = "storage.blob.describe"
STORAGE__BLOB__DESCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=STORAGE__BLOB__DESCRIBE_ENDPOINT_REF,
    api_name="storage",
    capability_name="blob",
    endpoint_name="describe",
    request_type_ref="aware_storage_service_dto.storage.DescribeStorageBlobRequest",
    response_type_ref="aware_storage_service_dto.storage.DescribeStorageBlobResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_storage__blob__describe,
)


async def invoke_storage__blob__register(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RegisterStorageBlobResponse:
    typed_handler = cast(AwareStorageServiceProtocol, handler)
    typed_request = RegisterStorageBlobRequest.model_validate(request)
    return await typed_handler.storage.blob.register(typed_request)


STORAGE__BLOB__REGISTER_ENDPOINT_REF: Final[str] = "storage.blob.register"
STORAGE__BLOB__REGISTER_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=STORAGE__BLOB__REGISTER_ENDPOINT_REF,
    api_name="storage",
    capability_name="blob",
    endpoint_name="register",
    request_type_ref="aware_storage_service_dto.storage.RegisterStorageBlobRequest",
    response_type_ref="aware_storage_service_dto.storage.RegisterStorageBlobResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_storage__blob__register,
)


async def invoke_storage__media__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveStorageMediaResponse:
    typed_handler = cast(AwareStorageServiceProtocol, handler)
    typed_request = ResolveStorageMediaRequest.model_validate(request)
    return await typed_handler.storage.media.resolve(typed_request)


STORAGE__MEDIA__RESOLVE_ENDPOINT_REF: Final[str] = "storage.media.resolve"
STORAGE__MEDIA__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=STORAGE__MEDIA__RESOLVE_ENDPOINT_REF,
    api_name="storage",
    capability_name="media",
    endpoint_name="resolve",
    request_type_ref="aware_storage_service_dto.storage.ResolveStorageMediaRequest",
    response_type_ref="aware_storage_service_dto.storage.ResolveStorageMediaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_storage__media__resolve,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    STORAGE__BLOB__DESCRIBE_ENDPOINT_REF: STORAGE__BLOB__DESCRIBE_PROTOCOL_BINDING,
    STORAGE__BLOB__REGISTER_ENDPOINT_REF: STORAGE__BLOB__REGISTER_PROTOCOL_BINDING,
    STORAGE__MEDIA__RESOLVE_ENDPOINT_REF: STORAGE__MEDIA__RESOLVE_PROTOCOL_BINDING,
}


class StorageBlobCapabilityServiceProtocol(Protocol):

    async def describe(self, request: DescribeStorageBlobRequest) -> DescribeStorageBlobResponse: ...

    async def register(self, request: RegisterStorageBlobRequest) -> RegisterStorageBlobResponse: ...


class StorageMediaCapabilityServiceProtocol(Protocol):

    async def resolve(self, request: ResolveStorageMediaRequest) -> ResolveStorageMediaResponse: ...


class StorageApiServiceProtocol(Protocol):
    blob: StorageBlobCapabilityServiceProtocol
    media: StorageMediaCapabilityServiceProtocol


class AwareStorageServiceProtocol(Protocol):
    storage: StorageApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:2fe56ca396e502adbaf74a42583dc3ec75cc0ed51cecf89da06e3540a23b9ca6",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 17,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:656ce2b36b3e13ffb7f607639e2a06cb355d44bb2f01744c01133a2d69402b8c",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:storage.blob.describe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:storage.blob.register",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:storage.media.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:822575016481bfa5521cdaafb912430343bdedcfa7fd99906ebb2ad16dcabbf4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:storage.blob.describe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b2c2ef15bba50075bf533de26160c4826555adaa4b62224f0ac3150fbb2294be",'
    '      "section_key": "api.service_protocol.endpoint_binding:storage.blob.describe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:11dd3b2b9db0b0a0d968e42a60fa0193dcad002a783ee6d98ec5d1c52a4a15bc",'
    '      "section_key": "api.service_protocol.endpoint_invoker:storage.blob.register",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:06a64a372a1a9921fea367bf45aae5b29b890f536c629e61e5706c1dd11e4e27",'
    '      "section_key": "api.service_protocol.endpoint_binding:storage.blob.register",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e17e57b6a3ad3fab25dfb16fe548f34960b267c95abba8f1e67ea9c73f30e1f0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:storage.media.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:88511949c6abeb4825de7133f7a8564fdbab291fef7412f1d24ce0b02b85e1e8",'
    '      "section_key": "api.service_protocol.endpoint_binding:storage.media.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:80547eacaec31e3edd1f62944dd6cb083f057a657a103b87df210e874b1d96eb",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:d41be48407649a640cead69a1a644a348aead4d3ba82a5db8aaee9336d3adfe7",'
    '      "section_key": "api.service_protocol.capability_protocol:storage.blob",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:0f203b9fa7bcb0c1c08eb9b67faae14bd1efef9f801f20a53f32080518810f82",'
    '      "section_key": "api.service_protocol.capability_protocol:storage.media",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:26130e45e80d3e5349a26ded6abdcff062f5b36e5aba191830ade956caabe5b5",'
    '      "section_key": "api.service_protocol.api_protocol:storage",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:93ba32ad15c8049839b841493a85d545b70b81963a12ab2854b940e2f22c329a",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 27,'
    '      "rendered_text_digest": "sha256:403e58a525cff2bfd2e82afcaa2add7ac1dc814bb25ae5e88bdc7c44fc3da148",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 16'
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
    "AwareStorageServiceProtocol",
    "StorageApiServiceProtocol",
    "StorageBlobCapabilityServiceProtocol",
    "StorageMediaCapabilityServiceProtocol",
    "STORAGE__BLOB__DESCRIBE_ENDPOINT_REF",
    "STORAGE__BLOB__DESCRIBE_PROTOCOL_BINDING",
    "invoke_storage__blob__describe",
    "STORAGE__BLOB__REGISTER_ENDPOINT_REF",
    "STORAGE__BLOB__REGISTER_PROTOCOL_BINDING",
    "invoke_storage__blob__register",
    "STORAGE__MEDIA__RESOLVE_ENDPOINT_REF",
    "STORAGE__MEDIA__RESOLVE_PROTOCOL_BINDING",
    "invoke_storage__media__resolve",
]
