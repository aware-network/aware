# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "ontology-service-api"
API_FQN_PREFIX: Final[str] = "aware_ontology_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Subscribe to remote-safe Ontology " "commit fan-out events.",
                                "discriminant": "ontology.commit.subscribe",
                                "name": "subscribe",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                                "stream": {
                                    "description": "Canonical Ontology commit "
                                    "events emitted after domain "
                                    "commit and required "
                                    "Ontology reactions "
                                    "complete.",
                                    "events": [
                                        {
                                            "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitEventEnvelope",
                                            "kind": "delta",
                                            "source_path": "bindings/ontology.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/ontology.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "commit",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current committed ontology "
                                "graph lane head through Ontology "
                                "service authority.",
                                "discriminant": "ontology.graph.get_lane_head",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "description": "Read one committed "
                                "ObjectInstanceGraphCommit through "
                                "Ontology service authority.",
                                "discriminant": "ontology.graph.get_object_instance_graph_commit",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "description": "Invoke one ontology graph function "
                                "through Ontology-owned GraphOS "
                                "authority.",
                                "discriminant": "ontology.graph.invoke_function",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "description": "Resolve ontology runtime projection "
                                "coordinates without mutating graph "
                                "state.",
                                "discriminant": "ontology.graph.resolve_projection",
                                "name": "resolve_projection",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                        ],
                        "name": "graph",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure one Ontology-owned "
                                "ObjectConfigGraphPackage through the "
                                "Ontology service boundary.",
                                "discriminant": "ontology.package.ensure_object_config_graph_package",
                                "name": "ensure_object_config_graph_package",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure Ontology GraphOS persistence is "
                                "ready without making Environment own "
                                "ontology DB setup.",
                                "discriminant": "ontology.persistence.ensure_ready",
                                "name": "ensure_ready",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "persistence",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve an Ontology-owned runtime "
                                "artifact-set descriptor for explicit "
                                "materialization or revision "
                                "coordinates.",
                                "discriminant": "ontology.runtime.resolve_runtime_artifact_set",
                                "name": "resolve_runtime_artifact_set",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "runtime",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                ],
                "name": "ontology",
                "source_path": "bindings/ontology.apis.aware",
            }
        ],
        "fqn_prefix": "aware_ontology_service_api",
        "package_name": "ontology-service-api",
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
                                "description": "Subscribe to remote-safe Ontology " "commit fan-out events.",
                                "discriminant": "ontology.commit.subscribe",
                                "endpoint_ref": "ontology.commit.subscribe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "subscribe",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.commit_event.OntologyCommitSubscriptionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitSubscriptionResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.commit_event.OntologyCommitSubscriptionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                                "stream": {
                                    "description": "Canonical Ontology commit "
                                    "events emitted after domain "
                                    "commit and required "
                                    "Ontology reactions "
                                    "complete.",
                                    "events": [
                                        {
                                            "class_ref": "aware_ontology_service_dto.graph.instance.OntologyCommitEventEnvelope",
                                            "kind": "delta",
                                            "python_model_ref": "aware_ontology_service_dto.graph.instance.commit_event.OntologyCommitEventEnvelope",
                                            "source_path": "bindings/ontology.apis.aware",
                                        }
                                    ],
                                    "source_path": "bindings/ontology.apis.aware",
                                    "stream_mode": "server",
                                },
                            }
                        ],
                        "name": "commit",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current committed ontology "
                                "graph lane head through Ontology "
                                "service authority.",
                                "discriminant": "ontology.graph.get_lane_head",
                                "endpoint_ref": "ontology.graph.get_lane_head",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphGetLaneHeadRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetLaneHeadResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphGetLaneHeadResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one committed "
                                "ObjectInstanceGraphCommit through "
                                "Ontology service authority.",
                                "discriminant": "ontology.graph.get_object_instance_graph_commit",
                                "endpoint_ref": "ontology.graph.get_object_instance_graph_commit",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphGetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphGetObjectInstanceGraphCommitResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphGetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one ontology graph function "
                                "through Ontology-owned GraphOS "
                                "authority.",
                                "discriminant": "ontology.graph.invoke_function",
                                "endpoint_ref": "ontology.graph.invoke_function",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphInvokeFunctionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphInvokeFunctionResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphInvokeFunctionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve ontology runtime projection "
                                "coordinates without mutating graph "
                                "state.",
                                "discriminant": "ontology.graph.resolve_projection",
                                "endpoint_ref": "ontology.graph.resolve_projection",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_projection",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphResolveProjectionRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.instance.OntologyGraphResolveProjectionResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.instance.function_call.OntologyGraphResolveProjectionResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            },
                        ],
                        "name": "graph",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure one Ontology-owned "
                                "ObjectConfigGraphPackage through the "
                                "Ontology service boundary.",
                                "discriminant": "ontology.package.ensure_object_config_graph_package",
                                "endpoint_ref": "ontology.package.ensure_object_config_graph_package",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_object_config_graph_package",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureRequest",
                                    "python_model_ref": "aware_ontology_service_dto.graph.config.package_compile.OntologyObjectConfigGraphPackageEnsureRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.graph.config.OntologyObjectConfigGraphPackageEnsureResponse",
                                    "python_model_ref": "aware_ontology_service_dto.graph.config.package_compile.OntologyObjectConfigGraphPackageEnsureResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "package",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure Ontology GraphOS persistence is "
                                "ready without making Environment own "
                                "ontology DB setup.",
                                "discriminant": "ontology.persistence.ensure_ready",
                                "endpoint_ref": "ontology.persistence.ensure_ready",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_ready",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyRequest",
                                    "python_model_ref": "aware_ontology_service_dto.persistence.readiness.OntologyPersistenceEnsureReadyRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.persistence.OntologyPersistenceEnsureReadyResponse",
                                    "python_model_ref": "aware_ontology_service_dto.persistence.readiness.OntologyPersistenceEnsureReadyResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "persistence",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve an Ontology-owned runtime "
                                "artifact-set descriptor for explicit "
                                "materialization or revision "
                                "coordinates.",
                                "discriminant": "ontology.runtime.resolve_runtime_artifact_set",
                                "endpoint_ref": "ontology.runtime.resolve_runtime_artifact_set",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_runtime_artifact_set",
                                "request": {
                                    "class_ref": "aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveRequest",
                                    "python_model_ref": "aware_ontology_service_dto.runtime.artifact_set.OntologyRuntimeArtifactSetResolveRequest",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_ontology_service_dto.runtime.OntologyRuntimeArtifactSetResolveResponse",
                                    "python_model_ref": "aware_ontology_service_dto.runtime.artifact_set.OntologyRuntimeArtifactSetResolveResponse",
                                    "source_path": "bindings/ontology.apis.aware",
                                },
                                "source_path": "bindings/ontology.apis.aware",
                            }
                        ],
                        "name": "runtime",
                        "source_path": "bindings/ontology.apis.aware",
                    },
                ],
                "name": "ontology",
                "source_path": "bindings/ontology.apis.aware",
            }
        ],
        "fqn_prefix": "aware_ontology_service_api",
        "package_name": "ontology-service-api",
        "schema_version": 1,
    }
)

ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF: Final[str] = "ontology.commit.subscribe"
ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "ontology.graph.get_lane_head"
ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = (
    "ontology.graph.get_object_instance_graph_commit"
)
ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "ontology.graph.invoke_function"
ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF: Final[str] = "ontology.graph.resolve_projection"
ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF: Final[str] = (
    "ontology.package.ensure_object_config_graph_package"
)
ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF: Final[str] = "ontology.persistence.ensure_ready"
ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF: Final[str] = (
    "ontology.runtime.resolve_runtime_artifact_set"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "ontology.commit.subscribe": ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF,
    "ontology.graph.get_lane_head": ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF,
    "ontology.graph.get_object_instance_graph_commit": ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    "ontology.graph.invoke_function": ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF,
    "ontology.graph.resolve_projection": ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
    "ontology.package.ensure_object_config_graph_package": ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF,
    "ontology.persistence.ensure_ready": ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF,
    "ontology.runtime.resolve_runtime_artifact_set": ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "ONTOLOGY__COMMIT__SUBSCRIBE_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__GET_LANE_HEAD_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__INVOKE_FUNCTION_ENDPOINT_REF",
    "ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF",
    "ONTOLOGY__PACKAGE__ENSURE_OBJECT_CONFIG_GRAPH_PACKAGE_ENDPOINT_REF",
    "ONTOLOGY__PERSISTENCE__ENSURE_READY_ENDPOINT_REF",
    "ONTOLOGY__RUNTIME__RESOLVE_RUNTIME_ARTIFACT_SET_ENDPOINT_REF",
]
