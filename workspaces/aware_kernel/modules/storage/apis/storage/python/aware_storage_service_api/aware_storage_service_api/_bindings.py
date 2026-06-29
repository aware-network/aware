# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "storage-service-api"
API_FQN_PREFIX: Final[str] = "aware_storage_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Describe one StorageBlob metadata " "record by object id.",
                                "discriminant": "storage.blob.describe",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            },
                            {
                                "description": "Register commit-backed StorageBlob "
                                "metadata for bytes already stored on "
                                "the Storage data-plane.",
                                "discriminant": "storage.blob.register",
                                "name": "register",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            },
                        ],
                        "name": "blob",
                        "source_path": "bindings/storage.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Resolve one StorageBlob into "
                                "renderer-safe media descriptors "
                                "without embedding raw bytes.",
                                "discriminant": "storage.media.resolve",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            }
                        ],
                        "name": "media",
                        "source_path": "bindings/storage.apis.aware",
                    },
                ],
                "name": "storage",
                "source_path": "bindings/storage.apis.aware",
            }
        ],
        "fqn_prefix": "aware_storage_service_api",
        "package_name": "storage-service-api",
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
                                "description": "Describe one StorageBlob metadata " "record by object id.",
                                "discriminant": "storage.blob.describe",
                                "endpoint_ref": "storage.blob.describe",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "describe",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobRequest",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.DescribeStorageBlobRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.DescribeStorageBlobResponse",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.DescribeStorageBlobResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Register commit-backed StorageBlob "
                                "metadata for bytes already stored on "
                                "the Storage data-plane.",
                                "discriminant": "storage.blob.register",
                                "endpoint_ref": "storage.blob.register",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "register",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobRequest",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.RegisterStorageBlobRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.RegisterStorageBlobResponse",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.RegisterStorageBlobResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            },
                        ],
                        "name": "blob",
                        "source_path": "bindings/storage.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Resolve one StorageBlob into "
                                "renderer-safe media descriptors "
                                "without embedding raw bytes.",
                                "discriminant": "storage.media.resolve",
                                "endpoint_ref": "storage.media.resolve",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "resolve",
                                "request": {
                                    "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaRequest",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.ResolveStorageMediaRequest",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_storage_service_dto.storage.ResolveStorageMediaResponse",
                                    "python_model_ref": "aware_storage_service_dto.storage.service_operation.ResolveStorageMediaResponse",
                                    "source_path": "bindings/storage.apis.aware",
                                },
                                "source_path": "bindings/storage.apis.aware",
                            }
                        ],
                        "name": "media",
                        "source_path": "bindings/storage.apis.aware",
                    },
                ],
                "name": "storage",
                "source_path": "bindings/storage.apis.aware",
            }
        ],
        "fqn_prefix": "aware_storage_service_api",
        "package_name": "storage-service-api",
        "schema_version": 1,
    }
)

STORAGE__BLOB__DESCRIBE_ENDPOINT_REF: Final[str] = "storage.blob.describe"
STORAGE__BLOB__REGISTER_ENDPOINT_REF: Final[str] = "storage.blob.register"
STORAGE__MEDIA__RESOLVE_ENDPOINT_REF: Final[str] = "storage.media.resolve"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "storage.blob.describe": STORAGE__BLOB__DESCRIBE_ENDPOINT_REF,
    "storage.blob.register": STORAGE__BLOB__REGISTER_ENDPOINT_REF,
    "storage.media.resolve": STORAGE__MEDIA__RESOLVE_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "STORAGE__BLOB__DESCRIBE_ENDPOINT_REF",
    "STORAGE__BLOB__REGISTER_ENDPOINT_REF",
    "STORAGE__MEDIA__RESOLVE_ENDPOINT_REF",
]
