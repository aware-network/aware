# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "reactivity-service-api"
API_FQN_PREFIX: Final[str] = "aware_reactivity_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Publish ontology-backed action "
                                "lifecycle evidence from an action\n"
                                "            service back to Reactivity "
                                "without making Reactivity the "
                                "executor.",
                                "discriminant": "reactivity.action.publish_lifecycle",
                                "name": "publish_lifecycle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "description": "Resolve actor-subscription-backed "
                                "action intents for one matched\n"
                                "            Reactivity policy event "
                                "without fulfilling the actions.",
                                "discriminant": "reactivity.action.resolve_intents",
                                "name": "resolve_intents",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "description": "Subscribe to Reactivity-owned action " "execution lifecycle events.",
                                "discriminant": "reactivity.action.subscribe_lifecycle",
                                "name": "subscribe_lifecycle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                                "stream": {
                                    "description": "Action lifecycle events "
                                    "emitted by the Reactivity "
                                    "dispatch authority.",
                                    "events": [
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActionTerminal",
                                            "kind": "complete",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity.action.ActionFeedback",
                                            "kind": "delta",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntent",
                                            "kind": "notice",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActionExecution",
                                            "kind": "snapshot",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                    ],
                                    "source_path": "bindings/reactivity.apis.aware",
                                    "stream_mode": "server",
                                },
                            },
                        ],
                        "name": "action",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Subscribe to Reactivity-owned semantic " "bridge events.",
                                "discriminant": "reactivity.event.subscribe_events",
                                "name": "subscribe_events",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                                "stream": {
                                    "description": "Reactivity events emitted "
                                    "after Meta/environment "
                                    "fanout input is evaluated.",
                                    "events": [
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActorReactivityBridgeEvent",
                                            "kind": "delta",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/reactivity.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "event",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Register or verify a deterministic " "Reactivity policy bundle.",
                                "discriminant": "reactivity.policy.ensure_bundle",
                                "name": "ensure_bundle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "description": "List Reactivity policy bundles known " "to this service instance.",
                                "discriminant": "reactivity.policy.list_bundles",
                                "name": "list_bundles",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                        ],
                        "name": "policy",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read Reactivity service runtime status " "without graph-store access.",
                                "discriminant": "reactivity.status.get_status",
                                "name": "get_status",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityServiceStatusRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityServiceStatusResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            }
                        ],
                        "name": "status",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                ],
                "name": "reactivity",
                "source_path": "bindings/reactivity.apis.aware",
            }
        ],
        "fqn_prefix": "aware_reactivity_service_api",
        "package_name": "reactivity-service-api",
        "schema_version": 1,
    }
)

