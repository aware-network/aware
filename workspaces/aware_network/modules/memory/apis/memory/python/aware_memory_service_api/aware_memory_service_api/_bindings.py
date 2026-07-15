# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "memory-service-api"
API_FQN_PREFIX: Final[str] = "aware_memory_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Read one MemoryWorking lane by id or " "actor/key coordinates.",
                                "discriminant": "memory.describe_memory_working.describe_memory_working",
                                "name": "describe_memory_working",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.DescribeMemoryWorkingRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.DescribeMemoryWorkingResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "describe_memory_working",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve or create one actor-scoped " "MemoryWorking lane.",
                                "discriminant": "memory.ensure_memory_working.ensure_memory_working",
                                "name": "ensure_memory_working",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.EnsureMemoryWorkingRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.EnsureMemoryWorkingResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "ensure_memory_working",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List ordered MemoryWorkingItem pins " "for one working-memory lane.",
                                "discriminant": "memory.list_memory_working_items.list_memory_working_items",
                                "name": "list_memory_working_items",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ListMemoryWorkingItemsRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ListMemoryWorkingItemsResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "list_memory_working_items",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Persist one provider-neutral resolved "
                                "meaning under a verified\n"
                                "            remembered event with "
                                "resolver terminal provenance.",
                                "discriminant": "memory.record_resolved_event_meaning.record_resolved_event_meaning",
                                "name": "record_resolved_event_meaning",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RecordResolvedEventMeaningRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RecordResolvedEventMeaningResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "record_resolved_event_meaning",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Validate and retain one "
                                "AttentionFocusTransition pointer in "
                                "working memory.",
                                "discriminant": "memory.remember_attention_transition.remember_attention_transition",
                                "name": "remember_attention_transition",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberAttentionTransitionRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberAttentionTransitionResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_attention_transition",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Retain one Content pointer in working " "memory.",
                                "discriminant": "memory.remember_content.remember_content",
                                "name": "remember_content",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberContentRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberContentResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_content",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Retain one Reactivity Event pointer in " "working memory.",
                                "discriminant": "memory.remember_event.remember_event",
                                "name": "remember_event",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberEventRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberEventResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_event",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Validate actor/session context through "
                                "Identity, then resolve usable Memory "
                                "evidence.",
                                "discriminant": "memory.resolve_actor_memory_context.resolve_actor_memory_context",
                                "name": "resolve_actor_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve actor-scoped Memory context " "into a compact consumer frame.",
                                "discriminant": "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",
                                "name": "resolve_actor_memory_context_frame",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_memory_context_frame",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve one actor working-memory lane "
                                "into evidence-labeled context.",
                                "discriminant": "memory.resolve_memory_context.resolve_memory_context",
                                "name": "resolve_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Validate one retained "
                                "MemoryWorkingItem and return source "
                                "evidence.",
                                "discriminant": "memory.validate_memory_working_item.validate_memory_working_item",
                                "name": "validate_memory_working_item",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "validate_memory_working_item",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read and stream actor-scoped Memory " "context snapshots.",
                                "discriminant": "memory.watch_actor_memory_context.watch_actor_memory_context",
                                "name": "watch_actor_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed Memory " "actor-context snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_memory_service_dto.memory.working.MemoryActorContextEvent",
                                            "kind": "snapshot",
                                            "source_path": "bindings/memory.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/memory.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_actor_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read and stream actor-scoped Memory " "consumer frames.",
                                "discriminant": "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",
                                "name": "watch_actor_memory_context_frame",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed Memory " "actor-context consumer " "frames.",
                                    "events": [
                                        {
                                            "class_ref": "aware_memory_service_dto.memory.working.MemoryActorContextFrameEvent",
                                            "kind": "snapshot",
                                            "source_path": "bindings/memory.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/memory.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_actor_memory_context_frame",
                        "source_path": "bindings/memory.apis.aware",
                    },
                ],
                "name": "memory",
                "source_path": "bindings/memory.apis.aware",
            }
        ],
        "fqn_prefix": "aware_memory_service_api",
        "package_name": "memory-service-api",
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
                                "description": "Read one MemoryWorking lane by id or " "actor/key coordinates.",
                                "discriminant": "memory.describe_memory_working.describe_memory_working",
                                "endpoint_ref": "memory.describe_memory_working.describe_memory_working",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_memory_working",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.DescribeMemoryWorkingRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.DescribeMemoryWorkingRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.DescribeMemoryWorkingResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.DescribeMemoryWorkingResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "describe_memory_working",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve or create one actor-scoped " "MemoryWorking lane.",
                                "discriminant": "memory.ensure_memory_working.ensure_memory_working",
                                "endpoint_ref": "memory.ensure_memory_working.ensure_memory_working",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_memory_working",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.EnsureMemoryWorkingRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.EnsureMemoryWorkingRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.EnsureMemoryWorkingResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.EnsureMemoryWorkingResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "ensure_memory_working",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List ordered MemoryWorkingItem pins " "for one working-memory lane.",
                                "discriminant": "memory.list_memory_working_items.list_memory_working_items",
                                "endpoint_ref": "memory.list_memory_working_items.list_memory_working_items",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_memory_working_items",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ListMemoryWorkingItemsRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ListMemoryWorkingItemsRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ListMemoryWorkingItemsResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ListMemoryWorkingItemsResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "list_memory_working_items",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Persist one provider-neutral resolved "
                                "meaning under a verified\n"
                                "            remembered event with "
                                "resolver terminal provenance.",
                                "discriminant": "memory.record_resolved_event_meaning.record_resolved_event_meaning",
                                "endpoint_ref": "memory.record_resolved_event_meaning.record_resolved_event_meaning",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "record_resolved_event_meaning",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RecordResolvedEventMeaningRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RecordResolvedEventMeaningRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RecordResolvedEventMeaningResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RecordResolvedEventMeaningResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "record_resolved_event_meaning",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate and retain one "
                                "AttentionFocusTransition pointer in "
                                "working memory.",
                                "discriminant": "memory.remember_attention_transition.remember_attention_transition",
                                "endpoint_ref": "memory.remember_attention_transition.remember_attention_transition",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "remember_attention_transition",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberAttentionTransitionRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberAttentionTransitionRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberAttentionTransitionResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberAttentionTransitionResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_attention_transition",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Retain one Content pointer in working " "memory.",
                                "discriminant": "memory.remember_content.remember_content",
                                "endpoint_ref": "memory.remember_content.remember_content",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "remember_content",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberContentRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberContentRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberContentResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberContentResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_content",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Retain one Reactivity Event pointer in " "working memory.",
                                "discriminant": "memory.remember_event.remember_event",
                                "endpoint_ref": "memory.remember_event.remember_event",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "remember_event",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberEventRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberEventRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.RememberEventResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.RememberEventResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "remember_event",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate actor/session context through "
                                "Identity, then resolve usable Memory "
                                "evidence.",
                                "discriminant": "memory.resolve_actor_memory_context.resolve_actor_memory_context",
                                "endpoint_ref": "memory.resolve_actor_memory_context.resolve_actor_memory_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_actor_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve actor-scoped Memory context " "into a compact consumer frame.",
                                "discriminant": "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",
                                "endpoint_ref": "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_actor_memory_context_frame",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextFrameRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveActorMemoryContextFrameResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_actor_memory_context_frame",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve one actor working-memory lane "
                                "into evidence-labeled context.",
                                "discriminant": "memory.resolve_memory_context.resolve_memory_context",
                                "endpoint_ref": "memory.resolve_memory_context.resolve_memory_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveMemoryContextRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ResolveMemoryContextResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ResolveMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "resolve_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Validate one retained "
                                "MemoryWorkingItem and return source "
                                "evidence.",
                                "discriminant": "memory.validate_memory_working_item.validate_memory_working_item",
                                "endpoint_ref": "memory.validate_memory_working_item.validate_memory_working_item",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "validate_memory_working_item",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ValidateMemoryWorkingItemRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.ValidateMemoryWorkingItemResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                            }
                        ],
                        "name": "validate_memory_working_item",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read and stream actor-scoped Memory " "context snapshots.",
                                "discriminant": "memory.watch_actor_memory_context.watch_actor_memory_context",
                                "endpoint_ref": "memory.watch_actor_memory_context.watch_actor_memory_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_actor_memory_context",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed Memory " "actor-context snapshots.",
                                    "events": [
                                        {
                                            "class_ref": "aware_memory_service_dto.memory.working.MemoryActorContextEvent",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_memory_service_dto.memory.working.models.MemoryActorContextEvent",
                                            "source_path": "bindings/memory.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/memory.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_actor_memory_context",
                        "source_path": "bindings/memory.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read and stream actor-scoped Memory " "consumer frames.",
                                "discriminant": "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",
                                "endpoint_ref": "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "watch_actor_memory_context_frame",
                                "request": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameRequest",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextFrameRequest",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameResponse",
                                    "python_model_ref": "aware_memory_service_dto.memory.working.service_operation.WatchActorMemoryContextFrameResponse",
                                    "source_path": "bindings/memory.apis.aware",
                                },
                                "source_path": "bindings/memory.apis.aware",
                                "stream": {
                                    "description": "Canonical streamed Memory " "actor-context consumer " "frames.",
                                    "events": [
                                        {
                                            "class_ref": "aware_memory_service_dto.memory.working.MemoryActorContextFrameEvent",
                                            "kind": "snapshot",
                                            "python_model_ref": "aware_memory_service_dto.memory.working.models.MemoryActorContextFrameEvent",
                                            "source_path": "bindings/memory.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/memory.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "watch_actor_memory_context_frame",
                        "source_path": "bindings/memory.apis.aware",
                    },
                ],
                "name": "memory",
                "source_path": "bindings/memory.apis.aware",
            }
        ],
        "fqn_prefix": "aware_memory_service_api",
        "package_name": "memory-service-api",
        "schema_version": 1,
    }
)

MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF: Final[str] = (
    "memory.describe_memory_working.describe_memory_working"
)
MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF: Final[str] = (
    "memory.ensure_memory_working.ensure_memory_working"
)
MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF: Final[str] = (
    "memory.list_memory_working_items.list_memory_working_items"
)
MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF: Final[str] = (
    "memory.record_resolved_event_meaning.record_resolved_event_meaning"
)
MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "memory.remember_attention_transition.remember_attention_transition"
)
MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF: Final[str] = "memory.remember_content.remember_content"
MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF: Final[str] = "memory.remember_event.remember_event"
MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: Final[str] = (
    "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame"
)
MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.resolve_actor_memory_context.resolve_actor_memory_context"
)
MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.resolve_memory_context.resolve_memory_context"
)
MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF: Final[str] = (
    "memory.validate_memory_working_item.validate_memory_working_item"
)
MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: Final[str] = (
    "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame"
)
MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.watch_actor_memory_context.watch_actor_memory_context"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "memory.describe_memory_working.describe_memory_working": MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF,
    "memory.ensure_memory_working.ensure_memory_working": MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF,
    "memory.list_memory_working_items.list_memory_working_items": MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF,
    "memory.record_resolved_event_meaning.record_resolved_event_meaning": MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF,
    "memory.remember_attention_transition.remember_attention_transition": MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF,
    "memory.remember_content.remember_content": MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF,
    "memory.remember_event.remember_event": MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF,
    "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame": MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    "memory.resolve_actor_memory_context.resolve_actor_memory_context": MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
    "memory.resolve_memory_context.resolve_memory_context": MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF,
    "memory.validate_memory_working_item.validate_memory_working_item": MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF,
    "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame": MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    "memory.watch_actor_memory_context.watch_actor_memory_context": MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF",
    "MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF",
    "MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF",
    "MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF",
    "MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF",
    "MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF",
    "MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF",
    "MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF",
    "MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF",
]
