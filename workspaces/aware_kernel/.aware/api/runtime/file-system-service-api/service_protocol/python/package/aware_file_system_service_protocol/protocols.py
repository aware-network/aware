# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
    ApplyFileSystemDeltaResponse,
    CollectFileSystemDeltaRequest,
    CollectFileSystemDeltaResponse,
    ResolveFileSystemBackendCapabilitiesRequest,
    ResolveFileSystemBackendCapabilitiesResponse,
    ScanFileSystemSnapshotRequest,
    ScanFileSystemSnapshotResponse,
    VerifyFileSystemRootRequest,
    VerifyFileSystemRootResponse,
)

API_PACKAGE_NAME: Final[str] = "file-system-service-api"
API_FQN_PREFIX: Final[str] = "aware_file_system_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_file_system_service_api"


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


async def invoke_filesystem__backend__capabilities(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveFileSystemBackendCapabilitiesResponse:
    typed_handler = cast(AwareFileSystemServiceProtocol, handler)
    typed_request = ResolveFileSystemBackendCapabilitiesRequest.model_validate(request)
    return await typed_handler.filesystem.backend.capabilities(typed_request)


FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF: Final[str] = "filesystem.backend.capabilities"
FILESYSTEM__BACKEND__CAPABILITIES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF,
        api_name="filesystem",
        capability_name="backend",
        endpoint_name="capabilities",
        request_type_ref="aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesRequest",
        response_type_ref="aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_filesystem__backend__capabilities,
    )
)


async def invoke_filesystem__delta__apply(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyFileSystemDeltaResponse:
    typed_handler = cast(AwareFileSystemServiceProtocol, handler)
    typed_request = ApplyFileSystemDeltaRequest.model_validate(request)
    return await typed_handler.filesystem.delta.apply(typed_request)


FILESYSTEM__DELTA__APPLY_ENDPOINT_REF: Final[str] = "filesystem.delta.apply"
FILESYSTEM__DELTA__APPLY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=FILESYSTEM__DELTA__APPLY_ENDPOINT_REF,
    api_name="filesystem",
    capability_name="delta",
    endpoint_name="apply",
    request_type_ref="aware_file_system_service_dto.file_system.ApplyFileSystemDeltaRequest",
    response_type_ref="aware_file_system_service_dto.file_system.ApplyFileSystemDeltaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_filesystem__delta__apply,
)


async def invoke_filesystem__delta__collect(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> CollectFileSystemDeltaResponse:
    typed_handler = cast(AwareFileSystemServiceProtocol, handler)
    typed_request = CollectFileSystemDeltaRequest.model_validate(request)
    return await typed_handler.filesystem.delta.collect(typed_request)


FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF: Final[str] = "filesystem.delta.collect"
FILESYSTEM__DELTA__COLLECT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF,
    api_name="filesystem",
    capability_name="delta",
    endpoint_name="collect",
    request_type_ref="aware_file_system_service_dto.file_system.CollectFileSystemDeltaRequest",
    response_type_ref="aware_file_system_service_dto.file_system.CollectFileSystemDeltaResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_filesystem__delta__collect,
)


async def invoke_filesystem__root__verify(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> VerifyFileSystemRootResponse:
    typed_handler = cast(AwareFileSystemServiceProtocol, handler)
    typed_request = VerifyFileSystemRootRequest.model_validate(request)
    return await typed_handler.filesystem.root.verify(typed_request)


FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF: Final[str] = "filesystem.root.verify"
FILESYSTEM__ROOT__VERIFY_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF,
    api_name="filesystem",
    capability_name="root",
    endpoint_name="verify",
    request_type_ref="aware_file_system_service_dto.file_system.VerifyFileSystemRootRequest",
    response_type_ref="aware_file_system_service_dto.file_system.VerifyFileSystemRootResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_filesystem__root__verify,
)


async def invoke_filesystem__snapshot__scan(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ScanFileSystemSnapshotResponse:
    typed_handler = cast(AwareFileSystemServiceProtocol, handler)
    typed_request = ScanFileSystemSnapshotRequest.model_validate(request)
    return await typed_handler.filesystem.snapshot.scan(typed_request)


FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF: Final[str] = "filesystem.snapshot.scan"
FILESYSTEM__SNAPSHOT__SCAN_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF,
    api_name="filesystem",
    capability_name="snapshot",
    endpoint_name="scan",
    request_type_ref="aware_file_system_service_dto.file_system.ScanFileSystemSnapshotRequest",
    response_type_ref="aware_file_system_service_dto.file_system.ScanFileSystemSnapshotResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_filesystem__snapshot__scan,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF: FILESYSTEM__BACKEND__CAPABILITIES_PROTOCOL_BINDING,
    FILESYSTEM__DELTA__APPLY_ENDPOINT_REF: FILESYSTEM__DELTA__APPLY_PROTOCOL_BINDING,
    FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF: FILESYSTEM__DELTA__COLLECT_PROTOCOL_BINDING,
    FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF: FILESYSTEM__ROOT__VERIFY_PROTOCOL_BINDING,
    FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF: FILESYSTEM__SNAPSHOT__SCAN_PROTOCOL_BINDING,
}


class FilesystemBackendCapabilityServiceProtocol(Protocol):

    async def capabilities(
        self, request: ResolveFileSystemBackendCapabilitiesRequest
    ) -> ResolveFileSystemBackendCapabilitiesResponse: ...


class FilesystemDeltaCapabilityServiceProtocol(Protocol):

    async def apply(self, request: ApplyFileSystemDeltaRequest) -> ApplyFileSystemDeltaResponse: ...

    async def collect(self, request: CollectFileSystemDeltaRequest) -> CollectFileSystemDeltaResponse: ...


