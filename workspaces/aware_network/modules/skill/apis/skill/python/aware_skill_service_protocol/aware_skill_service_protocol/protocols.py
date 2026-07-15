# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_skill_service_dto.skill.service_operation import SkillInvokeRequest, SkillInvokeResponse

API_PACKAGE_NAME: Final[str] = "skill-service-api"
API_FQN_PREFIX: Final[str] = "aware_skill_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_skill_service_api"


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


async def invoke_skill__invoke__invoke(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SkillInvokeResponse:
    typed_handler = cast(AwareSkillServiceProtocol, handler)
    typed_request = SkillInvokeRequest.model_validate(request)
    return await typed_handler.skill.invoke.invoke(typed_request)


SKILL__INVOKE__INVOKE_ENDPOINT_REF: Final[str] = "skill.invoke.invoke"
SKILL__INVOKE__INVOKE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=SKILL__INVOKE__INVOKE_ENDPOINT_REF,
    api_name="skill",
    capability_name="invoke",
    endpoint_name="invoke",
    request_type_ref="aware_skill_service_dto.skill.SkillInvokeRequest",
    response_type_ref="aware_skill_service_dto.skill.SkillInvokeResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_skill__invoke__invoke,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    SKILL__INVOKE__INVOKE_ENDPOINT_REF: SKILL__INVOKE__INVOKE_PROTOCOL_BINDING,
}


class SkillInvokeCapabilityServiceProtocol(Protocol):

    async def invoke(self, request: SkillInvokeRequest) -> SkillInvokeResponse: ...


class SkillApiServiceProtocol(Protocol):
    invoke: SkillInvokeCapabilityServiceProtocol


class AwareSkillServiceProtocol(Protocol):
    skill: SkillApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:f4a15b7dd3c5a9252c15107130d46e6789be0a0e9e0d78cb760d653aa96270fd",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 10,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:bc94786dc0e299dcb99b45aaa73cfc14ba04a7857e4db2e1a7d5b793992052d6",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:skill.invoke.invoke",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0c76296ecf1202dd48b56d2cbfb2491a2831008c1cb2e8157ec005a87cda4a24",'
    '      "section_key": "api.service_protocol.endpoint_invoker:skill.invoke.invoke",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:90eda799804023f1a84b99819eb58a1befd5a17d2234a6b4ba487883db3b450e",'
    '      "section_key": "api.service_protocol.endpoint_binding:skill.invoke.invoke",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:508bed65151106356af0ae6baf1b76f5ede0cad976813869b5c14d03af85723e",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:7feb097c339e4739079aee062e8b447f2bc171321ca3fd5e097252f4267cd1e5",'
    '      "section_key": "api.service_protocol.capability_protocol:skill.invoke",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:8b3bfaf05b53f200186e389396600452a85c906a6f14c6e7ccf4f99e5dd312bb",'
    '      "section_key": "api.service_protocol.api_protocol:skill",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:f8171a157e36d181f00569bf1c8bf723a7ca27c2bc25a3c457d38d1d06a054de",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:9527f1373ac3264876076f053063f23f7fe490892d7ef720a5b8a4cb5da9076d",'
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
    "AwareSkillServiceProtocol",
    "SkillApiServiceProtocol",
    "SkillInvokeCapabilityServiceProtocol",
    "SKILL__INVOKE__INVOKE_ENDPOINT_REF",
    "SKILL__INVOKE__INVOKE_PROTOCOL_BINDING",
    "invoke_skill__invoke__invoke",
]
