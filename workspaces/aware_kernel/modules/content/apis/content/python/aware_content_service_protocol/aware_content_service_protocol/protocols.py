# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_content_service_dto.content.content_service_operation import (
    CommitContentTextRequest,
    CommitContentTextResponse,
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


async def invoke_content__text__commit_content_text(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> CommitContentTextResponse:
    typed_handler = cast(AwareContentServiceProtocol, handler)
    typed_request = CommitContentTextRequest.model_validate(request)
    return await typed_handler.content.text.commit_content_text(typed_request)


CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF: Final[str] = "content.text.commit_content_text"
CONTENT__TEXT__COMMIT_CONTENT_TEXT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF,
        api_name="content",
        capability_name="text",
        endpoint_name="commit_content_text",
        request_type_ref="aware_content_service_dto.content.CommitContentTextRequest",
        response_type_ref="aware_content_service_dto.content.CommitContentTextResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_content__text__commit_content_text,
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
    CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF: CONTENT__TEXT__COMMIT_CONTENT_TEXT_PROTOCOL_BINDING,
    CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF: CONTENT__TEXT__RESOLVE_CONTENT_TEXT_PROTOCOL_BINDING,
}


class ContentPackageCapabilityServiceProtocol(Protocol):

    async def materialize_content_package(
        self, request: MaterializeContentPackageRequest
    ) -> MaterializeContentPackageResponse: ...


class ContentTextCapabilityServiceProtocol(Protocol):

    async def commit_content_text(self, request: CommitContentTextRequest) -> CommitContentTextResponse: ...

    async def resolve_content_text(self, request: ResolveContentTextRequest) -> ResolveContentTextResponse: ...


class ContentApiServiceProtocol(Protocol):
    package: ContentPackageCapabilityServiceProtocol
    text: ContentTextCapabilityServiceProtocol


class AwareContentServiceProtocol(Protocol):
    content: ContentApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:7d1afb5b2faa010512484401a49b640191dc22ef170a760904e8fe5806365d42",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 17,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:d2b5fb052c11ba42674a4238055b642606f0191ed6abb50027ded096c0bf37fe",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:content.text.commit_content_text",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a1d99eb9ea6dabc8c3201e97f30e4bf10fe26ffd14167b457a1aba21b3d88617",'
    '      "section_key": "api.service_protocol.endpoint_invoker:content.package.materialize_content_package",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:380f0db1f07c1e19bacc3566175b2377beab1da67bca5d257f67518b576cd35c",'
    '      "section_key": "api.service_protocol.endpoint_binding:content.package.materialize_content_package",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d78d41c41dd4e971147cc9719e36ca75691e085dde04c180803133cb4b3c1061",'
    '      "section_key": "api.service_protocol.endpoint_invoker:content.text.commit_content_text",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:736e18c44557cecc32b38f8e374bc28544e27edf1e7612f9c29715a262aec4a5",'
    '      "section_key": "api.service_protocol.endpoint_binding:content.text.commit_content_text",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e2915d7f8823e128c10ee1144b7e62b116d59dd3e9f8f3336c3987529d1508f4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a06a597132773eafc629f6bcbf3bd3a1207df4c9ffa369a7c3e98fad0b57036a",'
    '      "section_key": "api.service_protocol.endpoint_binding:content.text.resolve_content_text",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:0e1e82f85a99519cbaa69b4a33ffa901250e6cbdb228d58f0107761a3d0eaf37",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e2df2cacc987b83e1e9271fa7c8864befdb067fa52eb9ca00ef69754869673a4",'
    '      "section_key": "api.service_protocol.capability_protocol:content.package",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:3555a3e9efb5e136c8c7e001b4017026b4c02bbf321155a7b6039a6c00ae0370",'
    '      "section_key": "api.service_protocol.capability_protocol:content.text",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e1de17ede4756f047f31cfd5e898e86ad052efe40b5ecf8c466bbb25b9eaa71d",'
    '      "section_key": "api.service_protocol.api_protocol:content",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:2b20eace69941a4e1ddb0df3cebfedca3b5bf3d0525b20eb04d3dba7db4977d6",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 27,'
    '      "rendered_text_digest": "sha256:043b0785d186bf6d6777231c8f6f192b1cec21f523a822a0d7e906420f6b577f",'
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
    "AwareContentServiceProtocol",
    "ContentApiServiceProtocol",
    "ContentPackageCapabilityServiceProtocol",
    "ContentTextCapabilityServiceProtocol",
    "CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_ENDPOINT_REF",
    "CONTENT__PACKAGE__MATERIALIZE_CONTENT_PACKAGE_PROTOCOL_BINDING",
    "invoke_content__package__materialize_content_package",
    "CONTENT__TEXT__COMMIT_CONTENT_TEXT_ENDPOINT_REF",
    "CONTENT__TEXT__COMMIT_CONTENT_TEXT_PROTOCOL_BINDING",
    "invoke_content__text__commit_content_text",
    "CONTENT__TEXT__RESOLVE_CONTENT_TEXT_ENDPOINT_REF",
    "CONTENT__TEXT__RESOLVE_CONTENT_TEXT_PROTOCOL_BINDING",
    "invoke_content__text__resolve_content_text",
]
