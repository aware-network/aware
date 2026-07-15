# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API client bindings for Python SDK wrappers.
from __future__ import annotations

from typing import Final

from aware_api.interface import LoadedApiInterface, load_api_interface_spec_payload
from aware_api.invocation import LoadedApiInvocationManifest, load_api_invocation_manifest_payload

API_PACKAGE_NAME: Final[str] = "file-system-service-api"
API_FQN_PREFIX: Final[str] = "aware_file_system_service_api"

API_INTERFACE_SPEC: Final[LoadedApiInterface] = load_api_interface_spec_payload(
    {
        "apis": [
            {
                "capabilities": [
                    {
                        "endpoints": [
                            {
                                "description": "Resolve available filesystem backend "
                                "capabilities for Python, Rust, "
                                "service, and fallback routing.",
                                "discriminant": "filesystem.backend.capabilities",
                                "name": "capabilities",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "backend",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Apply a canonical filesystem delta set "
                                "under a local root with path and "
                                "digest policy receipts.",
                                "discriminant": "filesystem.delta.apply",
                                "name": "apply",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ApplyFileSystemDeltaRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ApplyFileSystemDeltaResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            },
                            {
                                "description": "Collect a canonical filesystem delta "
                                "set from a local root and optional "
                                "base snapshot.",
                                "discriminant": "filesystem.delta.collect",
                                "name": "collect",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.CollectFileSystemDeltaRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.CollectFileSystemDeltaResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            },
                        ],
                        "name": "delta",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Verify that relative paths stay inside "
                                "the declared filesystem root.",
                                "discriminant": "filesystem.root.verify",
                                "name": "verify",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.VerifyFileSystemRootRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.VerifyFileSystemRootResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "root",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "description": "Scan one filesystem root into "
                                "canonical relative-path metadata and "
                                "optional digest entries.",
                                "discriminant": "filesystem.snapshot.scan",
                                "name": "scan",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ScanFileSystemSnapshotRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ScanFileSystemSnapshotResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "snapshot",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                ],
                "name": "filesystem",
                "source_path": "bindings/filesystem.apis.aware",
            }
        ],
        "fqn_prefix": "aware_file_system_service_api",
        "package_name": "file-system-service-api",
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
                                "description": "Resolve available filesystem backend "
                                "capabilities for Python, Rust, "
                                "service, and fallback routing.",
                                "discriminant": "filesystem.backend.capabilities",
                                "endpoint_ref": "filesystem.backend.capabilities",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "capabilities",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesRequest",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ResolveFileSystemBackendCapabilitiesRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ResolveFileSystemBackendCapabilitiesResponse",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ResolveFileSystemBackendCapabilitiesResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "backend",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Apply a canonical filesystem delta set "
                                "under a local root with path and "
                                "digest policy receipts.",
                                "discriminant": "filesystem.delta.apply",
                                "endpoint_ref": "filesystem.delta.apply",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "apply",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ApplyFileSystemDeltaRequest",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ApplyFileSystemDeltaRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ApplyFileSystemDeltaResponse",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ApplyFileSystemDeltaResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            },
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Collect a canonical filesystem delta "
                                "set from a local root and optional "
                                "base snapshot.",
                                "discriminant": "filesystem.delta.collect",
                                "endpoint_ref": "filesystem.delta.collect",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "collect",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.CollectFileSystemDeltaRequest",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.CollectFileSystemDeltaRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.CollectFileSystemDeltaResponse",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.CollectFileSystemDeltaResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            },
                        ],
                        "name": "delta",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Verify that relative paths stay inside "
                                "the declared filesystem root.",
                                "discriminant": "filesystem.root.verify",
                                "endpoint_ref": "filesystem.root.verify",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "verify",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.VerifyFileSystemRootRequest",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.VerifyFileSystemRootRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.VerifyFileSystemRootResponse",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.VerifyFileSystemRootResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "root",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                    {
                        "endpoints": [
                            {
                                "addressing_strategy": "session_bound",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "description": "Scan one filesystem root into "
                                "canonical relative-path metadata and "
                                "optional digest entries.",
                                "discriminant": "filesystem.snapshot.scan",
                                "endpoint_ref": "filesystem.snapshot.scan",
                                "fulfillment_bindings": [],
                                "invocation_kind": "shared_client_endpoint",
                                "name": "scan",
                                "request": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ScanFileSystemSnapshotRequest",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ScanFileSystemSnapshotRequest",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "response": {
                                    "class_ref": "aware_file_system_service_dto.file_system.ScanFileSystemSnapshotResponse",
                                    "python_model_ref": "aware_file_system_service_dto.file_system.service_operation.ScanFileSystemSnapshotResponse",
                                    "source_path": "bindings/filesystem.apis.aware",
                                },
                                "source_path": "bindings/filesystem.apis.aware",
                            }
                        ],
                        "name": "snapshot",
                        "source_path": "bindings/filesystem.apis.aware",
                    },
                ],
                "name": "filesystem",
                "source_path": "bindings/filesystem.apis.aware",
            }
        ],
        "fqn_prefix": "aware_file_system_service_api",
        "package_name": "file-system-service-api",
        "schema_version": 1,
    }
)

FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF: Final[str] = "filesystem.backend.capabilities"
FILESYSTEM__DELTA__APPLY_ENDPOINT_REF: Final[str] = "filesystem.delta.apply"
FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF: Final[str] = "filesystem.delta.collect"
FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF: Final[str] = "filesystem.root.verify"
FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF: Final[str] = "filesystem.snapshot.scan"

ENDPOINT_REF_BY_NAME: Final[dict[str, str]] = {
    "filesystem.backend.capabilities": FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF,
    "filesystem.delta.apply": FILESYSTEM__DELTA__APPLY_ENDPOINT_REF,
    "filesystem.delta.collect": FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF,
    "filesystem.root.verify": FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF,
    "filesystem.snapshot.scan": FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF,
}

__all__ = [
    "API_FQN_PREFIX",
    "API_INTERFACE_SPEC",
    "API_INVOCATION_MANIFEST",
    "API_PACKAGE_NAME",
    "ENDPOINT_REF_BY_NAME",
    "FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF",
    "FILESYSTEM__DELTA__APPLY_ENDPOINT_REF",
    "FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF",
    "FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF",
    "FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF",
]
