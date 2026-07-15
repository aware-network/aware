# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_code_service_dto.code.features.package_distribution import (
    DescribeCodePackageRequest,
    DescribeCodePackageResponse,
    DiscoverCodePackageChannelHeadsRequest,
    DiscoverCodePackageChannelHeadsResponse,
    DownloadCodePackageRequest,
    DownloadCodePackageResponse,
    PublishCodePackageRequest,
    PublishCodePackageResponse,
    ResolveCodePackageRequest,
    ResolveCodePackageResponse,
    SearchCodePackageRequest,
    SearchCodePackageResponse,
)
from aware_hub_service_dto.hub.artifact_authority import (
    PublishHubArtifactRequest,
    PublishHubArtifactResponse,
    ResolveHubArtifactRequest,
    ResolveHubArtifactResponse,
)
from aware_hub_service_dto.hub.deployment_artifact_authority import (
    ResolveDeploymentArtifactRequest,
    ResolveDeploymentArtifactResponse,
)
from aware_hub_service_dto.hub.public_map_discovery import DiscoverPublicMapRequest, DiscoverPublicMapResponse

API_PACKAGE_NAME: Final[str] = "hub-service-api"
API_FQN_PREFIX: Final[str] = "aware_hub_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_hub_service_api"


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


async def invoke_hub__artifact__publish(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> PublishHubArtifactResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = PublishHubArtifactRequest.model_validate(request)
    return await typed_handler.hub.artifact.publish(typed_request)


HUB__ARTIFACT__PUBLISH_ENDPOINT_REF: Final[str] = "hub.artifact.publish"
HUB__ARTIFACT__PUBLISH_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__ARTIFACT__PUBLISH_ENDPOINT_REF,
    api_name="hub",
    capability_name="artifact",
    endpoint_name="publish",
    request_type_ref="aware_hub_service_dto.hub.PublishHubArtifactRequest",
    response_type_ref="aware_hub_service_dto.hub.PublishHubArtifactResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__artifact__publish,
)


async def invoke_hub__artifact__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveHubArtifactResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = ResolveHubArtifactRequest.model_validate(request)
    return await typed_handler.hub.artifact.resolve(typed_request)


HUB__ARTIFACT__RESOLVE_ENDPOINT_REF: Final[str] = "hub.artifact.resolve"
HUB__ARTIFACT__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__ARTIFACT__RESOLVE_ENDPOINT_REF,
    api_name="hub",
    capability_name="artifact",
    endpoint_name="resolve",
    request_type_ref="aware_hub_service_dto.hub.ResolveHubArtifactRequest",
    response_type_ref="aware_hub_service_dto.hub.ResolveHubArtifactResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__artifact__resolve,
)


async def invoke_hub__code_package__describe(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeCodePackageResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = DescribeCodePackageRequest.model_validate(request)
    return await typed_handler.hub.code_package.describe(typed_request)


HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF: Final[str] = "hub.code_package.describe"
HUB__CODE_PACKAGE__DESCRIBE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF,
    api_name="hub",
    capability_name="code_package",
    endpoint_name="describe",
    request_type_ref="aware_code_service_dto.code.DescribeCodePackageRequest",
    response_type_ref="aware_code_service_dto.code.DescribeCodePackageResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__code_package__describe,
)


async def invoke_hub__code_package__discover_channel_heads(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DiscoverCodePackageChannelHeadsResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = DiscoverCodePackageChannelHeadsRequest.model_validate(request)
    return await typed_handler.hub.code_package.discover_channel_heads(typed_request)


HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF: Final[str] = "hub.code_package.discover_channel_heads"
HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF,
        api_name="hub",
        capability_name="code_package",
        endpoint_name="discover_channel_heads",
        request_type_ref="aware_code_service_dto.code.DiscoverCodePackageChannelHeadsRequest",
        response_type_ref="aware_code_service_dto.code.DiscoverCodePackageChannelHeadsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_hub__code_package__discover_channel_heads,
    )
)


async def invoke_hub__code_package__download(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DownloadCodePackageResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = DownloadCodePackageRequest.model_validate(request)
    return await typed_handler.hub.code_package.download(typed_request)


HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF: Final[str] = "hub.code_package.download"
HUB__CODE_PACKAGE__DOWNLOAD_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF,
    api_name="hub",
    capability_name="code_package",
    endpoint_name="download",
    request_type_ref="aware_code_service_dto.code.DownloadCodePackageRequest",
    response_type_ref="aware_code_service_dto.code.DownloadCodePackageResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__code_package__download,
)