class FilesystemRootCapabilityServiceProtocol(Protocol):

    async def verify(self, request: VerifyFileSystemRootRequest) -> VerifyFileSystemRootResponse: ...


class FilesystemSnapshotCapabilityServiceProtocol(Protocol):

    async def scan(self, request: ScanFileSystemSnapshotRequest) -> ScanFileSystemSnapshotResponse: ...


class FilesystemApiServiceProtocol(Protocol):
    backend: FilesystemBackendCapabilityServiceProtocol
    delta: FilesystemDeltaCapabilityServiceProtocol
    root: FilesystemRootCapabilityServiceProtocol
    snapshot: FilesystemSnapshotCapabilityServiceProtocol


class AwareFileSystemServiceProtocol(Protocol):
    filesystem: FilesystemApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:1e798294ebce7a6aabd46e92420989b56001ff6c97f293fc6a91d6b787d0729d",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 25,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:9100be6d24c721a45ba4dd19042f37de8adddbbefe4081647dcfdd269d6c723a",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:filesystem.backend.capabilities",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:filesystem.delta.apply",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:filesystem.delta.collect",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:filesystem.root.verify",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:filesystem.snapshot.scan",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f76c9d96e3830f5d612f7c4c851341de2e477d0938742e1705d3470f16a43542",'
    '      "section_key": "api.service_protocol.endpoint_invoker:filesystem.backend.capabilities",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:838843092b6b29cd03f29fb4585b667f493f0f36cb5d2b758ddfb57b8746ff6e",'
    '      "section_key": "api.service_protocol.endpoint_binding:filesystem.backend.capabilities",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:417914002113b577ccf1208638433b96ec1f7185db5d8f3e99d306198b1da00c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:filesystem.delta.apply",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6349073d5b8d8508a40ef1802a9029a097695e3f8cca4e74d780e3659c03b51c",'
    '      "section_key": "api.service_protocol.endpoint_binding:filesystem.delta.apply",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dd8d29a9fc704c746edf71aaa3a8807cd142a6c22938293bf59ec48431541fcc",'
    '      "section_key": "api.service_protocol.endpoint_invoker:filesystem.delta.collect",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:1ca6c9733aad7437ec6cbc602c62ef59d410a96eaf488822e0edc0f3efd4203d",'
    '      "section_key": "api.service_protocol.endpoint_binding:filesystem.delta.collect",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:80ba49265be6b0a8b2f728e42e91296b59c17d3fdf26b6354edad0aa1a0f86e3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:filesystem.root.verify",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:58cea1f11156b8e893ff081e1042b63dd760186d7d0c9d7a2a85510e7dfc68e7",'
    '      "section_key": "api.service_protocol.endpoint_binding:filesystem.root.verify",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d9b30ab9d967252a72800e06d9b0e0c891a5ac3860916bf579b9f0f3e40c1dc6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:filesystem.snapshot.scan",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:9270b7838dd05495ce451835c59b8a0cfe781e9bd897944b76ce5f409f4f817a",'
    '      "section_key": "api.service_protocol.endpoint_binding:filesystem.snapshot.scan",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:8481ccea886e0dc75eed3ceba4a8473ed2db14f0a304def203324fff00e2fd45",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:908f1c31d7a2a082ee799375c1bcb930d2d46d160f099b7e57b7744960e32261",'
    '      "section_key": "api.service_protocol.capability_protocol:filesystem.backend",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:3fff4f2bd829380ad14a5388eee02f73f0de1bd812d8b404dc8079f681f8fcb4",'
    '      "section_key": "api.service_protocol.capability_protocol:filesystem.delta",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ae9f858b7ad0bbac8a79b7234f9a69749b6357cd8c8f5ad61e26d61c4ce9097d",'
    '      "section_key": "api.service_protocol.capability_protocol:filesystem.root",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b6b10bc1441cfc5953f8832712aa52ee8954251435d2922d56b771ee4aea949e",'
    '      "section_key": "api.service_protocol.capability_protocol:filesystem.snapshot",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:be87d6b77f68d6cd572ecaaa5f3d2587e4dc257893fdea1e074a1396e7fe2ce2",'
    '      "section_key": "api.service_protocol.api_protocol:filesystem",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:8f7b5fb332a83e5f21deae5fa7d4f281649f4b1cdc4b24991fd71de38d20f932",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 35,'
    '      "rendered_text_digest": "sha256:55cb38eff3414fee012ede57cfae7e22f931840777816ed7c522c5b952d28365",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 24'
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
    "AwareFileSystemServiceProtocol",
    "FilesystemApiServiceProtocol",
    "FilesystemBackendCapabilityServiceProtocol",
    "FilesystemDeltaCapabilityServiceProtocol",
    "FilesystemRootCapabilityServiceProtocol",
    "FilesystemSnapshotCapabilityServiceProtocol",
    "FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF",
    "FILESYSTEM__BACKEND__CAPABILITIES_PROTOCOL_BINDING",
    "invoke_filesystem__backend__capabilities",
    "FILESYSTEM__DELTA__APPLY_ENDPOINT_REF",
    "FILESYSTEM__DELTA__APPLY_PROTOCOL_BINDING",
    "invoke_filesystem__delta__apply",
    "FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF",
    "FILESYSTEM__DELTA__COLLECT_PROTOCOL_BINDING",
    "invoke_filesystem__delta__collect",
    "FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF",
    "FILESYSTEM__ROOT__VERIFY_PROTOCOL_BINDING",
    "invoke_filesystem__root__verify",
    "FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF",
    "FILESYSTEM__SNAPSHOT__SCAN_PROTOCOL_BINDING",
    "invoke_filesystem__snapshot__scan",
]
