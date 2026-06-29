# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "meta-service-api"
API_FQN_PREFIX: Final[str] = "aware_meta_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Subscribe to remote-safe Meta commit " "fan-out events.",
                                "discriminant": "meta.commit.subscribe",
                                "name": "subscribe",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitSubscriptionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitSubscriptionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                                "stream": {
                                    "description": "Canonical Meta commit "
                                    "events emitted after domain "
                                    "commit and required Meta "
                                    "reactions complete.",
                                    "events": [
                                        {
                                            "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitEventEnvelope",
                                            "kind": "delta",
                                            "source_path": "bindings/meta.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/meta.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "commit",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Analyze one Meta ObjectConfigGraph "
                                "package for constructor/projection "
                                "completeness without mutating graph "
                                "state.",
                                "discriminant": "meta.diagnostics.analyze_object_config_graph_completeness",
                                "name": "analyze_object_config_graph_completeness",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "diagnostics",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current committed graph lane "
                                "head through Meta service authority.",
                                "discriminant": "meta.graph.get_lane_head",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "description": "Read one committed "
                                "ObjectInstanceGraphCommit through Meta "
                                "service authority.",
                                "discriminant": "meta.graph.get_object_instance_graph_commit",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "description": "Invoke one graph function through the "
                                "canonical Meta commit authority "
                                "boundary.",
                                "discriminant": "meta.graph.invoke_function",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "description": "Invoke one graph function against an "
                                "explicit temporal overlay without "
                                "committing durable graph state.",
                                "discriminant": "meta.graph.invoke_temporal_function",
                                "name": "invoke_temporal_function",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "description": "Resolve a renderer-safe Meta graph "
                                "view from lane and commit coordinates "
                                "without mutating graph state.",
                                "discriminant": "meta.graph.resolve_graph_view",
                                "name": "resolve_graph_view",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "description": "Resolve runtime projection coordinates "
                                "through Meta service authority without "
                                "mutating graph state.",
                                "discriminant": "meta.graph.resolve_projection",
                                "name": "resolve_projection",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                        ],
                        "name": "graph",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure one canonical "
                                "ObjectConfigGraphPackage through Meta "
                                "Service authority.",
                                "discriminant": "meta.package.ensure_object_config_graph_package",
                                "name": "ensure_object_config_graph_package",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure the OCG-backed database is "
                                "ready from a Structure-resolved "
                                "environment DB artifact receipt.",
                                "discriminant": "meta.persistence.ensure_database_ready",
                                "name": "ensure_database_ready",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "persistence",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe Meta-owned runtime read-model "
                                "truth for Workspace-required "
                                "projections without exposing raw "
                                "runtime/index objects.",
                                "discriminant": "meta.runtime_read_model.describe_workspace",
                                "name": "describe_workspace",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.runtime.MetaRuntimeReadModelRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.runtime.MetaRuntimeReadModelResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "runtime_read_model",
                        "source_path": "bindings/meta.apis.aware",
                    },
                ],
                "name": "meta",
                "source_path": "bindings/meta.apis.aware",
            }
        ],
        "fqn_prefix": "aware_meta_service_api",
        "package_name": "meta-service-api",
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
                                "description": "Subscribe to remote-safe Meta commit " "fan-out events.",
                                "discriminant": "meta.commit.subscribe",
                                "endpoint_ref": "meta.commit.subscribe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "subscribe",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitSubscriptionRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.commit_event.MetaCommitSubscriptionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitSubscriptionResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.commit_event.MetaCommitSubscriptionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                                "stream": {
                                    "description": "Canonical Meta commit "
                                    "events emitted after domain "
                                    "commit and required Meta "
                                    "reactions complete.",
                                    "events": [
                                        {
                                            "class_ref": "aware_meta_service_dto.graph.instance.MetaCommitEventEnvelope",
                                            "kind": "delta",
                                            "python_model_ref": "aware_meta_service_dto.graph.instance.commit_event.MetaCommitEventEnvelope",
                                            "source_path": "bindings/meta.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/meta.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "commit",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Analyze one Meta ObjectConfigGraph "
                                "package for constructor/projection "
                                "completeness without mutating graph "
                                "state.",
                                "discriminant": "meta.diagnostics.analyze_object_config_graph_completeness",
                                "endpoint_ref": "meta.diagnostics.analyze_object_config_graph_completeness",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "analyze_object_config_graph_completeness",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeRequest",
                                    "python_model_ref": "aware_meta_service_dto.diagnostics.completeness.MetaCompletenessAnalyzeRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.diagnostics.MetaCompletenessAnalyzeResponse",
                                    "python_model_ref": "aware_meta_service_dto.diagnostics.completeness.MetaCompletenessAnalyzeResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "diagnostics",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current committed graph lane "
                                "head through Meta service authority.",
                                "discriminant": "meta.graph.get_lane_head",
                                "endpoint_ref": "meta.graph.get_lane_head",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphGetLaneHeadRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetLaneHeadResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphGetLaneHeadResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one committed "
                                "ObjectInstanceGraphCommit through Meta "
                                "service authority.",
                                "discriminant": "meta.graph.get_object_instance_graph_commit",
                                "endpoint_ref": "meta.graph.get_object_instance_graph_commit",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphGetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphGetObjectInstanceGraphCommitResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphGetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one graph function through the "
                                "canonical Meta commit authority "
                                "boundary.",
                                "discriminant": "meta.graph.invoke_function",
                                "endpoint_ref": "meta.graph.invoke_function",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphInvokeFunctionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeFunctionResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphInvokeFunctionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one graph function against an "
                                "explicit temporal overlay without "
                                "committing durable graph state.",
                                "discriminant": "meta.graph.invoke_temporal_function",
                                "endpoint_ref": "meta.graph.invoke_temporal_function",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_temporal_function",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphInvokeTemporalFunctionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphInvokeTemporalFunctionResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphInvokeTemporalFunctionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve a renderer-safe Meta graph "
                                "view from lane and commit coordinates "
                                "without mutating graph state.",
                                "discriminant": "meta.graph.resolve_graph_view",
                                "endpoint_ref": "meta.graph.resolve_graph_view",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_graph_view",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.view.graph_view.MetaGraphResolveGraphViewRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.view.MetaGraphResolveGraphViewResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.view.graph_view.MetaGraphResolveGraphViewResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve runtime projection coordinates "
                                "through Meta service authority without "
                                "mutating graph state.",
                                "discriminant": "meta.graph.resolve_projection",
                                "endpoint_ref": "meta.graph.resolve_projection",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_projection",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphResolveProjectionRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.instance.MetaGraphResolveProjectionResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.instance.function_call.MetaGraphResolveProjectionResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            },
                        ],
                        "name": "graph",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure one canonical "
                                "ObjectConfigGraphPackage through Meta "
                                "Service authority.",
                                "discriminant": "meta.package.ensure_object_config_graph_package",
                                "endpoint_ref": "meta.package.ensure_object_config_graph_package",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_object_config_graph_package",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureRequest",
                                    "python_model_ref": "aware_meta_service_dto.graph.config.package_compile.MetaObjectConfigGraphPackageEnsureRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.graph.config.MetaObjectConfigGraphPackageEnsureResponse",
                                    "python_model_ref": "aware_meta_service_dto.graph.config.package_compile.MetaObjectConfigGraphPackageEnsureResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure the OCG-backed database is "
                                "ready from a Structure-resolved "
                                "environment DB artifact receipt.",
                                "discriminant": "meta.persistence.ensure_database_ready",
                                "endpoint_ref": "meta.persistence.ensure_database_ready",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_database_ready",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyRequest",
                                    "python_model_ref": "aware_meta_service_dto.persistence.database_readiness.MetaPersistenceEnsureDatabaseReadyRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.persistence.MetaPersistenceEnsureDatabaseReadyResponse",
                                    "python_model_ref": "aware_meta_service_dto.persistence.database_readiness.MetaPersistenceEnsureDatabaseReadyResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "persistence",
                        "source_path": "bindings/meta.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe Meta-owned runtime read-model "
                                "truth for Workspace-required "
                                "projections without exposing raw "
                                "runtime/index objects.",
                                "discriminant": "meta.runtime_read_model.describe_workspace",
                                "endpoint_ref": "meta.runtime_read_model.describe_workspace",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_workspace",
                                "request": {
                                    "class_ref": "aware_meta_service_dto.runtime.MetaRuntimeReadModelRequest",
                                    "python_model_ref": "aware_meta_service_dto.runtime.read_model.MetaRuntimeReadModelRequest",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_meta_service_dto.runtime.MetaRuntimeReadModelResponse",
                                    "python_model_ref": "aware_meta_service_dto.runtime.read_model.MetaRuntimeReadModelResponse",
                                    "source_path": "bindings/meta.apis.aware",
                                },
                                "source_path": "bindings/meta.apis.aware",
                            }
                        ],
                        "name": "runtime_read_model",
                        "source_path": "bindings/meta.apis.aware",
                    },
                ],
                "name": "meta",
                "source_path": "bindings/meta.apis.aware",
            }
        ],
        "fqn_prefix": "aware_meta_service_api",
        "package_name": "meta-service-api",
        "schema_version": 1,
    }
)