async def invoke_hub__code_package__publish(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> PublishCodePackageResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = PublishCodePackageRequest.model_validate(request)
    return await typed_handler.hub.code_package.publish(typed_request)


HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF: Final[str] = "hub.code_package.publish"
HUB__CODE_PACKAGE__PUBLISH_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF,
    api_name="hub",
    capability_name="code_package",
    endpoint_name="publish",
    request_type_ref="aware_code_service_dto.code.PublishCodePackageRequest",
    response_type_ref="aware_code_service_dto.code.PublishCodePackageResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__code_package__publish,
)


async def invoke_hub__code_package__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveCodePackageResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = ResolveCodePackageRequest.model_validate(request)
    return await typed_handler.hub.code_package.resolve(typed_request)


HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF: Final[str] = "hub.code_package.resolve"
HUB__CODE_PACKAGE__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF,
    api_name="hub",
    capability_name="code_package",
    endpoint_name="resolve",
    request_type_ref="aware_code_service_dto.code.ResolveCodePackageRequest",
    response_type_ref="aware_code_service_dto.code.ResolveCodePackageResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__code_package__resolve,
)


async def invoke_hub__code_package__search(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SearchCodePackageResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = SearchCodePackageRequest.model_validate(request)
    return await typed_handler.hub.code_package.search(typed_request)


HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF: Final[str] = "hub.code_package.search"
HUB__CODE_PACKAGE__SEARCH_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF,
    api_name="hub",
    capability_name="code_package",
    endpoint_name="search",
    request_type_ref="aware_code_service_dto.code.SearchCodePackageRequest",
    response_type_ref="aware_code_service_dto.code.SearchCodePackageResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__code_package__search,
)


async def invoke_hub__deployment_artifact__resolve(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveDeploymentArtifactResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = ResolveDeploymentArtifactRequest.model_validate(request)
    return await typed_handler.hub.deployment_artifact.resolve(typed_request)


HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF: Final[str] = "hub.deployment_artifact.resolve"
HUB__DEPLOYMENT_ARTIFACT__RESOLVE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF,
        api_name="hub",
        capability_name="deployment_artifact",
        endpoint_name="resolve",
        request_type_ref="aware_hub_service_dto.hub.ResolveDeploymentArtifactRequest",
        response_type_ref="aware_hub_service_dto.hub.ResolveDeploymentArtifactResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_hub__deployment_artifact__resolve,
    )
)


async def invoke_hub__public_map__discover(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DiscoverPublicMapResponse:
    typed_handler = cast(AwareHubServiceProtocol, handler)
    typed_request = DiscoverPublicMapRequest.model_validate(request)
    return await typed_handler.hub.public_map.discover(typed_request)


HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF: Final[str] = "hub.public_map.discover"
HUB__PUBLIC_MAP__DISCOVER_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF,
    api_name="hub",
    capability_name="public_map",
    endpoint_name="discover",
    request_type_ref="aware_hub_service_dto.hub.DiscoverPublicMapRequest",
    response_type_ref="aware_hub_service_dto.hub.DiscoverPublicMapResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_hub__public_map__discover,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    HUB__ARTIFACT__PUBLISH_ENDPOINT_REF: HUB__ARTIFACT__PUBLISH_PROTOCOL_BINDING,
    HUB__ARTIFACT__RESOLVE_ENDPOINT_REF: HUB__ARTIFACT__RESOLVE_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF: HUB__CODE_PACKAGE__DESCRIBE_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF: HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF: HUB__CODE_PACKAGE__DOWNLOAD_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF: HUB__CODE_PACKAGE__PUBLISH_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF: HUB__CODE_PACKAGE__RESOLVE_PROTOCOL_BINDING,
    HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF: HUB__CODE_PACKAGE__SEARCH_PROTOCOL_BINDING,
    HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF: HUB__DEPLOYMENT_ARTIFACT__RESOLVE_PROTOCOL_BINDING,
    HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF: HUB__PUBLIC_MAP__DISCOVER_PROTOCOL_BINDING,
}


