# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_node_service_dto.node.host import (
    DescribeHostedRuntimesRequest,
    DescribeHostedRuntimesResponse,
    DescribeHostedServiceRuntimesRequest,
    DescribeHostedServiceRuntimesResponse,
    DiscoverApiRoutesRequest,
    DiscoverApiRoutesResponse,
    DiscoverEnvironmentConfigsRequest,
    DiscoverEnvironmentConfigsResponse,
    GetBootEnvironmentDescriptorRequest,
    GetBootEnvironmentDescriptorResponse,
    GetEnvironmentStatusRequest,
    GetEnvironmentStatusResponse,
    ProvisionEnvironmentRequest,
    ProvisionEnvironmentResponse,
    RestartHostedRuntimeRequest,
    RestartHostedRuntimeResponse,
)

API_PACKAGE_NAME: Final[str] = "node-service-api"
API_FQN_PREFIX: Final[str] = "aware_node_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_node_service_api"


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


async def invoke_node__host__describe_hosted_runtimes(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeHostedRuntimesResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = DescribeHostedRuntimesRequest.model_validate(request)
    return await typed_handler.node.host.describe_hosted_runtimes(typed_request)


NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF: Final[str] = "node.host.describe_hosted_runtimes"
NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="describe_hosted_runtimes",
        request_type_ref="aware_node_service_dto.comms.models.DescribeHostedRuntimesRequest",
        response_type_ref="aware_node_service_dto.comms.models.DescribeHostedRuntimesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__describe_hosted_runtimes,
    )
)


async def invoke_node__host__describe_hosted_service_runtimes(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeHostedServiceRuntimesResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = DescribeHostedServiceRuntimesRequest.model_validate(request)
    return await typed_handler.node.host.describe_hosted_service_runtimes(typed_request)


NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF: Final[str] = "node.host.describe_hosted_service_runtimes"
NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="describe_hosted_service_runtimes",
        request_type_ref="aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesRequest",
        response_type_ref="aware_node_service_dto.comms.models.DescribeHostedServiceRuntimesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__describe_hosted_service_runtimes,
    )
)


async def invoke_node__host__discover_environment_configs(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DiscoverEnvironmentConfigsResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = DiscoverEnvironmentConfigsRequest.model_validate(request)
    return await typed_handler.node.host.discover_environment_configs(typed_request)


NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF: Final[str] = "node.host.discover_environment_configs"
NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="discover_environment_configs",
        request_type_ref="aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsRequest",
        response_type_ref="aware_node_service_dto.comms.models.DiscoverEnvironmentConfigsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__discover_environment_configs,
    )
)


async def invoke_node__host__discover_service_api_dependency_routes(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DiscoverApiRoutesResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = DiscoverApiRoutesRequest.model_validate(request)
    return await typed_handler.node.host.discover_service_api_dependency_routes(typed_request)


NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: Final[str] = (
    "node.host.discover_service_api_dependency_routes"
)
NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="discover_service_api_dependency_routes",
        request_type_ref="aware_node_service_dto.comms.models.DiscoverApiRoutesRequest",
        response_type_ref="aware_node_service_dto.comms.models.DiscoverApiRoutesResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__discover_service_api_dependency_routes,
    )
)


async def invoke_node__host__get_boot_environment_descriptor(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetBootEnvironmentDescriptorResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = GetBootEnvironmentDescriptorRequest.model_validate(request)
    return await typed_handler.node.host.get_boot_environment_descriptor(typed_request)


NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF: Final[str] = "node.host.get_boot_environment_descriptor"
NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="get_boot_environment_descriptor",
        request_type_ref="aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorRequest",
        response_type_ref="aware_node_service_dto.comms.models.GetBootEnvironmentDescriptorResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__get_boot_environment_descriptor,
    )
)


async def invoke_node__host__get_environment_status(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetEnvironmentStatusResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = GetEnvironmentStatusRequest.model_validate(request)
    return await typed_handler.node.host.get_environment_status(typed_request)


NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF: Final[str] = "node.host.get_environment_status"
NODE__HOST__GET_ENVIRONMENT_STATUS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="get_environment_status",
        request_type_ref="aware_node_service_dto.comms.models.GetEnvironmentStatusRequest",
        response_type_ref="aware_node_service_dto.comms.models.GetEnvironmentStatusResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__get_environment_status,
    )
)


