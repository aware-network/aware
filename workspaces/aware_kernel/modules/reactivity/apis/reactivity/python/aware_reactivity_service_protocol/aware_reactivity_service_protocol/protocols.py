# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
from aware_reactivity_service_dto.reactivity.action_feedback import ActionFeedback
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
from aware_reactivity_service_dto.reactivity.bridge_event import ActorReactivityBridgeEvent
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
    ReactivityPolicyBundleEnsureResponse,
    ReactivityPolicyBundleListRequest,
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
    ReactivityActionLifecyclePublishResponse,
    ReactivityActionLifecycleSubscriptionRequest,
    ReactivityActionLifecycleSubscriptionResponse,
    ReactivityEventSubscriptionRequest,
    ReactivityEventSubscriptionResponse,
    ReactivityServiceStatusRequest,
    ReactivityServiceStatusResponse,
)

API_PACKAGE_NAME: Final[str] = "reactivity-service-api"
API_FQN_PREFIX: Final[str] = "aware_reactivity_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_reactivity_service_api"


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


async def invoke_reactivity__action__publish_lifecycle(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityActionLifecyclePublishResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityActionLifecyclePublishRequest.model_validate(request)
    return await typed_handler.reactivity.action.publish_lifecycle(typed_request)


REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF: Final[str] = "reactivity.action.publish_lifecycle"
REACTIVITY__ACTION__PUBLISH_LIFECYCLE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="action",
        endpoint_name="publish_lifecycle",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__action__publish_lifecycle,
    )
)


async def invoke_reactivity__action__resolve_intents(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityActionIntentResolveResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityActionIntentResolveRequest.model_validate(request)
    return await typed_handler.reactivity.action.resolve_intents(typed_request)


REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF: Final[str] = "reactivity.action.resolve_intents"
REACTIVITY__ACTION__RESOLVE_INTENTS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="action",
        endpoint_name="resolve_intents",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__action__resolve_intents,
    )
)

ReactivityActionSubscribeLifecycleStreamEvent: TypeAlias = (
    ActionTerminal | ActionFeedback | ReactivityActionIntent | ActionExecution
)


async def invoke_reactivity__action__subscribe_lifecycle(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityActionLifecycleSubscriptionResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityActionLifecycleSubscriptionRequest.model_validate(request)
    return await typed_handler.reactivity.action.subscribe_lifecycle(typed_request)


def stream_invoke_reactivity__action__subscribe_lifecycle(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityActionLifecycleSubscriptionRequest.model_validate(request)
    _ = execution
    return typed_handler.reactivity.action.stream_subscribe_lifecycle(typed_request)


REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF: Final[str] = "reactivity.action.subscribe_lifecycle"
REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="action",
        endpoint_name="subscribe_lifecycle",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionResponse",
        stream_event_type_refs=(
            "aware_reactivity_service_dto.reactivity.ActionTerminal",
            "aware_reactivity_service_dto.reactivity.ActionFeedback",
            "aware_reactivity_service_dto.reactivity.ReactivityActionIntent",
            "aware_reactivity_service_dto.reactivity.ActionExecution",
        ),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=stream_invoke_reactivity__action__subscribe_lifecycle,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__action__subscribe_lifecycle,
    )
)

ReactivityEventSubscribeEventsStreamEvent: TypeAlias = ActorReactivityBridgeEvent


async def invoke_reactivity__event__subscribe_events(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityEventSubscriptionResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityEventSubscriptionRequest.model_validate(request)
    return await typed_handler.reactivity.event.subscribe_events(typed_request)


def stream_invoke_reactivity__event__subscribe_events(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityEventSubscriptionRequest.model_validate(request)
    _ = execution
    return typed_handler.reactivity.event.stream_subscribe_events(typed_request)


REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF: Final[str] = "reactivity.event.subscribe_events"
REACTIVITY__EVENT__SUBSCRIBE_EVENTS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="event",
        endpoint_name="subscribe_events",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionResponse",
        stream_event_type_refs=("aware_reactivity_service_dto.reactivity.ActorReactivityBridgeEvent",),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=stream_invoke_reactivity__event__subscribe_events,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__event__subscribe_events,
    )
)


async def invoke_reactivity__policy__ensure_bundle(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityPolicyBundleEnsureResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityPolicyBundleEnsureRequest.model_validate(request)
    return await typed_handler.reactivity.policy.ensure_bundle(typed_request)


REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF: Final[str] = "reactivity.policy.ensure_bundle"
REACTIVITY__POLICY__ENSURE_BUNDLE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="policy",
        endpoint_name="ensure_bundle",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__policy__ensure_bundle,
    )
)


