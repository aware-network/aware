# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "network-service-api"
API_FQN_PREFIX: Final[str] = "aware_network_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Resolve an experience-first Network "
                                "territory read model from environment "
                                "and hosted-service advertisements.",
                                "discriminant": "network.discovery.discover_experience_territory",
                                "name": "discover_experience_territory",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                            {
                                "description": "Resolve the Control territory read "
                                "model: nodes, environments, hosted "
                                "services, and peers.",
                                "discriminant": "network.discovery.discover_territory",
                                "name": "discover_territory",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                        ],
                        "name": "discovery",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List Environment advertisements known "
                                "to Network Service topology truth.",
                                "discriminant": "network.environment.list",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "environment",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List hosted Service advertisements for " "one NetworkNode.",
                                "discriminant": "network.hosted_service.list",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "hosted_service",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "List peer edges for one NetworkNode "
                                "from Network Service topology truth.",
                                "discriminant": "network.peer.list",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                            {
                                "description": "Upsert one canonical NetworkNodePeer "
                                "edge used for node-to-node routing.",
                                "discriminant": "network.peer.upsert",
                                "name": "upsert",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                        ],
                        "name": "peer",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Reconcile one complete Node runtime "
                                "publication through canonical Network "
                                "Service authority.",
                                "discriminant": "network.publication.reconcile_node_publication",
                                "name": "reconcile_node_publication",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "publication",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve remote hosted-Service routes " "for a consumer NetworkNode.",
                                "discriminant": "network.route.resolve_hosted_service_routes",
                                "name": "resolve_hosted_service_routes",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "route",
                        "source_path": "bindings/network.apis.aware",
                    },
                ],
                "name": "network",
                "source_path": "bindings/network.apis.aware",
            }
        ],
        "fqn_prefix": "aware_network_service_api",
        "package_name": "network-service-api",
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
                                "description": "Resolve an experience-first Network "
                                "territory read model from environment "
                                "and hosted-service advertisements.",
                                "discriminant": "network.discovery.discover_experience_territory",
                                "endpoint_ref": "network.discovery.discover_experience_territory",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover_experience_territory",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkDiscoverExperienceTerritoryRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkDiscoverExperienceTerritoryResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve the Control territory read "
                                "model: nodes, environments, hosted "
                                "services, and peers.",
                                "discriminant": "network.discovery.discover_territory",
                                "endpoint_ref": "network.discovery.discover_territory",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "discover_territory",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkDiscoverTerritoryRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkDiscoverTerritoryResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                        ],
                        "name": "discovery",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List Environment advertisements known "
                                "to Network Service topology truth.",
                                "discriminant": "network.environment.list",
                                "endpoint_ref": "network.environment.list",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListEnvironmentsRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListEnvironmentsResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "environment",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List hosted Service advertisements for " "one NetworkNode.",
                                "discriminant": "network.hosted_service.list",
                                "endpoint_ref": "network.hosted_service.list",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListHostedServicesRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListHostedServicesResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "hosted_service",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "List peer edges for one NetworkNode "
                                "from Network Service topology truth.",
                                "discriminant": "network.peer.list",
                                "endpoint_ref": "network.peer.list",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "list",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListPeersRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkListPeersResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Upsert one canonical NetworkNodePeer "
                                "edge used for node-to-node routing.",
                                "discriminant": "network.peer.upsert",
                                "endpoint_ref": "network.peer.upsert",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "upsert",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkUpsertPeerRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkUpsertPeerResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            },
                        ],
                        "name": "peer",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Reconcile one complete Node runtime "
                                "publication through canonical Network "
                                "Service authority.",
                                "discriminant": "network.publication.reconcile_node_publication",
                                "endpoint_ref": "network.publication.reconcile_node_publication",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "reconcile_node_publication",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkReconcileNodePublicationRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkReconcileNodePublicationResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "publication",
                        "source_path": "bindings/network.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve remote hosted-Service routes " "for a consumer NetworkNode.",
                                "discriminant": "network.route.resolve_hosted_service_routes",
                                "endpoint_ref": "network.route.resolve_hosted_service_routes",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve_hosted_service_routes",
                                "request": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesRequest",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkResolveHostedServiceRoutesRequest",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesResponse",
                                    "python_model_ref": "aware_network_service_dto.comms.models.network_service.NetworkResolveHostedServiceRoutesResponse",
                                    "source_path": "bindings/network.apis.aware",
                                },
                                "source_path": "bindings/network.apis.aware",
                            }
                        ],
                        "name": "route",
                        "source_path": "bindings/network.apis.aware",
                    },
                ],
                "name": "network",
                "source_path": "bindings/network.apis.aware",
            }
        ],
        "fqn_prefix": "aware_network_service_api",
        "package_name": "network-service-api",
        "schema_version": 1,
    }
)

NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF: Final[str] = (
    "network.discovery.discover_experience_territory"
)
NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF: Final[str] = "network.discovery.discover_territory"
NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF: Final[str] = "network.environment.list"
NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF: Final[str] = "network.hosted_service.list"
NETWORK__PEER__LIST_ENDPOINT_REF: Final[str] = "network.peer.list"
NETWORK__PEER__UPSERT_ENDPOINT_REF: Final[str] = "network.peer.upsert"
NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF: Final[str] = (
    "network.publication.reconcile_node_publication"
)
NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF: Final[str] = "network.route.resolve_hosted_service_routes"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "network.discovery.discover_experience_territory": NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF,
    "network.discovery.discover_territory": NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF,
    "network.environment.list": NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF,
    "network.hosted_service.list": NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF,
    "network.peer.list": NETWORK__PEER__LIST_ENDPOINT_REF,
    "network.peer.upsert": NETWORK__PEER__UPSERT_ENDPOINT_REF,
    "network.publication.reconcile_node_publication": NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF,
    "network.route.resolve_hosted_service_routes": NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF",
    "NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF",
    "NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF",
    "NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF",
    "NETWORK__PEER__LIST_ENDPOINT_REF",
    "NETWORK__PEER__UPSERT_ENDPOINT_REF",
    "NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF",
    "NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF",
]
