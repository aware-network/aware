// GENERATED CODE - DO NOT MODIFY BY HAND
// Thin typed API wrapper over package:aware_api/aware_api.dart.

import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'bindings.dart';
import 'content/content_service_operation.dart'
    as contentContentServiceOperation_6;

class ContentPackageCapabilityClient {
  ContentPackageCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Materialize a provider export document into Content-owned ContentPackage truth.
  Future<contentContentServiceOperation_6.MaterializeContentPackageResponse>
  materializeContentPackage(
    contentContentServiceOperation_6.MaterializeContentPackageRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      contentContentServiceOperation_6.MaterializeContentPackageResponse
    >(
      endpointRef: contentPackageMaterializeContentPackageEndpointRef,
      discriminant: contentPackageMaterializeContentPackageDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          contentContentServiceOperation_6
              .MaterializeContentPackageResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: contentPackageMaterializeContentPackageEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class ContentTextCapabilityClient {
  ContentTextCapabilityClient(AwareApiClient client) : _client = client;

  final AwareApiClient _client;

  /// Commit provider-neutral text as Content truth and return exact commit evidence.
  Future<contentContentServiceOperation_6.CommitContentTextResponse>
  commitContentText(
    contentContentServiceOperation_6.CommitContentTextRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      contentContentServiceOperation_6.CommitContentTextResponse
    >(
      endpointRef: contentTextCommitContentTextEndpointRef,
      discriminant: contentTextCommitContentTextDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          contentContentServiceOperation_6.CommitContentTextResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: contentTextCommitContentTextEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }

  /// Resolve one Content object into deterministic text parts and a flattened text payload.
  Future<contentContentServiceOperation_6.ResolveContentTextResponse>
  resolveContentText(
    contentContentServiceOperation_6.ResolveContentTextRequest request, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.invokeApiEndpoint<
      contentContentServiceOperation_6.ResolveContentTextResponse
    >(
      endpointRef: contentTextResolveContentTextEndpointRef,
      discriminant: contentTextResolveContentTextDiscriminant,
      requestPayload: request.toJson(),
      decodeResponse: (payload) =>
          contentContentServiceOperation_6.ResolveContentTextResponse.fromJson(
            _requireJsonMap(
              payload,
              endpointRef: contentTextResolveContentTextEndpointRef,
            ),
          ),
      timeout: timeout,
    );
  }
}

class ContentApiClient {
  ContentApiClient(AwareApiClient client)
    : package = ContentPackageCapabilityClient(client),
      text = ContentTextCapabilityClient(client);

  final ContentPackageCapabilityClient package;
  final ContentTextCapabilityClient text;
}

class AwareContentServiceApiClient {
  AwareContentServiceApiClient(AwareApiClient client)
    : content = ContentApiClient(client);

  final Map<String, Object?> interfaceSpecPayload = apiInterfaceSpecPayload;
  final Map<String, Object?> invocationManifestPayload =
      apiInvocationManifestPayload;
  final ContentApiClient content;
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