async def invoke_node__host__provision_environment(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ProvisionEnvironmentResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = ProvisionEnvironmentRequest.model_validate(request)
    return await typed_handler.node.host.provision_environment(typed_request)


NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF: Final[str] = "node.host.provision_environment"
NODE__HOST__PROVISION_ENVIRONMENT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="provision_environment",
        request_type_ref="aware_node_service_dto.comms.models.ProvisionEnvironmentRequest",
        response_type_ref="aware_node_service_dto.comms.models.ProvisionEnvironmentResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__provision_environment,
    )
)


async def invoke_node__host__restart_hosted_runtime(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RestartHostedRuntimeResponse:
    typed_handler = cast(AwareNodeServiceProtocol, handler)
    typed_request = RestartHostedRuntimeRequest.model_validate(request)
    return await typed_handler.node.host.restart_hosted_runtime(typed_request)


NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF: Final[str] = "node.host.restart_hosted_runtime"
NODE__HOST__RESTART_HOSTED_RUNTIME_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF,
        api_name="node",
        capability_name="host",
        endpoint_name="restart_hosted_runtime",
        request_type_ref="aware_node_service_dto.comms.models.RestartHostedRuntimeRequest",
        response_type_ref="aware_node_service_dto.comms.models.RestartHostedRuntimeResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_node__host__restart_hosted_runtime,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF: NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_PROTOCOL_BINDING,
    NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF: NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_PROTOCOL_BINDING,
    NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF: NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_PROTOCOL_BINDING,
    NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING,
    NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF: NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_PROTOCOL_BINDING,
    NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF: NODE__HOST__GET_ENVIRONMENT_STATUS_PROTOCOL_BINDING,
    NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF: NODE__HOST__PROVISION_ENVIRONMENT_PROTOCOL_BINDING,
    NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF: NODE__HOST__RESTART_HOSTED_RUNTIME_PROTOCOL_BINDING,
}


class NodeHostCapabilityServiceProtocol(Protocol):

    async def describe_hosted_runtimes(
        self, request: DescribeHostedRuntimesRequest
    ) -> DescribeHostedRuntimesResponse: ...

    async def describe_hosted_service_runtimes(
        self, request: DescribeHostedServiceRuntimesRequest
    ) -> DescribeHostedServiceRuntimesResponse: ...

    async def discover_environment_configs(
        self, request: DiscoverEnvironmentConfigsRequest
    ) -> DiscoverEnvironmentConfigsResponse: ...

    async def discover_service_api_dependency_routes(
        self, request: DiscoverApiRoutesRequest
    ) -> DiscoverApiRoutesResponse: ...

    async def get_boot_environment_descriptor(
        self, request: GetBootEnvironmentDescriptorRequest
    ) -> GetBootEnvironmentDescriptorResponse: ...

    async def get_environment_status(self, request: GetEnvironmentStatusRequest) -> GetEnvironmentStatusResponse: ...

    async def provision_environment(self, request: ProvisionEnvironmentRequest) -> ProvisionEnvironmentResponse: ...

    async def restart_hosted_runtime(self, request: RestartHostedRuntimeRequest) -> RestartHostedRuntimeResponse: ...


class NodeApiServiceProtocol(Protocol):
    host: NodeHostCapabilityServiceProtocol


