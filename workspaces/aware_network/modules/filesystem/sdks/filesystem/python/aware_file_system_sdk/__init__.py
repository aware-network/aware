from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTS: dict[str, tuple[str, str]] = {
    "AwareFileSystemSdk": ("aware_file_system_sdk.client", "AwareFileSystemSdk"),
    "FileSystemApiNamespaceClient": (
        "aware_file_system_sdk.client",
        "FileSystemApiNamespaceClient",
    ),
    "FileSystemDeltaCapabilityClient": (
        "aware_file_system_sdk.client",
        "FileSystemDeltaCapabilityClient",
    ),
    "FileSystemGeneratedApiClient": (
        "aware_file_system_sdk.client",
        "FileSystemGeneratedApiClient",
    ),
    "FileSystemRootCapabilityClient": (
        "aware_file_system_sdk.client",
        "FileSystemRootCapabilityClient",
    ),
    "FileSystemSnapshotCapabilityClient": (
        "aware_file_system_sdk.client",
        "FileSystemSnapshotCapabilityClient",
    ),
    "build_file_system_sdk": (
        "aware_file_system_sdk.client",
        "build_file_system_sdk",
    ),
    "build_root_ref": ("aware_file_system_sdk.client", "build_root_ref"),
    "default_apply_policy": (
        "aware_file_system_sdk.client",
        "default_apply_policy",
    ),
    "DirectFileSystemRuntimeApiClient": (
        "aware_file_system_sdk.local_runtime",
        "DirectFileSystemRuntimeApiClient",
    ),
    "DirectFileSystemRuntimeApiSession": (
        "aware_file_system_sdk.local_runtime",
        "DirectFileSystemRuntimeApiSession",
    ),
    "build_direct_file_system_runtime_api_client": (
        "aware_file_system_sdk.local_runtime",
        "build_direct_file_system_runtime_api_client",
    ),
    "build_direct_file_system_runtime_api_session": (
        "aware_file_system_sdk.local_runtime",
        "build_direct_file_system_runtime_api_session",
    ),
    "FileSystemCodePackageAppliedFile": (
        "aware_file_system_sdk.code_package_delta",
        "FileSystemCodePackageAppliedFile",
    ),
    "FileSystemCodePackageApplyResult": (
        "aware_file_system_sdk.code_package_delta",
        "FileSystemCodePackageApplyResult",
    ),
    "FileSystemCodePackageDeltaClient": (
        "aware_file_system_sdk.code_package_delta",
        "FileSystemCodePackageDeltaClient",
    ),
    "FileSystemCodePackageDeltaPlan": (
        "aware_file_system_sdk.code_package_delta",
        "FileSystemCodePackageDeltaPlan",
    ),
    "build_code_package_delta_client": (
        "aware_file_system_sdk.code_package_delta",
        "build_code_package_delta_client",
    ),
    "FileSystemCodeLayoutClassificationResult": (
        "aware_file_system_sdk.code_layout",
        "FileSystemCodeLayoutClassificationResult",
    ),
    "FileSystemCodeLayoutClassifier": (
        "aware_file_system_sdk.code_layout",
        "FileSystemCodeLayoutClassifier",
    ),
    "FileSystemCodeLayoutPathClassification": (
        "aware_file_system_sdk.code_layout",
        "FileSystemCodeLayoutPathClassification",
    ),
    "FileSystemCodeLayoutPathScope": (
        "aware_file_system_sdk.code_layout",
        "FileSystemCodeLayoutPathScope",
    ),
    "build_code_layout_classifier": (
        "aware_file_system_sdk.code_layout",
        "build_code_layout_classifier",
    ),
    "classify_code_layout_paths": (
        "aware_file_system_sdk.code_layout",
        "classify_code_layout_paths",
    ),
    "FileSystemSdkError": ("aware_file_system_sdk.base", "FileSystemSdkError"),
    "normalize_relative_path": (
        "aware_file_system_sdk.base",
        "normalize_relative_path",
    ),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


__all__ = sorted(_EXPORTS)