class HubArtifactCapabilityServiceProtocol(Protocol):

    async def publish(self, request: PublishHubArtifactRequest) -> PublishHubArtifactResponse: ...

    async def resolve(self, request: ResolveHubArtifactRequest) -> ResolveHubArtifactResponse: ...


class HubCodePackageCapabilityServiceProtocol(Protocol):

    async def describe(self, request: DescribeCodePackageRequest) -> DescribeCodePackageResponse: ...

    async def discover_channel_heads(
        self, request: DiscoverCodePackageChannelHeadsRequest
    ) -> DiscoverCodePackageChannelHeadsResponse: ...

    async def download(self, request: DownloadCodePackageRequest) -> DownloadCodePackageResponse: ...

    async def publish(self, request: PublishCodePackageRequest) -> PublishCodePackageResponse: ...

    async def resolve(self, request: ResolveCodePackageRequest) -> ResolveCodePackageResponse: ...

    async def search(self, request: SearchCodePackageRequest) -> SearchCodePackageResponse: ...


class HubDeploymentArtifactCapabilityServiceProtocol(Protocol):

    async def resolve(self, request: ResolveDeploymentArtifactRequest) -> ResolveDeploymentArtifactResponse: ...


class HubPublicMapCapabilityServiceProtocol(Protocol):

    async def discover(self, request: DiscoverPublicMapRequest) -> DiscoverPublicMapResponse: ...


class HubApiServiceProtocol(Protocol):
    artifact: HubArtifactCapabilityServiceProtocol
    code_package: HubCodePackageCapabilityServiceProtocol
    deployment_artifact: HubDeploymentArtifactCapabilityServiceProtocol
    public_map: HubPublicMapCapabilityServiceProtocol