async def invoke_reactivity__policy__list_bundles(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityPolicyBundleListResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityPolicyBundleListRequest.model_validate(request)
    return await typed_handler.reactivity.policy.list_bundles(typed_request)


REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF: Final[str] = "reactivity.policy.list_bundles"
REACTIVITY__POLICY__LIST_BUNDLES_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF,
        api_name="reactivity",
        capability_name="policy",
        endpoint_name="list_bundles",
        request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListRequest",
        response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_reactivity__policy__list_bundles,
    )
)


async def invoke_reactivity__status__get_status(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ReactivityServiceStatusResponse:
    typed_handler = cast(AwareReactivityServiceProtocol, handler)
    typed_request = ReactivityServiceStatusRequest.model_validate(request)
    return await typed_handler.reactivity.status.get_status(typed_request)


REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF: Final[str] = "reactivity.status.get_status"
REACTIVITY__STATUS__GET_STATUS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = ServiceProtocolEndpointBinding(
    endpoint_ref=REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF,
    api_name="reactivity",
    capability_name="status",
    endpoint_name="get_status",
    request_type_ref="aware_reactivity_service_dto.reactivity.ReactivityServiceStatusRequest",
    response_type_ref="aware_reactivity_service_dto.reactivity.ReactivityServiceStatusResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_reactivity__status__get_status,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF: REACTIVITY__ACTION__PUBLISH_LIFECYCLE_PROTOCOL_BINDING,
    REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF: REACTIVITY__ACTION__RESOLVE_INTENTS_PROTOCOL_BINDING,
    REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF: REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_PROTOCOL_BINDING,
    REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF: REACTIVITY__EVENT__SUBSCRIBE_EVENTS_PROTOCOL_BINDING,
    REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF: REACTIVITY__POLICY__ENSURE_BUNDLE_PROTOCOL_BINDING,
    REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF: REACTIVITY__POLICY__LIST_BUNDLES_PROTOCOL_BINDING,
    REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF: REACTIVITY__STATUS__GET_STATUS_PROTOCOL_BINDING,
}


class ReactivityActionCapabilityServiceProtocol(Protocol):

    async def publish_lifecycle(
        self, request: ReactivityActionLifecyclePublishRequest
    ) -> ReactivityActionLifecyclePublishResponse: ...

    async def resolve_intents(
        self, request: ReactivityActionIntentResolveRequest
    ) -> ReactivityActionIntentResolveResponse: ...

    async def subscribe_lifecycle(
        self, request: ReactivityActionLifecycleSubscriptionRequest
    ) -> ReactivityActionLifecycleSubscriptionResponse: ...

    def stream_subscribe_lifecycle(
        self, request: ReactivityActionLifecycleSubscriptionRequest
    ) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]: ...


class ReactivityEventCapabilityServiceProtocol(Protocol):

    async def subscribe_events(
        self, request: ReactivityEventSubscriptionRequest
    ) -> ReactivityEventSubscriptionResponse: ...

    def stream_subscribe_events(
        self, request: ReactivityEventSubscriptionRequest
    ) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]: ...


class ReactivityPolicyCapabilityServiceProtocol(Protocol):

    async def ensure_bundle(
        self, request: ReactivityPolicyBundleEnsureRequest
    ) -> ReactivityPolicyBundleEnsureResponse: ...

    async def list_bundles(self, request: ReactivityPolicyBundleListRequest) -> ReactivityPolicyBundleListResponse: ...


class ReactivityStatusCapabilityServiceProtocol(Protocol):

    async def get_status(self, request: ReactivityServiceStatusRequest) -> ReactivityServiceStatusResponse: ...


class ReactivityApiServiceProtocol(Protocol):
    action: ReactivityActionCapabilityServiceProtocol
    event: ReactivityEventCapabilityServiceProtocol
    policy: ReactivityPolicyCapabilityServiceProtocol
    status: ReactivityStatusCapabilityServiceProtocol


