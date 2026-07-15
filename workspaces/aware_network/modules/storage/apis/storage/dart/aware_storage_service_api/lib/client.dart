// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'storage/service_operation.dart' as storageServiceOperation_6;

class StorageBlobCapabilityClient {
  StorageBlobCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Describe one StorageBlob metadata record by object id.
  Future<storageServiceOperation_6.DescribeStorageBlobResponse> describe(
    storageServiceOperation_6.DescribeStorageBlobRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      storageServiceOperation_6.DescribeStorageBlobResponse
    >(
      endpointRef: storageBlobDescribeEndpointRef,
      discriminant: storageBlobDescribeDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          storageServiceOperation_6.DescribeStorageBlobResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: storageBlobDescribeEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Register commit-backed StorageBlob metadata for bytes already stored on the Storage data-plane.
  Future<storageServiceOperation_6.RegisterStorageBlobResponse> register(
    storageServiceOperation_6.RegisterStorageBlobRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      storageServiceOperation_6.RegisterStorageBlobResponse
    >(
      endpointRef: storageBlobRegisterEndpointRef,
      discriminant: storageBlobRegisterDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          storageServiceOperation_6.RegisterStorageBlobResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: storageBlobRegisterEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class StorageMediaCapabilityClient {
  StorageMediaCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Resolve one StorageBlob into renderer-safe media descriptors without embedding raw bytes.
  Future<storageServiceOperation_6.ResolveStorageMediaResponse> resolve(
    storageServiceOperation_6.ResolveStorageMediaRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      storageServiceOperation_6.ResolveStorageMediaResponse
    >(
      endpointRef: storageMediaResolveEndpointRef,
      discriminant: storageMediaResolveDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          storageServiceOperation_6.ResolveStorageMediaResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: storageMediaResolveEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class StorageApiClient {
  StorageApiClient(AwareApiClient client)
    : blob = StorageBlobCapabilityClient(client),
      media = StorageMediaCapabilityClient(client);

  final StorageBlobCapabilityClient blob;
  final StorageMediaCapabilityClient media;
}

class AwareStorageServiceApiClient {
  AwareStorageServiceApiClient(AwareApiClient client)
    : storage = StorageApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final StorageApiClient storage;
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