API_INVOCATION_MANIFEST: Final[LoadedApiInvocationManifest] = load_api_invocation_manifest_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Publish ontology-backed action "
                                "lifecycle evidence from an action\n"
                                "            service back to Reactivity "
                                "without making Reactivity the "
                                "executor.",
                                "discriminant": "reactivity.action.publish_lifecycle",
                                "endpoint_ref": "reactivity.action.publish_lifecycle",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "publish_lifecycle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityActionLifecyclePublishRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecyclePublishResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityActionLifecyclePublishResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve actor-subscription-backed "
                                "action intents for one matched\n"
                                "            Reactivity policy event "
                                "without fulfilling the actions.",
                                "discriminant": "reactivity.action.resolve_intents",
                                "endpoint_ref": "reactivity.action.resolve_intents",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_intents",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.action_intent.ReactivityActionIntentResolveRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntentResolveResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.action_intent.ReactivityActionIntentResolveResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Subscribe to Reactivity-owned action " "execution lifecycle events.",
                                "discriminant": "reactivity.action.subscribe_lifecycle",
                                "endpoint_ref": "reactivity.action.subscribe_lifecycle",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "subscribe_lifecycle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityActionLifecycleSubscriptionRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionLifecycleSubscriptionResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityActionLifecycleSubscriptionResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                                "stream": {
                                    "description": "Action lifecycle events "
                                    "emitted by the Reactivity "
                                    "dispatch authority.",
                                    "events": [
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActionTerminal",
                                            "kind": "complete",
                                            "python_model_ref": "aware_reactivity_service_dto.reactivity.action_terminal.ActionTerminal",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity.action.ActionFeedback",
                                            "kind": "delta",
                                            "python_model_ref": "aware_reactivity_ontology.action.action_feedback.ActionFeedback",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityActionIntent",
                                            "kind": "notice",
                                            "python_model_ref": "aware_reactivity_service_dto.reactivity.action_intent.ReactivityActionIntent",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActionExecution",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_reactivity_service_dto.reactivity.action_execution.ActionExecution",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        },
                                    ],
                                    "source_path": "bindings/reactivity.apis.aware",
                                    "stream_mode": "server",
                                },
                            },
                        ],
                        "name": "action",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Subscribe to Reactivity-owned semantic " "bridge events.",
                                "discriminant": "reactivity.event.subscribe_events",
                                "endpoint_ref": "reactivity.event.subscribe_events",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "subscribe_events",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityEventSubscriptionRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityEventSubscriptionResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityEventSubscriptionResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                                "stream": {
                                    "description": "Reactivity events emitted "
                                    "after Meta/environment "
                                    "fanout input is evaluated.",
                                    "events": [
                                        {
                                            "class_ref": "aware_reactivity_service_dto.reactivity.ActorReactivityBridgeEvent",
                                            "kind": "delta",
                                            "python_model_ref": "aware_reactivity_service_dto.reactivity.bridge_event.ActorReactivityBridgeEvent",
                                            "source_path": "bindings/reactivity.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/reactivity.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "event",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Register or verify a deterministic " "Reactivity policy bundle.",
                                "discriminant": "reactivity.policy.ensure_bundle",
                                "endpoint_ref": "reactivity.policy.ensure_bundle",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_bundle",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.policy_bundle.ReactivityPolicyBundleEnsureRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleEnsureResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.policy_bundle.ReactivityPolicyBundleEnsureResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List Reactivity policy bundles known " "to this service instance.",
                                "discriminant": "reactivity.policy.list_bundles",
                                "endpoint_ref": "reactivity.policy.list_bundles",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_bundles",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.policy_bundle.ReactivityPolicyBundleListRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityPolicyBundleListResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.policy_bundle.ReactivityPolicyBundleListResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            },
                        ],
                        "name": "policy",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read Reactivity service runtime status " "without graph-store access.",
                                "discriminant": "reactivity.status.get_status",
                                "endpoint_ref": "reactivity.status.get_status",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_status",
                                "request": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityServiceStatusRequest",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityServiceStatusRequest",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_reactivity_service_dto.reactivity.ReactivityServiceStatusResponse",
                                    "python_model_ref": "aware_reactivity_service_dto.reactivity.service_operation.ReactivityServiceStatusResponse",
                                    "source_path": "bindings/reactivity.apis.aware",
                                },
                                "source_path": "bindings/reactivity.apis.aware",
                            }
                        ],
                        "name": "status",
                        "source_path": "bindings/reactivity.apis.aware",
                    },
                ],
                "name": "reactivity",
                "source_path": "bindings/reactivity.apis.aware",
            }
        ],
        "fqn_prefix": "aware_reactivity_service_api",
        "package_name": "reactivity-service-api",
        "schema_version": 1,
    }
)

REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF: Final[str] = "reactivity.action.publish_lifecycle"
REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF: Final[str] = "reactivity.action.resolve_intents"
REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF: Final[str] = "reactivity.action.subscribe_lifecycle"
REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF: Final[str] = "reactivity.event.subscribe_events"
REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF: Final[str] = "reactivity.policy.ensure_bundle"
REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF: Final[str] = "reactivity.policy.list_bundles"
REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF: Final[str] = "reactivity.status.get_status"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "reactivity.action.publish_lifecycle": REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF,
    "reactivity.action.resolve_intents": REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF,
    "reactivity.action.subscribe_lifecycle": REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF,
    "reactivity.event.subscribe_events": REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF,
    "reactivity.policy.ensure_bundle": REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF,
    "reactivity.policy.list_bundles": REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF,
    "reactivity.status.get_status": REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF",
    "REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF",
    "REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF",
    "REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF",
    "REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF",
    "REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF",
    "REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF",
]