class AwareReactivityServiceProtocol(Protocol):
    reactivity: ReactivityApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:b7fd3cd954407c4c07f083e0e953be874bd46f64cc73623bf69bc211d723198d",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 31,'
    '  "sections": ['
    "    {"
    '      "line_count": 22,'
    '      "rendered_text_digest": "sha256:6f7eb579188a5a01eb5a82e61cfcbf4eb4d81ce11a65fa4c85e0711081967332",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.action.publish_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.action.resolve_intents",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.action.subscribe_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.event.subscribe_events",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.policy.ensure_bundle",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.policy.list_bundles",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:reactivity.status.get_status",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2ca9dede0a13d7f3167b3f71e9a2a1445b27a5131a98ad454cb18be45602f4dc",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.action.publish_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:483c1082e62e5315760af4159805a6afff6dc860dfaa75575636fd01a147f2e2",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.action.publish_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b54bddf465a692104288c9056d0516f5edf5dd16fdc057b02711893d6ddfe1d6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.action.resolve_intents",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:fe287a3b50169f2a4d276114c6d88ab4e649433e479470ba9ee42a5fda235b17",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.action.resolve_intents",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:a14ff2c7fe55d251763559b7ae4108e593d5fd8ea723f494f32559c979c73eb7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.action.subscribe_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 22,'
    '      "rendered_text_digest": "sha256:c8be7c0e0846abf1ca451c5493d576114814da9f735696fc6945a4a9a2d66d1f",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.action.subscribe_lifecycle",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:1455d62f636a994b496891833988900a62c689909cdfe1c2be160b18f5900489",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.event.subscribe_events",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:8e83507f8145ca0752ccce450d19e84b8d0b9fd392cb5febe5599fab45f64d55",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.event.subscribe_events",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:c4c5326b40a777509b8a9eb29d9f6cf5346c2e90a1f6c0cafb226345eafd2360",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.policy.ensure_bundle",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:3af41b84953c7633461e7811f2cb8b88d040770a9fa72ab7aab13027cdb83608",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.policy.ensure_bundle",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0f97cee823a479e8e89473f9178ae1268fd88be4f9cedaa1534d615ab5e5bc9f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.policy.list_bundles",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8eae7ccb03aea1a7d75d0a3369a02300f1a0727612e59a81a3e39f965e21d86b",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.policy.list_bundles",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e2d7d746578286da3490a3a9eee802f836292a7928f0dcd0d3c45a6f0bfad865",'
    '      "section_key": "api.service_protocol.endpoint_invoker:reactivity.status.get_status",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d1af87840ca315c7e878291be9984515707a73407966cfa41e328424d56e9348",'
    '      "section_key": "api.service_protocol.endpoint_binding:reactivity.status.get_status",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:c9352d14e968325883ca03a735d9625ea1216bf51062a6815d975e89412bfbcf",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:acf1d58c3c48f947e8cfdd1956c328b1048699d017b0c03a79c3c34a2fe05ce3",'
    '      "section_key": "api.service_protocol.capability_protocol:reactivity.action",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:848738d1e6ce4101fd2e4349978215f42c7cd0d867ba9c195725d21857c55d97",'
    '      "section_key": "api.service_protocol.capability_protocol:reactivity.event",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:411dbe8bd298be6d665a296009cf9ccb27edbe64df64db247efe20ad9552e35c",'
    '      "section_key": "api.service_protocol.capability_protocol:reactivity.policy",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:5c888ada4852b1c738a2393ffcc6d7f67c7f33e07337c98d29cabddbff1eea1f",'
    '      "section_key": "api.service_protocol.capability_protocol:reactivity.status",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:db74d9744b7cf9617996233af3180e37f189b5d0c84935413e3e8bc00e34ad64",'
    '      "section_key": "api.service_protocol.api_protocol:reactivity",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:ed4a5d7189f5858513449b569a3436799b76e4dad944963640c3b11058dafe2c",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 45,'
    '      "rendered_text_digest": "sha256:33c2371840ef2e61a210dde3ee5b29f4a0fe419beef7a50a0745a5548d3cb6b2",'
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
    "AwareReactivityServiceProtocol",
    "ReactivityApiServiceProtocol",
    "ReactivityActionCapabilityServiceProtocol",
    "ReactivityEventCapabilityServiceProtocol",
    "ReactivityPolicyCapabilityServiceProtocol",
    "ReactivityStatusCapabilityServiceProtocol",
    "ReactivityActionSubscribeLifecycleStreamEvent",
    "ReactivityEventSubscribeEventsStreamEvent",
    "REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF",
    "REACTIVITY__ACTION__PUBLISH_LIFECYCLE_PROTOCOL_BINDING",
    "invoke_reactivity__action__publish_lifecycle",
    "REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF",
    "REACTIVITY__ACTION__RESOLVE_INTENTS_PROTOCOL_BINDING",
    "invoke_reactivity__action__resolve_intents",
    "REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF",
    "REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_PROTOCOL_BINDING",
    "invoke_reactivity__action__subscribe_lifecycle",
    "stream_invoke_reactivity__action__subscribe_lifecycle",
    "REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF",
    "REACTIVITY__EVENT__SUBSCRIBE_EVENTS_PROTOCOL_BINDING",
    "invoke_reactivity__event__subscribe_events",
    "stream_invoke_reactivity__event__subscribe_events",
    "REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF",
    "REACTIVITY__POLICY__ENSURE_BUNDLE_PROTOCOL_BINDING",
    "invoke_reactivity__policy__ensure_bundle",
    "REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF",
    "REACTIVITY__POLICY__LIST_BUNDLES_PROTOCOL_BINDING",
    "invoke_reactivity__policy__list_bundles",
    "REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF",
    "REACTIVITY__STATUS__GET_STATUS_PROTOCOL_BINDING",
    "invoke_reactivity__status__get_status",
]
