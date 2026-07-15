# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_content_service_dto.content.content_service_operation import (
    MaterializeContentPackageRequest,
    MaterializeContentPackageResponse,
    ResolveContentTextRequest,
    ResolveContentTextResponse,
)

API_PACKAGE_NAME: Final[str] = "content-service-api"
API_FQN_PREFIX: Final[str] = "aware_content_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_content_service_api"


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


async def invoke_content__package__materialize_content_package(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MaterializeContentPackageResponse:
    typed_handler = cast(AwareContentServiceProtocol, handler)
    typed_request = MaterializeContentPackageRequest.model_validate(request)
    return await typed_handler.content.package.materialize_content_package(typed_request)


CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF: Final[str] = "content.package.materialize_content_package"
CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF,
        api_name="content",
        capability_name="package",
        endpoint_name="materialize_content_package",
        request_type_ref="aware_content_service_dto.content.MaterializeContentPackageRequest",
        response_type_ref="aware_content_service_dto.content.MaterializeContentPackageResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_content__package__materialize_content_package,
    )
)


async def invoke_content__text__resolve_content_text(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveContentTextResponse:
    typed_handler = cast(AwareContentServiceProtocol, handler)
    typed_request = ResolveContentTextRequest.model_validate(request)
    return await typed_handler.content.text.resolve_content_text(typed_request)


CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF: Final[str] = "content.text.resolve_content_text"
CONTENT__TEXT__RESOLVE_CONTENT_TEXT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF,
        api_name="content",
        capability_name="text",
        endpoint_name="resolve_content_text",
        request_type_ref="aware_content_service_dto.content.ResolveContentTextRequest",
        response_type_ref="aware_content_service_dto.content.ResolveContentTextResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_content__text__resolve_content_text,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF: CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_PROTOCOL_BINDING,
    CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF: CONTENT__TEXT__RESOLVE_CONTENT_TEXT_PROTOCOL_BINDING,
}


class ContentPackageCapabilityServiceProtocol(Protocol):

    async def materialize_content_package(
        self, request: MaterializeContentPackageRequest
    ) -> MaterializeContentPackageResponse: ...


class ContentTextCapabilityServiceProtocol(Protocol):

    async def resolve_content_text(self, request: ResolveContentTextRequest) -> ResolveContentTextResponse: ...


class ContentApiServiceProtocol(Protocol):
    package: ContentPackageCapabilityServiceProtocol
    text: ContentTextCapabilityServiceProtocol


class AwareContentServiceProtocol(Protocol):
    content: ContentApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:59638eca40154daf53ce61234a93210a3dd09bce8ed220399a445447b0d6e845",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 14,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:6e0d0ea428ea73110bd8aab53a827f66f593487e01ed80416cbad72f50c4ddbc",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:content.package.materialize_content_package",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a1d99eb9ea6dabc8c3201e97f30e4bf10fe26ffd14167b457a1aba21b3d88617",'
    '      "section_key": "api.service_protocol.endpoint_invoker:content.package.materialize_content_package",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:380f0db1f07c1e19bacc3566175b2377beab1da67bca5d257f67518b576cd35c",'
    '      "section_key": "api.service_protocol.endpoint_binding:content.package.materialize_content_package",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e2915d7f8823e128c10ee1144b7e62b116d59dd3e9f8f3336c3987529d1508f4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a06a597132773eafc629f6bcbf3bd3a1207df4c9ffa369a7c3e98fad0b57036a",'
    '      "section_key": "api.service_protocol.endpoint_binding:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dfad076b422828a1a0108754419529a51952e9c2fa11fd7bc9be849fc5e2c435",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e2df2cacc987b83e1e9271fa7c8864befdb067fa52eb9ca00ef69754869673a4",'
    '      "section_key": "api.service_protocol.capability_protocol:content.package",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:773dd6ea6dca38d75ad18dc5e42d0179102b488e61ee56d81d074f90acd68ca0",'
    '      "section_key": "api.service_protocol.capability_protocol:content.text",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e1de17ede4756f047f31cfd5e898e86ad052efe40b5ecf8c466bbb25b9eaa71d",'
    '      "section_key": "api.service_protocol.api_protocol:content",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:2b20eace69941a4e1ddb0df3cebfedca3b5bf3d0525b20eb04d3dba7db4977d6",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 24,'
    '      "rendered_text_digest": "sha256:6c7dc14e3de3a7aa6d1e55f727cdffe0e08dacc1397c6894f4dda06308f544d6",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 13'
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
    "AwareContentServiceProtocol",
    "ContentApiServiceProtocol",
    "ContentPackageCapabilityServiceProtocol",
    "ContentTextCapabilityServiceProtocol",
    "CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF",
    "CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_PROTOCOL_BINDING",
    "invoke_content__package__materialize_content_package",
    "CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF",
    "CONTENT__TEXT__RESOLVE_CONTENT_TEXT_PROTOCOL_BINDING",
    "invoke_content__text__resolve_content_text",
]
