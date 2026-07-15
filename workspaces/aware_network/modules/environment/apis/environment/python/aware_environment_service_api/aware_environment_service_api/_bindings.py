# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "environment-service-api"
API_FQN_PREFIX: Final[str] = "aware_environment_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Admit an actor to an "
                                "EnvironmentProfile through committed "
                                "ActorConfig eligibility and Identity "
                                "role assignment.",
                                "discriminant": "environment.actor_admission.admit_actor",
                                "name": "admit_actor",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.AdmitEnvironmentActorRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.AdmitEnvironmentActorResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "actor_admission",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read Environment runtime capability "
                                "advertisement through the canonical "
                                "Environment API boundary.",
                                "discriminant": "environment.capabilities.fetch_capabilities",
                                "name": "fetch_capabilities",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.FetchCapabilitiesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.FetchCapabilitiesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "capabilities",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Materialize a committed projection "
                                "root as a typed ontology DTO snapshot "
                                "through an explicit commit locator.",
                                "discriminant": "environment.committed_projection_dto.materialize_committed_projection_dto",
                                "name": "materialize_committed_projection_dto",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "committed_projection_dto",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe one provisioned Environment "
                                "instance and its current boot/lane "
                                "pointers.",
                                "discriminant": "environment.describe.describe_environment",
                                "name": "describe_environment",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "describe",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe the hosted EnvironmentConfig "
                                "through the canonical Environment API "
                                "boundary.",
                                "discriminant": "environment.describe_config.describe_environment_config",
                                "name": "describe_environment_config",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentConfigRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentConfigResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "describe_config",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Invoke one graph function through the "
                                "canonical commit-backed Environment "
                                "runtime boundary.",
                                "discriminant": "environment.function_call.invoke_function",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.InvokeFunctionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.InvokeFunctionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "function_call",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the current head commit for one " "explicit Environment lane key.",
                                "discriminant": "environment.lane_head.get_lane_head",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.GetLaneHeadRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.GetLaneHeadResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "lane_head",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Create an EnvironmentSession-owned "
                                "navigation context after accepted "
                                "session join.",
                                "discriminant": "environment.navigation.create_navigation_context",
                                "name": "create_navigation_context",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.CreateEnvironmentNavigationContextRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.CreateEnvironmentNavigationContextResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Describe one Environment navigation "
                                "context without mutating Attention or "
                                "Experience state.",
                                "discriminant": "environment.navigation.describe_navigation_context",
                                "name": "describe_navigation_context",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "List Environment navigation contexts "
                                "owned by one EnvironmentSession.",
                                "discriminant": "environment.navigation.list_navigation_contexts",
                                "name": "list_navigation_contexts",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentNavigationContextsRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentNavigationContextsResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Select the Process/Thread target for "
                                "one Environment navigation context.",
                                "discriminant": "environment.navigation.select_navigation_target",
                                "name": "select_navigation_target",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "navigation",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read one ObjectInstanceGraphCommit by "
                                "id through the Environment service "
                                "boundary.",
                                "discriminant": "environment.object_instance_graph_commit.get_object_instance_graph_commit",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "object_instance_graph_commit",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Attach one Ontology authority to a "
                                "stable Environment through the "
                                "canonical Environment API boundary.",
                                "discriminant": "environment.ontology.attach_environment_ontology",
                                "name": "attach_environment_ontology",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.AttachEnvironmentOntologyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.AttachEnvironmentOntologyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Resolve and register one "
                                "Ontology-owned runtime artifact set "
                                "for a running Environment.",
                                "discriminant": "environment.ontology.ensure_environment_ontology_runtime",
                                "name": "ensure_environment_ontology_runtime",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "List Environment-owned Ontology "
                                "membership pointers without expanding "
                                "Ontology-owned OIGI inventory.",
                                "discriminant": "environment.ontology.list_environment_ontologies",
                                "name": "list_environment_ontologies",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentOntologiesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentOntologiesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "ontology",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Provision concrete Environment "
                                "Process/Thread topology from an "
                                "installed EnvironmentProfile seed.",
                                "discriminant": "environment.profile.provision_environment_profile",
                                "name": "provision_environment_profile",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ProvisionEnvironmentProfileRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ProvisionEnvironmentProfileResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Install or update Environment-owned "
                                "profile topology through the "
                                "Environment API boundary.",
                                "discriminant": "environment.profile.upsert_environment_profile",
                                "name": "upsert_environment_profile",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.UpsertEnvironmentProfileRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.UpsertEnvironmentProfileResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "profile",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Ensure the Environment runtime is "
                                "ready to execute commit-backed graph "
                                "operations.",
                                "discriminant": "environment.ready.ensure_ready",
                                "name": "ensure_ready",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureReadyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureReadyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "ready",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve hosted runtime "
                                "OCG/function/class references for "
                                "remote graph invocation.",
                                "discriminant": "environment.runtime_ref.resolve_runtime_refs",
                                "name": "resolve_runtime_refs",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveRuntimeRefsRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveRuntimeRefsResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "runtime_ref",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Configure Environment-hosted service "
                                "API dependency routes through the "
                                "canonical Environment API boundary.",
                                "discriminant": "environment.service_routes.configure_service_api_dependency_routes",
                                "name": "configure_service_api_dependency_routes",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "service_routes",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe a shared EnvironmentSession "
                                "without resolving navigation or "
                                "Attention.",
                                "discriminant": "environment.session.describe_session",
                                "name": "describe_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Join a shared EnvironmentSession after "
                                "accepted Environment admission.",
                                "discriminant": "environment.session.join_session",
                                "name": "join_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.JoinEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.JoinEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Commit one EnvironmentSession-owned "
                                "portal to an existing AttentionSession "
                                "authority.",
                                "discriminant": "environment.session.mount_attention_session",
                                "name": "mount_attention_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.MountEnvironmentSessionAttentionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.MountEnvironmentSessionAttentionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Resolve Environment session "
                                "Thread/Layout pins against Attention "
                                "session and transition validation.",
                                "discriminant": "environment.session.resolve_attention",
                                "name": "resolve_attention",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "description": "Start a shared EnvironmentSession "
                                "after accepted Environment admission.",
                                "discriminant": "environment.session.start_session",
                                "name": "start_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.StartEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.StartEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "session",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Read the canonical Environment status "
                                "envelope with explicit authority "
                                "blocks.",
                                "discriminant": "environment.status.describe_environment_status",
                                "name": "describe_environment_status",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentStatusRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentStatusResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "status",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Describe the process/thread topology "
                                "and attached OIG lanes for an "
                                "Environment.",
                                "discriminant": "environment.topology.describe_environment_topology",
                                "name": "describe_environment_topology",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentTopologyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentTopologyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "topology",
                        "source_path": "bindings/environment.apis.aware",
                    },
                ],
                "name": "environment",
                "source_path": "bindings/environment.apis.aware",
            }
        ],
        "fqn_prefix": "aware_environment_service_api",
        "package_name": "environment-service-api",
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
                                "description": "Admit an actor to an "
                                "EnvironmentProfile through committed "
                                "ActorConfig eligibility and Identity "
                                "role assignment.",
                                "discriminant": "environment.actor_admission.admit_actor",
                                "endpoint_ref": "environment.actor_admission.admit_actor",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "admit_actor",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.AdmitEnvironmentActorRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.AdmitEnvironmentActorRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.AdmitEnvironmentActorResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.AdmitEnvironmentActorResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "actor_admission",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read Environment runtime capability "
                                "advertisement through the canonical "
                                "Environment API boundary.",
                                "discriminant": "environment.capabilities.fetch_capabilities",
                                "endpoint_ref": "environment.capabilities.fetch_capabilities",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "fetch_capabilities",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.FetchCapabilitiesRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.FetchCapabilitiesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.FetchCapabilitiesResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.FetchCapabilitiesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "capabilities",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Materialize a committed projection "
                                "root as a typed ontology DTO snapshot "
                                "through an explicit commit locator.",
                                "discriminant": "environment.committed_projection_dto.materialize_committed_projection_dto",
                                "endpoint_ref": "environment.committed_projection_dto.materialize_committed_projection_dto",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "materialize_committed_projection_dto",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.MaterializeCommittedProjectionDtoRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.MaterializeCommittedProjectionDtoResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.MaterializeCommittedProjectionDtoResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "committed_projection_dto",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe one provisioned Environment "
                                "instance and its current boot/lane "
                                "pointers.",
                                "discriminant": "environment.describe.describe_environment",
                                "endpoint_ref": "environment.describe.describe_environment",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_environment",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "describe",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe the hosted EnvironmentConfig "
                                "through the canonical Environment API "
                                "boundary.",
                                "discriminant": "environment.describe_config.describe_environment_config",
                                "endpoint_ref": "environment.describe_config.describe_environment_config",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_environment_config",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentConfigRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentConfigRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentConfigResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentConfigResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "describe_config",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Invoke one graph function through the "
                                "canonical commit-backed Environment "
                                "runtime boundary.",
                                "discriminant": "environment.function_call.invoke_function",
                                "endpoint_ref": "environment.function_call.invoke_function",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "invoke_function",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.InvokeFunctionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.InvokeFunctionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.InvokeFunctionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.InvokeFunctionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "function_call",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the current head commit for one " "explicit Environment lane key.",
                                "discriminant": "environment.lane_head.get_lane_head",
                                "endpoint_ref": "environment.lane_head.get_lane_head",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_lane_head",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.GetLaneHeadRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.GetLaneHeadRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.GetLaneHeadResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.GetLaneHeadResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "lane_head",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Create an EnvironmentSession-owned "
                                "navigation context after accepted "
                                "session join.",
                                "discriminant": "environment.navigation.create_navigation_context",
                                "endpoint_ref": "environment.navigation.create_navigation_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "create_navigation_context",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.CreateEnvironmentNavigationContextRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.CreateEnvironmentNavigationContextRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.CreateEnvironmentNavigationContextResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.CreateEnvironmentNavigationContextResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe one Environment navigation "
                                "context without mutating Attention or "
                                "Experience state.",
                                "discriminant": "environment.navigation.describe_navigation_context",
                                "endpoint_ref": "environment.navigation.describe_navigation_context",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_navigation_context",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentNavigationContextRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentNavigationContextResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentNavigationContextResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List Environment navigation contexts "
                                "owned by one EnvironmentSession.",
                                "discriminant": "environment.navigation.list_navigation_contexts",
                                "endpoint_ref": "environment.navigation.list_navigation_contexts",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_navigation_contexts",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentNavigationContextsRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ListEnvironmentNavigationContextsRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentNavigationContextsResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ListEnvironmentNavigationContextsResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Select the Process/Thread target for "
                                "one Environment navigation context.",
                                "discriminant": "environment.navigation.select_navigation_target",
                                "endpoint_ref": "environment.navigation.select_navigation_target",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "select_navigation_target",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.SelectEnvironmentNavigationTargetRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.SelectEnvironmentNavigationTargetResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.SelectEnvironmentNavigationTargetResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "navigation",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read one ObjectInstanceGraphCommit by "
                                "id through the Environment service "
                                "boundary.",
                                "discriminant": "environment.object_instance_graph_commit.get_object_instance_graph_commit",
                                "endpoint_ref": "environment.object_instance_graph_commit.get_object_instance_graph_commit",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "get_object_instance_graph_commit",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.GetObjectInstanceGraphCommitRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.GetObjectInstanceGraphCommitResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.GetObjectInstanceGraphCommitResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "object_instance_graph_commit",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Attach one Ontology authority to a "
                                "stable Environment through the "
                                "canonical Environment API boundary.",
                                "discriminant": "environment.ontology.attach_environment_ontology",
                                "endpoint_ref": "environment.ontology.attach_environment_ontology",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "attach_environment_ontology",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.AttachEnvironmentOntologyRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.AttachEnvironmentOntologyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.AttachEnvironmentOntologyResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.AttachEnvironmentOntologyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve and register one "
                                "Ontology-owned runtime artifact set "
                                "for a running Environment.",
                                "discriminant": "environment.ontology.ensure_environment_ontology_runtime",
                                "endpoint_ref": "environment.ontology.ensure_environment_ontology_runtime",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_environment_ontology_runtime",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.EnsureEnvironmentOntologyRuntimeRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureEnvironmentOntologyRuntimeResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.EnsureEnvironmentOntologyRuntimeResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List Environment-owned Ontology "
                                "membership pointers without expanding "
                                "Ontology-owned OIGI inventory.",
                                "discriminant": "environment.ontology.list_environment_ontologies",
                                "endpoint_ref": "environment.ontology.list_environment_ontologies",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list_environment_ontologies",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentOntologiesRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ListEnvironmentOntologiesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ListEnvironmentOntologiesResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ListEnvironmentOntologiesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "ontology",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Provision concrete Environment "
                                "Process/Thread topology from an "
                                "installed EnvironmentProfile seed.",
                                "discriminant": "environment.profile.provision_environment_profile",
                                "endpoint_ref": "environment.profile.provision_environment_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "provision_environment_profile",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ProvisionEnvironmentProfileRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ProvisionEnvironmentProfileRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ProvisionEnvironmentProfileResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ProvisionEnvironmentProfileResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Install or update Environment-owned "
                                "profile topology through the "
                                "Environment API boundary.",
                                "discriminant": "environment.profile.upsert_environment_profile",
                                "endpoint_ref": "environment.profile.upsert_environment_profile",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "upsert_environment_profile",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.UpsertEnvironmentProfileRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.UpsertEnvironmentProfileRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.UpsertEnvironmentProfileResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.UpsertEnvironmentProfileResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "profile",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Ensure the Environment runtime is "
                                "ready to execute commit-backed graph "
                                "operations.",
                                "discriminant": "environment.ready.ensure_ready",
                                "endpoint_ref": "environment.ready.ensure_ready",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "ensure_ready",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureReadyRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.EnsureReadyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.EnsureReadyResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.EnsureReadyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "ready",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve hosted runtime "
                                "OCG/function/class references for "
                                "remote graph invocation.",
                                "discriminant": "environment.runtime_ref.resolve_runtime_refs",
                                "endpoint_ref": "environment.runtime_ref.resolve_runtime_refs",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_runtime_refs",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveRuntimeRefsRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ResolveRuntimeRefsRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveRuntimeRefsResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ResolveRuntimeRefsResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "runtime_ref",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Configure Environment-hosted service "
                                "API dependency routes through the "
                                "canonical Environment API boundary.",
                                "discriminant": "environment.service_routes.configure_service_api_dependency_routes",
                                "endpoint_ref": "environment.service_routes.configure_service_api_dependency_routes",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "configure_service_api_dependency_routes",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ConfigureServiceApiDependencyRoutesRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ConfigureServiceApiDependencyRoutesResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ConfigureServiceApiDependencyRoutesResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "service_routes",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe a shared EnvironmentSession "
                                "without resolving navigation or "
                                "Attention.",
                                "discriminant": "environment.session.describe_session",
                                "endpoint_ref": "environment.session.describe_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentSessionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentSessionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Join a shared EnvironmentSession after "
                                "accepted Environment admission.",
                                "discriminant": "environment.session.join_session",
                                "endpoint_ref": "environment.session.join_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "join_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.JoinEnvironmentSessionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.JoinEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.JoinEnvironmentSessionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.JoinEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Commit one EnvironmentSession-owned "
                                "portal to an existing AttentionSession "
                                "authority.",
                                "discriminant": "environment.session.mount_attention_session",
                                "endpoint_ref": "environment.session.mount_attention_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "mount_attention_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.MountEnvironmentSessionAttentionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.MountEnvironmentSessionAttentionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.MountEnvironmentSessionAttentionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.MountEnvironmentSessionAttentionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve Environment session "
                                "Thread/Layout pins against Attention "
                                "session and transition validation.",
                                "discriminant": "environment.session.resolve_attention",
                                "endpoint_ref": "environment.session.resolve_attention",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_attention",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ResolveEnvironmentSessionAttentionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.ResolveEnvironmentSessionAttentionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.ResolveEnvironmentSessionAttentionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Start a shared EnvironmentSession "
                                "after accepted Environment admission.",
                                "discriminant": "environment.session.start_session",
                                "endpoint_ref": "environment.session.start_session",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "start_session",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.StartEnvironmentSessionRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.StartEnvironmentSessionRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.StartEnvironmentSessionResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.StartEnvironmentSessionResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            },
                        ],
                        "name": "session",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Read the canonical Environment status "
                                "envelope with explicit authority "
                                "blocks.",
                                "discriminant": "environment.status.describe_environment_status",
                                "endpoint_ref": "environment.status.describe_environment_status",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_environment_status",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentStatusRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentStatusRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentStatusResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentStatusResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "status",
                        "source_path": "bindings/environment.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Describe the process/thread topology "
                                "and attached OIG lanes for an "
                                "Environment.",
                                "discriminant": "environment.topology.describe_environment_topology",
                                "endpoint_ref": "environment.topology.describe_environment_topology",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe_environment_topology",
                                "request": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentTopologyRequest",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentTopologyRequest",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_environment_service_dto.environment.DescribeEnvironmentTopologyResponse",
                                    "python_model_ref": "aware_environment_service_dto.environment.environment.DescribeEnvironmentTopologyResponse",
                                    "source_path": "bindings/environment.apis.aware",
                                },
                                "source_path": "bindings/environment.apis.aware",
                            }
                        ],
                        "name": "topology",
                        "source_path": "bindings/environment.apis.aware",
                    },
                ],
                "name": "environment",
                "source_path": "bindings/environment.apis.aware",
            }
        ],
        "fqn_prefix": "aware_environment_service_api",
        "package_name": "environment-service-api",
        "schema_version": 1,
    }
)

ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF: Final[str] = "environment.actor_admission.admit_actor"
ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF: Final[str] = "environment.capabilities.fetch_capabilities"
ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF: Final[str] = (
    "environment.committed_projection_dto.materialize_committed_projection_dto"
)
ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF: Final[str] = (
    "environment.describe_config.describe_environment_config"
)
ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF: Final[str] = "environment.describe.describe_environment"
ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF: Final[str] = "environment.function_call.invoke_function"
ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF: Final[str] = "environment.lane_head.get_lane_head"
ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "environment.navigation.create_navigation_context"
)
ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "environment.navigation.describe_navigation_context"
)
ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF: Final[str] = (
    "environment.navigation.list_navigation_contexts"
)
ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF: Final[str] = (
    "environment.navigation.select_navigation_target"
)
ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF: Final[str] = (
    "environment.object_instance_graph_commit.get_object_instance_graph_commit"
)
ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF: Final[str] = (
    "environment.ontology.attach_environment_ontology"
)
ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF: Final[str] = (
    "environment.ontology.ensure_environment_ontology_runtime"
)
ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF: Final[str] = (
    "environment.ontology.list_environment_ontologies"
)
ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "environment.profile.provision_environment_profile"
)
ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "environment.profile.upsert_environment_profile"
)
ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF: Final[str] = "environment.ready.ensure_ready"
ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF: Final[str] = "environment.runtime_ref.resolve_runtime_refs"
ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF: Final[str] = (
    "environment.service_routes.configure_service_api_dependency_routes"
)
ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF: Final[str] = "environment.session.describe_session"
ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF: Final[str] = "environment.session.join_session"
ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = "environment.session.mount_attention_session"
ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF: Final[str] = "environment.session.resolve_attention"
ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF: Final[str] = "environment.session.start_session"
ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF: Final[str] = (
    "environment.status.describe_environment_status"
)
ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF: Final[str] = (
    "environment.topology.describe_environment_topology"
)

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "environment.actor_admission.admit_actor": ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF,
    "environment.capabilities.fetch_capabilities": ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF,
    "environment.committed_projection_dto.materialize_committed_projection_dto": ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF,
    "environment.describe_config.describe_environment_config": ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF,
    "environment.describe.describe_environment": ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF,
    "environment.function_call.invoke_function": ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF,
    "environment.lane_head.get_lane_head": ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF,
    "environment.navigation.create_navigation_context": ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF,
    "environment.navigation.describe_navigation_context": ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF,
    "environment.navigation.list_navigation_contexts": ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF,
    "environment.navigation.select_navigation_target": ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF,
    "environment.object_instance_graph_commit.get_object_instance_graph_commit": ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF,
    "environment.ontology.attach_environment_ontology": ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF,
    "environment.ontology.ensure_environment_ontology_runtime": ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF,
    "environment.ontology.list_environment_ontologies": ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF,
    "environment.profile.provision_environment_profile": ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    "environment.profile.upsert_environment_profile": ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    "environment.ready.ensure_ready": ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF,
    "environment.runtime_ref.resolve_runtime_refs": ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF,
    "environment.service_routes.configure_service_api_dependency_routes": ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF,
    "environment.session.describe_session": ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF,
    "environment.session.join_session": ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF,
    "environment.session.mount_attention_session": ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF,
    "environment.session.resolve_attention": ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF,
    "environment.session.start_session": ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF,
    "environment.status.describe_environment_status": ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF,
    "environment.topology.describe_environment_topology": ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "ENVIRONMENT__ACTOR_ADMISSION__ADMIT_ACTOR_ENDPOINT_REF",
    "ENVIRONMENT__CAPABILITIES__FETCH_CAPABILITIES_ENDPOINT_REF",
    "ENVIRONMENT__COMMITTED_PROJECTION_DTO__MATERIALIZE_COMMITTED_PROJECTION_DTO_ENDPOINT_REF",
    "ENVIRONMENT__DESCRIBE_CONFIG__DESCRIBE_ENVIRONMENT_CONFIG_ENDPOINT_REF",
    "ENVIRONMENT__DESCRIBE__DESCRIBE_ENVIRONMENT_ENDPOINT_REF",
    "ENVIRONMENT__FUNCTION_CALL__INVOKE_FUNCTION_ENDPOINT_REF",
    "ENVIRONMENT__LANE_HEAD__GET_LANE_HEAD_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__CREATE_NAVIGATION_CONTEXT_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__DESCRIBE_NAVIGATION_CONTEXT_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__LIST_NAVIGATION_CONTEXTS_ENDPOINT_REF",
    "ENVIRONMENT__NAVIGATION__SELECT_NAVIGATION_TARGET_ENDPOINT_REF",
    "ENVIRONMENT__OBJECT_INSTANCE_GRAPH_COMMIT__GET_OBJECT_INSTANCE_GRAPH_COMMIT_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__ATTACH_ENVIRONMENT_ONTOLOGY_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__ENSURE_ENVIRONMENT_ONTOLOGY_RUNTIME_ENDPOINT_REF",
    "ENVIRONMENT__ONTOLOGY__LIST_ENVIRONMENT_ONTOLOGIES_ENDPOINT_REF",
    "ENVIRONMENT__PROFILE__PROVISION_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "ENVIRONMENT__PROFILE__UPSERT_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "ENVIRONMENT__READY__ENSURE_READY_ENDPOINT_REF",
    "ENVIRONMENT__RUNTIME_REF__RESOLVE_RUNTIME_REFS_ENDPOINT_REF",
    "ENVIRONMENT__SERVICE_ROUTES__CONFIGURE_SERVICE_API_DEPENDENCY_ROUTES_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__DESCRIBE_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__JOIN_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__MOUNT_ATTENTION_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__RESOLVE_ATTENTION_ENDPOINT_REF",
    "ENVIRONMENT__SESSION__START_SESSION_ENDPOINT_REF",
    "ENVIRONMENT__STATUS__DESCRIBE_ENVIRONMENT_STATUS_ENDPOINT_REF",
    "ENVIRONMENT__TOPOLOGY__DESCRIBE_ENVIRONMENT_TOPOLOGY_ENDPOINT_REF",
]