META__COMMIT__SUBSCRIBE_ENDPOINT_REF: Final[str] = "meta.commit.subscribe"
META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF: Final[str] = (
    "meta.diagnostics.analyze_object_config_graph_completeness"
)
META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "meta.graph.get_lane_head"
META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = "meta.graph.get_object_instance_graph_commit"
META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "meta.graph.invoke_function"
META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF: Final[str] = "meta.graph.invoke_temporal_function"
META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF: Final[str] = "meta.graph.resolve_graph_view"
META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: Final[str] = "meta.graph.resolve_projection"
META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: Final[str] = (
    "meta.package.ensure_object_config_graph_package"
)
META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF: Final[str] = "meta.persistence.ensure_database_ready"
META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF: Final[str] = "meta.runtime_read_model.describe_workspace"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "meta.commit.subscribe": META__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    "meta.diagnostics.analyze_object_config_graph_completeness": META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF,
    "meta.graph.get_lane_head": META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    "meta.graph.get_object_instance_graph_commit": META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    "meta.graph.invoke_function": META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
    "meta.graph.invoke_temporal_function": META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF,
    "meta.graph.resolve_graph_view": META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF,
    "meta.graph.resolve_projection": META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
    "meta.package.ensure_object_config_graph_package": META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
    "meta.persistence.ensure_database_ready": META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF,
    "meta.runtime_read_model.describe_workspace": META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "META__COMMIT__SUBSCRIBE_ENDPOINT_REF",
    "META__DIAGNOSTICS__ANALYZE_OBJECT_CONFIG_GRAPH_COMPLETENESS_ENDPOINT_REF",
    "META__GRAPH__GET_LANE_HEAD_ENDPOINT_REF",
    "META__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "META__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF",
    "META__GRAPH__INVOKE_TEMPORAL_FUNCTION_ENDPOINT_REF",
    "META__GRAPH__RESOLVE_GRAPH_VIEW_ENDPOINT_REF",
    "META__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF",
    "META__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF",
    "META__PERSISTENCE__ENSURE_DATABASE_READY_ENDPOINT_REF",
    "META__RUNTIME_READ_MODEL__DESCRIBE_WORKSPACE_ENDPOINT_REF",
]
