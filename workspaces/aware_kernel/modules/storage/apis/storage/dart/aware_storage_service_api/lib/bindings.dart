// GENERATED CODE - DO NOT MODIFY BY HAND
// Compiled API bindings for generated Dart SDK wrappers.

import 'dart:convert' as convert;

const String apiPackageName = "storage-service-api";
const String apiFqnPrefix = "aware_storage_service_api";

final Map<String, Object?> apiInterfaceSpecPayload = _decodeJsonObject(r'''
{
  "apis": [
    {
      "capabilities": [
        {
          "endpoints": [
            {
              "description": "Describe one StorageBlob metadata record by object id.",
              "discriminant": "storage.blob.describe",
              "name": "describe",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            },
            {
              "description": "Register commit-backed StorageBlob metadata for bytes already stored on the Storage data-plane.",
              "discriminant": "storage.blob.register",
              "name": "register",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            }
          ],
          "name": "blob",
          "source_path": "bindings/storage.apis.aware"
        },
        {
          "endpoints": [
            {
              "description": "Resolve one StorageBlob into renderer-safe media descriptors without embedding raw bytes.",
              "discriminant": "storage.media.resolve",
              "name": "resolve",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            }
          ],
          "name": "media",
          "source_path": "bindings/storage.apis.aware"
        }
      ],
      "name": "storage",
      "source_path": "bindings/storage.apis.aware"
    }
  ],
  "fqn_prefix": "aware_storage_service_api",
  "package_name": "storage-service-api",
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
              "description": "Describe one StorageBlob metadata record by object id.",
              "discriminant": "storage.blob.describe",
              "endpoint_ref": "storage.blob.describe",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "describe",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            },
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Register commit-backed StorageBlob metadata for bytes already stored on the Storage data-plane.",
              "discriminant": "storage.blob.register",
              "endpoint_ref": "storage.blob.register",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "register",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            }
          ],
          "name": "blob",
          "source_path": "bindings/storage.apis.aware"
        },
        {
          "endpoints": [
            {
              "addressing_strategy": "session_bound",
              "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
              "client_operation": "invoke_api_endpoint",
              "description": "Resolve one StorageBlob into renderer-safe media descriptors without embedding raw bytes.",
              "discriminant": "storage.media.resolve",
              "endpoint_ref": "storage.media.resolve",
              "fulfillment_bindings": [],
              "invocation_kind": "shared_client_endpoint",
              "name": "resolve",
              "request": {
                "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaRequest",
                "source_path": "bindings/storage.apis.aware"
              },
              "response": {
                "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaResponse",
                "source_path": "bindings/storage.apis.aware"
              },
              "source_path": "bindings/storage.apis.aware"
            }
          ],
          "name": "media",
          "source_path": "bindings/storage.apis.aware"
        }
      ],
      "name": "storage",
      "source_path": "bindings/storage.apis.aware"
    }
  ],
  "fqn_prefix": "aware_storage_service_api",
  "package_name": "storage-service-api",
  "schema_version": 1
}
''');

const String storageBlobDescribeEndpointRef = "storage.blob.describe";
const String storageBlobDescribeDiscriminant = "storage.blob.describe";
const String storageBlobRegisterEndpointRef = "storage.blob.register";
const String storageBlobRegisterDiscriminant = "storage.blob.register";
const String storageMediaResolveEndpointRef = "storage.media.resolve";
const String storageMediaResolveDiscriminant = "storage.media.resolve";

Map<String, Object?> _decodeJsonObject(String raw) {
  final decoded = convert.jsonDecode(raw);
  if (decoded is! Map) {
    throw StateError(
      'Expected compiled API payload to decode to a JSON object.',
    );
  }
  return Map<String, Object?>.from(decoded);
}
