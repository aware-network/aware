// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'comms/models/network_service.dart' as commsModelsNetworkService_16;

class NetworkDiscoveryCapabilityClient {
  NetworkDiscoveryCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Resolve an experience-first Network territory read model from environment and hosted-service advertisements.
  Future<
    commsModelsNetworkService_16.NetworkDiscoverExperienceTerritoryResponse
  >
  discoverExperienceTerritory(
    commsModelsNetworkService_16.NetworkDiscoverExperienceTerritoryRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkDiscoverExperienceTerritoryResponse
    >(
      endpointRef: networkDiscoveryDiscoverExperienceTerritoryEndpointRef,
      discriminant: networkDiscoveryDiscoverExperienceTerritoryDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16
              .NetworkDiscoverExperienceTerritoryResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  networkDiscoveryDiscoverExperienceTerritoryEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Resolve the Control territory read model: nodes, environments, hosted services, and peers.
  Future<commsModelsNetworkService_16.NetworkDiscoverTerritoryResponse>
  discoverTerritory(
    commsModelsNetworkService_16.NetworkDiscoverTerritoryRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkDiscoverTerritoryResponse
    >(
      endpointRef: networkDiscoveryDiscoverTerritoryEndpointRef,
      discriminant: networkDiscoveryDiscoverTerritoryDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16
              .NetworkDiscoverTerritoryResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: networkDiscoveryDiscoverTerritoryEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class NetworkEnvironmentCapabilityClient {
  NetworkEnvironmentCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// List Environment advertisements known to Network Service topology truth.
  Future<commsModelsNetworkService_16.NetworkListEnvironmentsResponse> list(
    commsModelsNetworkService_16.NetworkListEnvironmentsRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkListEnvironmentsResponse
    >(
      endpointRef: networkEnvironmentListEndpointRef,
      discriminant: networkEnvironmentListDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16.NetworkListEnvironmentsResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: networkEnvironmentListEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class NetworkHostedServiceCapabilityClient {
  NetworkHostedServiceCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// List hosted Service advertisements for one NetworkNode.
  Future<commsModelsNetworkService_16.NetworkListHostedServicesResponse> list(
    commsModelsNetworkService_16.NetworkListHostedServicesRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkListHostedServicesResponse
    >(
      endpointRef: networkHostedServiceListEndpointRef,
      discriminant: networkHostedServiceListDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16
              .NetworkListHostedServicesResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: networkHostedServiceListEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class NetworkPeerCapabilityClient {
  NetworkPeerCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// List peer edges for one NetworkNode from Network Service topology truth.
  Future<commsModelsNetworkService_16.NetworkListPeersResponse> list(
    commsModelsNetworkService_16.NetworkListPeersRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkListPeersResponse
    >(
      endpointRef: networkPeerListEndpointRef,
      discriminant: networkPeerListDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16.NetworkListPeersResponse.fromJson(
            _requireJsonMap(payload, endpointRef: networkPeerListEndpointRef),
          ),
      timeout: timeout,
    );
  }

  /// Upsert one canonical NetworkNodePeer edge used for node-to-node routing.
  Future<commsModelsNetworkService_16.NetworkUpsertPeerResponse> upsert(
    commsModelsNetworkService_16.NetworkUpsertPeerRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkUpsertPeerResponse
    >(
      endpointRef: networkPeerUpsertEndpointRef,
      discriminant: networkPeerUpsertDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16.NetworkUpsertPeerResponse.fromJson(
            _requireJsonMap(payload, endpointRef: networkPeerUpsertEndpointRef),
          ),
      timeout: timeout,
    );
  }
}

class NetworkPublicationCapabilityClient {
  NetworkPublicationCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Reconcile one complete Node runtime publication through canonical Network Service authority.
  Future<commsModelsNetworkService_16.NetworkReconcileNodePublicationResponse>
  reconcileNodePublication(
    commsModelsNetworkService_16.NetworkReconcileNodePublicationRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkReconcileNodePublicationResponse
    >(
      endpointRef: networkPublicationReconcileNodePublicationEndpointRef,
      discriminant: networkPublicationReconcileNodePublicationDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16
              .NetworkReconcileNodePublicationResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef:
                  networkPublicationReconcileNodePublicationEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class NetworkRouteCapabilityClient {
  NetworkRouteCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Resolve remote hosted-Service routes for a consumer NetworkNode.
  Future<commsModelsNetworkService_16.NetworkResolveHostedServiceRoutesResponse>
  resolveHostedServiceRoutes(
    commsModelsNetworkService_16.NetworkResolveHostedServiceRoutesRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      commsModelsNetworkService_16.NetworkResolveHostedServiceRoutesResponse
    >(
      endpointRef: networkRouteResolveHostedServiceRoutesEndpointRef,
      discriminant: networkRouteResolveHostedServiceRoutesDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          commsModelsNetworkService_16
              .NetworkResolveHostedServiceRoutesResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: networkRouteResolveHostedServiceRoutesEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class NetworkApiClient {
  NetworkApiClient(AwareApiClient client)
    : discovery = NetworkDiscoveryCapabilityClient(client),
      environment = NetworkEnvironmentCapabilityClient(client),
      hostedService = NetworkHostedServiceCapabilityClient(client),
      peer = NetworkPeerCapabilityClient(client),
      publication = NetworkPublicationCapabilityClient(client),
      route = NetworkRouteCapabilityClient(client);

  final NetworkDiscoveryCapabilityClient discovery;
  final NetworkEnvironmentCapabilityClient environment;
  final NetworkHostedServiceCapabilityClient hostedService;
  final NetworkPeerCapabilityClient peer;
  final NetworkPublicationCapabilityClient publication;
  final NetworkRouteCapabilityClient route;
}

class AwareNetworkServiceApiClient {
  AwareNetworkServiceApiClient(AwareApiClient client)
    : network = NetworkApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final NetworkApiClient network;
}

Map<String, dynamic> _requireJsonMap(
  Object? payload, {
  required String endpointRef,
}) {
  if (payload is Map<String, dynamic>) {
    return payload;
  }
  if (payload is Map) {
    return Map<String, dynamic>.from(payload);
  }
  throw StateError(
    'Expected API payload for $endpointRef to decode to a JSON object.',
  );
}