class AwareNodeServiceProtocol(Protocol):
    node: NodeApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:c8126ed8c287db8173db37ad2ecbc785158682001fba5a984d7986822060bbc0",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 31,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:aa342cf8cc51d92a94857782525a4f4051a039f3cdecf07c53272033612c178f",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.describe_hosted_runtimes",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.describe_hosted_service_runtimes",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.discover_environment_configs",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.discover_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.get_boot_environment_descriptor",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.get_environment_status",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.provision_environment",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:node.host.restart_hosted_runtime",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:641c6e189f6ae4ce2eb35e2a9923893d2c2c662c487cddb5d1ea040a486dd243",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.describe_hosted_runtimes",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:3e56c8f69ebad92aa14743650ddef449217422982589411f27e9746b1c285ae2",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.describe_hosted_runtimes",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2916df3de0797e8863e9e79fa0cc876376940cf33988f4cd59809c802c3e279d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.describe_hosted_service_runtimes",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:80c20a7b0b367425544af2d69371c37e2137122c3fb280b68679d5442628c05a",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.describe_hosted_service_runtimes",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:779308aef241ece3c0ba74cb3012af1fa0c264dacdc54907e92a6d907f4617fd",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.discover_environment_configs",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:89e6af1257007ca07fa4d5d654da811533efc931aa0c80ce446ba8055ce94a43",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.discover_environment_configs",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:fbdbed78cae9db7015a9d5e35aec612eac85fccbccdea5312a638400a06a3ef1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.discover_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:418db1d521dcdfef73f7c0f348ffd5cb8fd4ad5e61b003154f522e237d8270ee",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.discover_service_api_dependency_routes",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d49ddf66d4e507c995d3e04b678e0881e7fa153d238e15bb2cee90866a3b340d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.get_boot_environment_descriptor",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:70f56ca06df80b5ffd650d704b8c908587640759e12fc38678dffd713ad26c70",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.get_boot_environment_descriptor",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:75a5cf72c4ff0f62e7684edde91f67a5a8b40eb2f20866be6df66e590899c385",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.get_environment_status",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6cbe9386c584aa28b497e4fd83e1bc9f648ff8823c76166a150a834ffe9d2d01",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.get_environment_status",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:73ec50fdd28c88b7d2088627a1827cf20b4e3d559340f6a8015f99eb12108502",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.provision_environment",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2ad020542982a771fdb5be1d3b4911236cca79753ea334da4216e4c2652c58ad",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.provision_environment",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f542bcb2441f9463c66d28c5fc6ad57963467a10af330f814c347c2aa7dfa057",'
    '      "section_key": "api.service_protocol.endpoint_invoker:node.host.restart_hosted_runtime",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:eca661cede54a277a3443d3324ee241bcefcbfb88eebe4deeba4e8b3f9790d02",'
    '      "section_key": "api.service_protocol.endpoint_binding:node.host.restart_hosted_runtime",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 11,'
    '      "rendered_text_digest": "sha256:aeb56d6dc4caf45f5edc10ca59423a8151b5bfd3f144b42d6c2939d0702e4150",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c3ccc9ce39b78e0a5cdb8fd9ca04dc0cf3a49685c56eeedc80dab27da5d7eded",'
    '      "section_key": "api.service_protocol.capability_protocol:node.host",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:660c6005d259c66339b981987c7f8d42133d6c29eb546c70c6d626af9d1179fe",'
    '      "section_key": "api.service_protocol.api_protocol:node",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:9000713dad7fe936d9d646dd1537ef23bd6eb8b5341ebec486d2035b48e7036c",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 41,'
    '      "rendered_text_digest": "sha256:a566aea3b70857243b1e316b3c6f7ec713559727e899a4b46c6789b0027eb2de",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 30'
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
    "AwareNodeServiceProtocol",
    "NodeApiServiceProtocol",
    "NodeHostCapabilityServiceProtocol",
    "NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_ENDPOINT_REF",
    "NODE__HOST__DESCRIBE_HOSTED_RUNTIMES_PROTOCOL_BINDING",
    "invoke_node__host__describe_hosted_runtimes",
    "NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_ENDPOINT_REF",
    "NODE__HOST__DESCRIBE_HOSTED_SERVICE_RUNTIMES_PROTOCOL_BINDING",
    "invoke_node__host__describe_hosted_service_runtimes",
    "NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_ENDPOINT_REF",
    "NODE__HOST__DISCOVER_ENVIRONMENT_CONFIGS_PROTOCOL_BINDING",
    "invoke_node__host__discover_environment_configs",
    "NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF",
    "NODE__HOST__DISCOVER_SERVICE_API_DEPENDENCY_ROUTES_PROTOCOL_BINDING",
    "invoke_node__host__discover_service_api_dependency_routes",
    "NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_ENDPOINT_REF",
    "NODE__HOST__GET_BOOT_ENVIRONMENT_DESCRIPTOR_PROTOCOL_BINDING",
    "invoke_node__host__get_boot_environment_descriptor",
    "NODE__HOST__GET_ENVIRONMENT_STATUS_ENDPOINT_REF",
    "NODE__HOST__GET_ENVIRONMENT_STATUS_PROTOCOL_BINDING",
    "invoke_node__host__get_environment_status",
    "NODE__HOST__PROVISION_ENVIRONMENT_ENDPOINT_REF",
    "NODE__HOST__PROVISION_ENVIRONMENT_PROTOCOL_BINDING",
    "invoke_node__host__provision_environment",
    "NODE__HOST__RESTART_HOSTED_RUNTIME_ENDPOINT_REF",
    "NODE__HOST__RESTART_HOSTED_RUNTIME_PROTOCOL_BINDING",
    "invoke_node__host__restart_hosted_runtime",
]