class AwareHubServiceProtocol(Protocol):
    hub: HubApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:04809e1ac7d629e39a3e7f7832711d876ef9b303d3d7eb0be724161ef3760b97",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 40,'
    '  "sections": ['
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:def52a173c60d8c1800fdd645e3d75b0719797350cd91f2b2f6b254cb8e164d9",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:hub.artifact.publish",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.describe",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.discover_channel_heads",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.download",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.publish",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.code_package.search",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.deployment_artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:hub.public_map.discover",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a41841ca6fa68449dee7e1a65e35f24f5d09af56f706f88bbd1caa2f766ee1e6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.artifact.publish",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0f361dbe8413403d27fc572c29345570966fb2b8f85706d1593a0a957bbe770e",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.artifact.publish",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:490b110aad7594fddbf1f722594cbeb590d4646faba6303ac1321dcb1aa00b76",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:cf6b1954b74188ce820a7d3a23ddc4b9c317160192ff9d1070ab5eef69f70948",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:8a49851b03d1c289a25501176ece2d95eb71328f5d5e22148cc5a7cc93066ee0",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.describe",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:f8089d33f1ad4d8911518d75bb1ab711bb4da1b5a87143b4779c472a75251f5b",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.describe",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:82ec28a7eed85f90fe52d9cd5badd3bd65c05682ccccb248ce1fd9e4b4661597",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.discover_channel_heads",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6e9b49bd5629e224b058e6877c802106a48f374164a84b498185b38ca6f1d18f",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.discover_channel_heads",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:075a24ed7b7a6b31890e5b4f6f9823606c5d1375b51e25d54a5b0bba7d4dbfc6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.download",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:76538814709aa2bfb49e3d4302742aaeb76f2c762b5598f4970993b09476cae5",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.download",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:584e70f74eb39f0be8b1e5f0775d0cc1d962f8cd06c6a265c82ddb583f0264c1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.publish",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0350d13bc81237922cc307487194b224755216388bc368c9934584c39a1e8008",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.publish",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:58a43dc88c5f3a2ea9a9d3ba60b18d0c58b44337d56fbd16edac04c41e494059",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8468f1af3a00dff7de098f0501eea5d8cfd7e8655c83e51eb2c859ab815b0b70",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0d525d45f307b4139d44f806ff7f030332bb1906384037a3ef7d4ec1aae880d4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.code_package.search",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0bd97fdec6ff8acf137ca02ee86c25d06022420cbf088a80ff06761256fca1c6",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.code_package.search",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9a6a5adc4cb09c9e354a7af0c005dd1b8420acf7c0e7a218dbae967b339ecb56",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.deployment_artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:77f85357940f4ef27d4f0a510200a4cb3f1c97293add90db3bec3d035bd49e16",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.deployment_artifact.resolve",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:cac40a90dd6c5044f42f8e49e2d1c420eca0aa4fde758d40ef6d5f15aa507bd1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:hub.public_map.discover",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:bb106005bb96cc5cd963a11d51114ff8c37d573b67a7ff5fd1f294eca20e02d6",'
    '      "section_key": "api.service_protocol.endpoint_binding:hub.public_map.discover",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 13,'
    '      "rendered_text_digest": "sha256:58283404ae96eb907d3663fd56d6fc32f78a266be4d3af979021cd21041f09b9",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:b419d7b2fd89ba7151b6e0d0c39f40ce0b6e6b5786736d66d9fb6c5da159b33a",'
    '      "section_key": "api.service_protocol.capability_protocol:hub.artifact",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 14,'
    '      "rendered_text_digest": "sha256:8c32ae3e68c1b44b486d2d79124e30e8129ee9909f2d9aba8980e4eea6c91f1a",'
    '      "section_key": "api.service_protocol.capability_protocol:hub.code_package",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:10aa66c6e39a107534a39f7d41722010cbc05d3acd94f84fb6a36c14d7f28979",'
    '      "section_key": "api.service_protocol.capability_protocol:hub.deployment_artifact",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6515f25bff3872e2f76fbeaa986b31356a744665908670ebcf528d6781eed203",'
    '      "section_key": "api.service_protocol.capability_protocol:hub.public_map",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:f51cfb18b247a53d0e1905b382cbcc8d00aefc6e26d62a9372ddd2aecffaa37d",'
    '      "section_key": "api.service_protocol.api_protocol:hub",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:559fe77cd2e4271b2eec1db2d253dd0df165abe42928e61c83f659597137585e",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 50,'
    '      "rendered_text_digest": "sha256:0cf0ddd00c6c06e7380588d4c04786c2ab93cdce7a09446f0758ff6cb265ac0d",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 39'
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
    "AwareHubServiceProtocol",
    "HubApiServiceProtocol",
    "HubArtifactCapabilityServiceProtocol",
    "HubCodePackageCapabilityServiceProtocol",
    "HubDeploymentArtifactCapabilityServiceProtocol",
    "HubPublicMapCapabilityServiceProtocol",
    "HUB__ARTIFACT__PUBLISH_ENDPOINT_REF",
    "HUB__ARTIFACT__PUBLISH_PROTOCOL_BINDING",
    "invoke_hub__artifact__publish",
    "HUB__ARTIFACT__RESOLVE_ENDPOINT_REF",
    "HUB__ARTIFACT__RESOLVE_PROTOCOL_BINDING",
    "invoke_hub__artifact__resolve",
    "HUB__CODE_PACKAGE__DESCRIBE_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DESCRIBE_PROTOCOL_BINDING",
    "invoke_hub__code_package__describe",
    "HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DISCOVER_CHANNEL_HEADS_PROTOCOL_BINDING",
    "invoke_hub__code_package__discover_channel_heads",
    "HUB__CODE_PACKAGE__DOWNLOAD_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__DOWNLOAD_PROTOCOL_BINDING",
    "invoke_hub__code_package__download",
    "HUB__CODE_PACKAGE__PUBLISH_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__PUBLISH_PROTOCOL_BINDING",
    "invoke_hub__code_package__publish",
    "HUB__CODE_PACKAGE__RESOLVE_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__RESOLVE_PROTOCOL_BINDING",
    "invoke_hub__code_package__resolve",
    "HUB__CODE_PACKAGE__SEARCH_ENDPOINT_REF",
    "HUB__CODE_PACKAGE__SEARCH_PROTOCOL_BINDING",
    "invoke_hub__code_package__search",
    "HUB__DEPLOYMENT_ARTIFACT__RESOLVE_ENDPOINT_REF",
    "HUB__DEPLOYMENT_ARTIFACT__RESOLVE_PROTOCOL_BINDING",
    "invoke_hub__deployment_artifact__resolve",
    "HUB__PUBLIC_MAP__DISCOVER_ENDPOINT_REF",
    "HUB__PUBLIC_MAP__DISCOVER_PROTOCOL_BINDING",
    "invoke_hub__public_map__discover",
]
