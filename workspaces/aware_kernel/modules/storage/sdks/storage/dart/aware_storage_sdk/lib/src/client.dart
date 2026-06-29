import 'package:aware_api/aware_api.dart';
import 'package:aware_storage_service_api/aware_storage_service_api.dart';
import 'package:uuid/uuid.dart';

class StorageSdkError extends StateError {
  StorageSdkError(String message) : super(message);
}

class StorageSdkClient {
  StorageSdkClient({required AwareStorageServiceApiClient serviceClient})
    : _serviceClient = serviceClient;

  factory StorageSdkClient.fromApiClient(AwareApiClient apiClient) {
    return StorageSdkClient(
      serviceClient: AwareStorageServiceApiClient(apiClient),
    );
  }

  final AwareStorageServiceApiClient _serviceClient;

  AwareStorageServiceApiClient get serviceClient => _serviceClient;

  Future<RegisterStorageBlobResponse> registerBlob({
    required String sha,
    required String mimeType,
    required int sizeBytes,
    UuidValue? objectId,
    UuidValue? actorId,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _serviceClient.storage.blob.register(
      StorageServiceRequest.registerBlob(
            actorId: actorId,
            objectId: objectId,
            sha: sha,
            mimeType: mimeType,
            sizeBytes: sizeBytes,
          )
          as RegisterStorageBlobRequest,
      timeout: timeout,
    );
    _raiseIfFailed(response, operation: 'register_blob');
    return response;
  }

  Future<DescribeStorageBlobResponse> describeBlob({
    required UuidValue objectId,
    UuidValue? actorId,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _serviceClient.storage.blob.describe(
      StorageServiceRequest.describeBlob(actorId: actorId, objectId: objectId)
          as DescribeStorageBlobRequest,
      timeout: timeout,
    );
    _raiseIfFailed(response, operation: 'describe_blob');
    return response;
  }

  Future<ResolveStorageMediaResponse> resolveMedia({
    required StorageMediaRef mediaRef,
    UuidValue? actorId,
    bool includeHttpUrl = true,
    String? preferredUriScheme,
    String? filename,
    StorageMediaDisposition disposition = StorageMediaDisposition.inline,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _serviceClient.storage.media.resolve(
      StorageServiceRequest.resolveMedia(
            actorId: actorId,
            mediaRef: mediaRef,
            requireOwnership: false,
            includeHttpUrl: includeHttpUrl,
            preferredUriScheme: preferredUriScheme,
            filename: filename,
            disposition: disposition,
          )
          as ResolveStorageMediaRequest,
      timeout: timeout,
    );
    _raiseIfFailed(response, operation: 'resolve_media');
    if (response.resolution == null) {
      throw StorageSdkError(
        'Storage media resolution response is missing resolution.',
      );
    }
    return response;
  }
}

void _raiseIfFailed(
  StorageServiceResponse response, {
  required String operation,
}) {
  if (response.success) {
    return;
  }
  throw StorageSdkError(response.error ?? 'Storage SDK $operation failed.');
}
