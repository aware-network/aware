# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_external_capital_provider_service_dto.external_capital.wallet_funding import (
    ExternalCapitalWalletFundingSessionRequest,
    ExternalCapitalWalletFundingSessionResponse,
)

API_PACKAGE_NAME: Final[str] = "external-capital-provider-service-api"
API_FQN_PREFIX: Final[str] = "aware_external_capital_provider_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_external_capital_provider_service_api"


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


async def invoke_external_capital__wallet_funding_session__create_wallet_funding_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ExternalCapitalWalletFundingSessionResponse:
    typed_handler = cast(AwareExternalCapitalProviderServiceProtocol, handler)
    typed_request = ExternalCapitalWalletFundingSessionRequest.model_validate(request)
    return await typed_handler.external_capital.wallet_funding_session.create_wallet_funding_session(typed_request)


EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF: Final[str] = (
    "external_capital.wallet_funding_session.create_wallet_funding_session"
)
EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF,
    api_name="external_capital",
    capability_name="wallet_funding_session",
    endpoint_name="create_wallet_funding_session",
    request_type_ref="aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionRequest",
    response_type_ref="aware_external_capital_provider_service_dto.external_capital.ExternalCapitalWalletFundingSessionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_external_capital__wallet_funding_session__create_wallet_funding_session,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF: EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_PROTOCOL_BINDING,
}


class ExternalCapitalWalletFundingSessionCapabilityServiceProtocol(Protocol):

    async def create_wallet_funding_session(
        self, request: ExternalCapitalWalletFundingSessionRequest
    ) -> ExternalCapitalWalletFundingSessionResponse: ...


class ExternalCapitalApiServiceProtocol(Protocol):
    wallet_funding_session: ExternalCapitalWalletFundingSessionCapabilityServiceProtocol


class AwareExternalCapitalProviderServiceProtocol(Protocol):
    external_capital: ExternalCapitalApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:fb5773e132a79b16b533ca0a4bce8b8eac083324255b867f8706ba110675f45d",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 10,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:bd4af3758d56194c646d82c913dc83f1f76e1851f96a68248192975487036d18",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:external_capital.wallet_funding_session.create_wallet_funding_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:71a6f47adf5cd4dd6968396c6b0a6502874ff8a383ccf89b5d810c720d7334e3",'
    '      "section_key": "api.service_protocol.endpoint_invoker:external_capital.wallet_funding_session.create_wallet_funding_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b98d10abd4c4178ed7af919094b573d2ddfd28168486b03f21053452f9022196",'
    '      "section_key": "api.service_protocol.endpoint_binding:external_capital.wallet_funding_session.create_wallet_funding_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:9f57ea0785be9704263e2481dcf80f3f27edd82898bdfb40451ff1e983c23419",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:a444e445f4605cade456f4d5c7c54d5395bc5ffe065997ec150007e6916c4a00",'
    '      "section_key": "api.service_protocol.capability_protocol:external_capital.wallet_funding_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:73b4c657e1afba7336505bf463697e1658972f0b070e1c2fc53c3eed5543db38",'
    '      "section_key": "api.service_protocol.api_protocol:external_capital",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:81b30f4573a69bf032e9dcc6254b32f5e8ddc5d4c5570dbe781d41e631550c87",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:10a190ac99c1f7ee5021b8da2cb101766763e0bd47fb1fbcf7fd8fefa63655a8",'
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
    "AwareExternalCapitalProviderServiceProtocol",
    "ExternalCapitalApiServiceProtocol",
    "ExternalCapitalWalletFundingSessionCapabilityServiceProtocol",
    "EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_ENDPOINT_REF",
    "EXTERNAL_CAPITAL__WALLET_FUNDING_SESSION__CREATE_WALLET_FUNDING_SESSION_PROTOCOL_BINDING",
    "invoke_external_capital__wallet_funding_session__create_wallet_funding_session",
]
