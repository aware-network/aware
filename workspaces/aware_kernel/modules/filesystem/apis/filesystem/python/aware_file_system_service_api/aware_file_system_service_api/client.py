# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF,
    FILESYSTEM__DELTA__APPLY_ENDPOINT_REF,
    FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF,
    FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF,
    FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
    ApplyFileSystemDeltaResponse,
    CollectFileSystemDeltaRequest,
    CollectFileSystemDeltaResponse,
    ResolveFileSystemBackendCapabilitiesRequest,
    ResolveFileSystemBackendCapabilitiesResponse,
    ScanFileSystemSnapshotRequest,
    ScanFileSystemSnapshotResponse,
    VerifyFileSystemRootRequest,
    VerifyFileSystemRootResponse,
)


class FilesystemBackendCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def capabilities(
        self, request: ResolveFileSystemBackendCapabilitiesRequest
    ) -> ResolveFileSystemBackendCapabilitiesResponse:
        """Resolve available filesystem backend capabilities for Python, Rust, service, and fallback routing."""
        return cast(
            ResolveFileSystemBackendCapabilitiesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=FILESYSTEM__BACKEND__CAPABILITIES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class FilesystemDeltaCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def apply(self, request: ApplyFileSystemDeltaRequest) -> ApplyFileSystemDeltaResponse:
        """Apply a canonical filesystem delta set under a local root with path and digest policy receipts."""
        return cast(
            ApplyFileSystemDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=FILESYSTEM__DELTA__APPLY_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def collect(self, request: CollectFileSystemDeltaRequest) -> CollectFileSystemDeltaResponse:
        """Collect a canonical filesystem delta set from a local root and optional base snapshot."""
        return cast(
            CollectFileSystemDeltaResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=FILESYSTEM__DELTA__COLLECT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class FilesystemRootCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def verify(self, request: VerifyFileSystemRootRequest) -> VerifyFileSystemRootResponse:
        """Verify that relative paths stay inside the declared filesystem root."""
        return cast(
            VerifyFileSystemRootResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=FILESYSTEM__ROOT__VERIFY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class FilesystemSnapshotCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def scan(self, request: ScanFileSystemSnapshotRequest) -> ScanFileSystemSnapshotResponse:
        """Scan one filesystem root into canonical relative-path metadata and optional digest entries."""
        return cast(
            ScanFileSystemSnapshotResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=FILESYSTEM__SNAPSHOT__SCAN_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class FilesystemApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.backend = FilesystemBackendCapabilityClient(client)
        self.delta = FilesystemDeltaCapabilityClient(client)
        self.root = FilesystemRootCapabilityClient(client)
        self.snapshot = FilesystemSnapshotCapabilityClient(client)


class AwareFileSystemServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.filesystem = FilesystemApiClient(client)


__all__ = [
    "AwareFileSystemServiceApiClient",
    "FilesystemApiClient",
    "FilesystemBackendCapabilityClient",
    "FilesystemDeltaCapabilityClient",
    "FilesystemRootCapabilityClient",
    "FilesystemSnapshotCapabilityClient",
]
