// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'code/features/package_distribution.dart'
    as codeFeaturesPackageDistribution_12;
import 'hub/artifact_authority.dart' as hubArtifactAuthority_4;
import 'hub/deployment_artifact_authority.dart'
    as hubDeploymentArtifactAuthority_2;
import 'hub/public_map_discovery.dart' as hubPublicMapDiscovery_2;

class HubArtifactCapabilityClient {
  HubArtifactCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Publish a generic immutable artifact payload lock through Hub authority truth.
  Future<hubArtifactAuthority_4.PublishHubArtifactResponse> publish(
    hubArtifactAuthority_4.PublishHubArtifactRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<hubArtifactAuthority_4.PublishHubArtifactResponse>(
          endpointRef: hubArtifactPublishEndpointRef,
          discriminant: hubArtifactPublishDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              hubArtifactAuthority_4.PublishHubArtifactResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: hubArtifactPublishEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }

  /// Resolve a generic immutable artifact payload lock through Hub authority truth.
  Future<hubArtifactAuthority_4.ResolveHubArtifactResponse> resolve(
    hubArtifactAuthority_4.ResolveHubArtifactRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<hubArtifactAuthority_4.ResolveHubArtifactResponse>(
          endpointRef: hubArtifactResolveEndpointRef,
          discriminant: hubArtifactResolveDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              hubArtifactAuthority_4.ResolveHubArtifactResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: hubArtifactResolveEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class HubCodePackageCapabilityClient {
  HubCodePackageCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Describe one CodePackage descriptor through Hub package authority truth.
  Future<codeFeaturesPackageDistribution_12.DescribeCodePackageResponse>
  describe(
    codeFeaturesPackageDistribution_12.DescribeCodePackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.DescribeCodePackageResponse
    >(
      endpointRef: hubCodePackageDescribeEndpointRef,
      discriminant: hubCodePackageDescribeDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12
              .DescribeCodePackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackageDescribeEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Discover public Hub CodePackage channel heads for pre-identity map surfaces.
  Future<
    codeFeaturesPackageDistribution_12.DiscoverCodePackageChannelHeadsResponse
  >
  discoverChannelHeads(
    codeFeaturesPackageDistribution_12.DiscoverCodePackageChannelHeadsRequest
    request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.DiscoverCodePackageChannelHeadsResponse
    >(
      endpointRef: hubCodePackageDiscoverChannelHeadsEndpointRef,
      discriminant: hubCodePackageDiscoverChannelHeadsDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12
              .DiscoverCodePackageChannelHeadsResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackageDiscoverChannelHeadsEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Return one explicit CodePackage artifact download lock through Hub package authority truth.
  Future<codeFeaturesPackageDistribution_12.DownloadCodePackageResponse>
  download(
    codeFeaturesPackageDistribution_12.DownloadCodePackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.DownloadCodePackageResponse
    >(
      endpointRef: hubCodePackageDownloadEndpointRef,
      discriminant: hubCodePackageDownloadDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12
              .DownloadCodePackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackageDownloadEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Register one staged CodePackage artifact lock into Hub package authority truth.
  Future<codeFeaturesPackageDistribution_12.PublishCodePackageResponse> publish(
    codeFeaturesPackageDistribution_12.PublishCodePackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.PublishCodePackageResponse
    >(
      endpointRef: hubCodePackagePublishEndpointRef,
      discriminant: hubCodePackagePublishDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12
              .PublishCodePackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackagePublishEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Resolve one exact CodePackage artifact lock through Hub package authority truth.
  Future<codeFeaturesPackageDistribution_12.ResolveCodePackageResponse> resolve(
    codeFeaturesPackageDistribution_12.ResolveCodePackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.ResolveCodePackageResponse
    >(
      endpointRef: hubCodePackageResolveEndpointRef,
      discriminant: hubCodePackageResolveDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12
              .ResolveCodePackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackageResolveEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Search CodePackage descriptors through Hub package authority truth.
  Future<codeFeaturesPackageDistribution_12.SearchCodePackageResponse> search(
    codeFeaturesPackageDistribution_12.SearchCodePackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      codeFeaturesPackageDistribution_12.SearchCodePackageResponse
    >(
      endpointRef: hubCodePackageSearchEndpointRef,
      discriminant: hubCodePackageSearchDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          codeFeaturesPackageDistribution_12.SearchCodePackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubCodePackageSearchEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class HubDeploymentArtifactCapabilityClient {
  HubDeploymentArtifactCapabilityClient(AwareApiClient client)
    : _client = client;

  final AwareApiClient _client;

  /// Resolve a deployment artifact payload lock through Hub authority truth.
  Future<hubDeploymentArtifactAuthority_2.ResolveDeploymentArtifactResponse>
  resolve(
    hubDeploymentArtifactAuthority_2.ResolveDeploymentArtifactRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      hubDeploymentArtifactAuthority_2.ResolveDeploymentArtifactResponse
    >(
      endpointRef: hubDeploymentArtifactResolveEndpointRef,
      discriminant: hubDeploymentArtifactResolveDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          hubDeploymentArtifactAuthority_2
              .ResolveDeploymentArtifactResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: hubDeploymentArtifactResolveEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class HubPublicMapCapabilityClient {
  HubPublicMapCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Discover the public Hub package/revision map for pre-identity Control surfaces.
  Future<hubPublicMapDiscovery_2.DiscoverPublicMapResponse> discover(
    hubPublicMapDiscovery_2.DiscoverPublicMapRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client
        .invokeApiEndpoint<hubPublicMapDiscovery_2.DiscoverPublicMapResponse>(
          endpointRef: hubPublicMapDiscoverEndpointRef,
          discriminant: hubPublicMapDiscoverDiscriminant,
          requestPayload: request.toJson(),
          decodeResponse: (payload) =>
              hubPublicMapDiscovery_2.DiscoverPublicMapResponse.fromJson(
                _requireJsonMap(
                  payload,
                  endpointRef: hubPublicMapDiscoverEndpointRef,
                ),
              ),
          timeout: timeout,
        );
  }
}

class HubApiClient {
  HubApiClient(AwareApiClient client)
    : artifact = HubArtifactCapabilityClient(client),
      codePackage = HubCodePackageCapabilityClient(client),
      deploymentArtifact = HubDeploymentArtifactCapabilityClient(client),
      publicMap = HubPublicMapCapabilityClient(client);

  final HubArtifactCapabilityClient artifact;
  final HubCodePackageCapabilityClient codePackage;
  final HubDeploymentArtifactCapabilityClient deploymentArtifact;
  final HubPublicMapCapabilityClient publicMap;
}

class AwareHubServiceApiClient {
  AwareHubServiceApiClient(AwareApiClient client) : hub = HubApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final HubApiClient hub;
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
