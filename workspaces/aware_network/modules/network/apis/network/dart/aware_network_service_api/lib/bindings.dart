// GENERATED CODE - DO NOT MODIFY BY HAND
// Compiled API bindings for generated Dart SDK wrappers.

import 'dart:convert' as convert;

const String apiPackageName = "network-service-api";
const String apiFqnPrefix = "aware_network_service_api";

final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(r'''
{
  "apis": [
    {
      "capabilities": [
        {
          "endpoints": [
            {
              "description": "Resolve an experience-first Network territory read model from environment and hosted-service advertisements.",
              "discriminant": "network.discovery.discover_experience_territory",
              "name": "discover_experience_territory",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            },
            {
              "description": "Resolve the Control territory read model: nodes, environments, hosted services, and peers.",
              "discriminant": "network.discovery.discover_territory",
              "name": "discover_territory",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "discovery",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "List Environment advertisements known to Network Service topology truth.",
              "discriminant": "network.environment.list",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "environment",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "List hosted Service advertisements for one NetworkNode.",
              "discriminant": "network.hosted_service.list",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "hosted_service",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "List peer edges for one NetworkNode from Network Service topology truth.",
              "discriminant": "network.peer.list",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            },
            {
              "description": "Upsert one canonical NetworkNodePeer edge used for node-to-node routing.",
              "discriminant": "network.peer.upsert",
              "name": "upsert",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "peer",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Reconcile one complete Node runtime publication through canonical Network Service authority.",
              "discriminant": "network.publication.reconcile_node_publication",
              "name": "reconcile_node_publication",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "publication",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Resolve remote hosted-Service routes for a consumer NetworkNode.",
              "discriminant": "network.route.resolve_hosted_service_routes",
              "name": "resolve_hosted_service_routes",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "route",
          "source_path": "bindings/network.apis.aware"
        }
      ],
      "name": "network",
      "source_path": "bindings/network.apis.aware"
    }
  ],
  "fqn_prefix": "aware_network_service_api",
  "package_name": "network-service-api",
  "schema_version": 1
}
''');

final Map<String, Object?> apiInvocationManifestPayload = _decodeJsonObject(r'''
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
              "description": "Resolve an experience-first Network territory read model from environment and hosted-service advertisements.",
              "discriminant": "network.discovery.discover_experience_territory",
              "endpoint_ref": "network.discovery.discover_experience_territory",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "discover_experience_territory",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverExperienceTerritoryResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve the Control territory read model: nodes, environments, hosted services, and peers.",
              "discriminant": "network.discovery.discover_territory",
              "endpoint_ref": "network.discovery.discover_territory",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "discover_territory",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkDiscoverTerritoryResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "discovery",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "List Environment advertisements known to Network Service topology truth.",
              "discriminant": "network.environment.list",
              "endpoint_ref": "network.environment.list",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListEnvironmentsResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "environment",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "List hosted Service advertisements for one NetworkNode.",
              "discriminant": "network.hosted_service.list",
              "endpoint_ref": "network.hosted_service.list",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListHostedServicesResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "hosted_service",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "List peer edges for one NetworkNode from Network Service topology truth.",
              "discriminant": "network.peer.list",
              "endpoint_ref": "network.peer.list",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "list",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkListPeersResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Upsert one canonical NetworkNodePeer edge used for node-to-node routing.",
              "discriminant": "network.peer.upsert",
              "endpoint_ref": "network.peer.upsert",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "upsert",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkUpsertPeerResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "peer",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Reconcile one complete Node runtime publication through canonical Network Service authority.",
              "discriminant": "network.publication.reconcile_node_publication",
              "endpoint_ref": "network.publication.reconcile_node_publication",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "reconcile_node_publication",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkReconcileNodePublicationResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "publication",
          "source_path": "bindings/network.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve remote hosted-Service routes for a consumer NetworkNode.",
              "discriminant": "network.route.resolve_hosted_service_routes",
              "endpoint_ref": "network.route.resolve_hosted_service_routes",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve_hosted_service_routes",
              "request": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesRequest",
                "source_path": "bindings/network.apis.aware"
              },
              "response": {
                "class_ref": "aware_network_service_dto.comms.models.NetworkResolveHostedServiceRoutesResponse",
                "source_path": "bindings/network.apis.aware"
              },
              "source_path": "bindings/network.apis.aware"
            }
          ],
          "name": "route",
          "source_path": "bindings/network.apis.aware"
        }
      ],
      "name": "network",
      "source_path": "bindings/network.apis.aware"
    }
  ],
  "fqn_prefix": "aware_network_service_api",
  "package_name": "network-service-api",
  "schema_version": 1
}
''');

const String networkDiscoveryDiscoverExperienceTerritoryEndpointRef =
    "network.discovery.discover_experience_territory";
const String networkDiscoveryDiscoverExperienceTerritoryDiscriminant =
    "network.discovery.discover_experience_territory";
const String networkDiscoveryDiscoverTerritoryEndpointRef =
    "network.discovery.discover_territory";
const String networkDiscoveryDiscoverTerritoryDiscriminant =
    "network.discovery.discover_territory";
const String networkEnvironmentListEndpointRef = "network.environment.list";
const String networkEnvironmentListDiscriminant = "network.environment.list";
const String networkHostedServiceListEndpointRef =
    "network.hosted_service.list";
const String networkHostedServiceListDiscriminant =
    "network.hosted_service.list";
const String networkPeerListEndpointRef = "network.peer.list";
const String networkPeerListDiscriminant = "network.peer.list";
const String networkPeerUpsertEndpointRef = "network.peer.upsert";
const String networkPeerUpsertDiscriminant = "network.peer.upsert";
const String networkPublicationReconcileNodePublicationEndpointRef =
    "network.publication.reconcile_node_publication";
const String networkPublicationReconcileNodePublicationDiscriminant =
    "network.publication.reconcile_node_publication";
const String networkRouteResolveHostedServiceRoutesEndpointRef =
    "network.route.resolve_hosted_service_routes";
const String networkRouteResolveHostedServiceRoutesDiscriminant =
    "network.route.resolve_hosted_service_routes";

Map<String, Object?> _decodeJsonObject(String raw) {
  final decoded = convert.jsonDecode(raw);
  if (decoded is! Map) {
    throw StateError(
      'Expected compiled API payload to decode to a JSON object.',
    );
  }
  return Map<String, Object?>.from(decoded);
}
