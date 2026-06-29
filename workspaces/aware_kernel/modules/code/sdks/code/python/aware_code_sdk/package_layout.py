from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Coroutine, Protocol

from aware_code_sdk.dto import (
    CodePackageLayoutContract,
    CodeSourceOwnershipPackageBinding,
    DiscoverCodePackageLayoutsRequest,
    DiscoverCodePackageLayoutsResponse,
)

from aware_code_sdk.local_semantic_contract import CodeSdkSemanticContractCatalog


@dataclass(frozen=True, slots=True)
class CodeSdkDiscoveryFile:
    """One observed workspace-relative file for Code-owned package discovery."""

    relative_path: str
    file_content: str = ""
    language: str | None = None


class CodeSdkPackageLayoutProvider(Protocol):
    """Synchronous package-layout provider for local Workspace consumers."""

    def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse: ...

    def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse: ...


class CodeSdkAsyncPackageLayoutProvider(Protocol):
    """Async package-layout provider backed by generated Code API clients."""

    async def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse: ...

    async def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse: ...


CodeSdkPackageLayoutRunner = Callable[
    [Callable[[], Coroutine[Any, Any, DiscoverCodePackageLayoutsResponse]]],
    DiscoverCodePackageLayoutsResponse,
]


@dataclass(frozen=True, slots=True)
class LocalCatalogCodeSdkPackageLayoutProvider:
    """Synchronous provider over an SDK-owned package layout catalog."""

    catalog: CodeSdkSemanticContractCatalog

    def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        resolved_request = _package_layout_request(
            request=request,
            workspace_root=workspace_root,
            manifest_paths=manifest_paths,
        )
        layout_contracts, diagnostics = self.catalog.discover_layout_contracts(
            manifest_paths=resolved_request.manifest_paths,
        )
        return DiscoverCodePackageLayoutsResponse(
            request_id=resolved_request.request_id,
            success=not diagnostics,
            layout_contracts=list(layout_contracts),
            diagnostics=list(diagnostics),
        )

    def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        _ = (workspace_root, files)
        return DiscoverCodePackageLayoutsResponse(
            success=True,
            layout_contracts=[],
            diagnostics=[],
        )


@dataclass(frozen=True, slots=True)
class GeneratedCodeSdkAsyncPackageLayoutProvider:
    """Async provider over any generated-compatible Code SDK client facade."""

    client: CodeSdkAsyncPackageLayoutProvider

    async def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        resolved_request = _package_layout_request(
            request=request,
            workspace_root=workspace_root,
            manifest_paths=manifest_paths,
        )
        return await self.client.discover_package_layouts(resolved_request)

    async def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        return await self.client.discover_package_layouts_for_files(
            workspace_root=workspace_root,
            files=files,
        )


def _run_package_layout_blocking(
    factory: Callable[[], Coroutine[Any, Any, DiscoverCodePackageLayoutsResponse]],
) -> DiscoverCodePackageLayoutsResponse:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    raise RuntimeError(
        "Blocking Code SDK package-layout provider cannot run inside an "
        "active event loop; use async_package_layout_provider instead."
    )


@dataclass(frozen=True, slots=True)
class BlockingCodeSdkPackageLayoutProvider:
    """Sync bridge for local consumers that receive an async Code SDK facade."""

    async_provider: CodeSdkAsyncPackageLayoutProvider
    runner: CodeSdkPackageLayoutRunner = _run_package_layout_blocking

    def discover_package_layouts(
        self,
        request: DiscoverCodePackageLayoutsRequest | None = None,
        *,
        workspace_root: str = ".",
        manifest_paths: tuple[str, ...] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        resolved_request = _package_layout_request(
            request=request,
            workspace_root=workspace_root,
            manifest_paths=manifest_paths,
        )
        return self.runner(
            lambda: self.async_provider.discover_package_layouts(resolved_request)
        )

    def discover_package_layouts_for_files(
        self,
        *,
        workspace_root: str = ".",
        files: Sequence[CodeSdkDiscoveryFile] = (),
    ) -> DiscoverCodePackageLayoutsResponse:
        return self.runner(
            lambda: self.async_provider.discover_package_layouts_for_files(
                workspace_root=workspace_root,
                files=files,
            )
        )


def source_ownership_package_binding_from_layout_contract(
    layout_contract: CodePackageLayoutContract,
) -> CodeSourceOwnershipPackageBinding:
    metadata = layout_contract.metadata or {}
    return CodeSourceOwnershipPackageBinding(
        package_name=layout_contract.package_name or layout_contract.package_root,
        package_root=layout_contract.package_root,
        sources_root=layout_contract.sources_root,
        manifest_relative_path=layout_contract.manifest_relative_path,
        language=_metadata_string(metadata, "language"),
        surface=layout_contract.surface,
        manifest_kind=_metadata_string(metadata, "manifest_kind"),
        generated_roots=list(layout_contract.generated_roots),
        owned_file_paths=_metadata_string_list(metadata, "owned_file_paths"),
        metadata=layout_contract.metadata,
    )


def source_ownership_package_bindings_from_layout_contracts(
    layout_contracts: tuple[CodePackageLayoutContract, ...],
) -> tuple[CodeSourceOwnershipPackageBinding, ...]:
    return tuple(
        source_ownership_package_binding_from_layout_contract(layout_contract)
        for layout_contract in layout_contracts
    )


def _package_layout_request(
    *,
    request: DiscoverCodePackageLayoutsRequest | None,
    workspace_root: str,
    manifest_paths: tuple[str, ...],
) -> DiscoverCodePackageLayoutsRequest:
    if request is not None:
        return request
    return DiscoverCodePackageLayoutsRequest(
        workspace_root=workspace_root,
        manifest_paths=list(manifest_paths),
    )


def _metadata_string(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _metadata_string_list(metadata: dict[str, object], key: str) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


__all__ = [
    "BlockingCodeSdkPackageLayoutProvider",
    "CodeSdkAsyncPackageLayoutProvider",
    "CodeSdkDiscoveryFile",
    "CodeSdkPackageLayoutProvider",
    "CodeSdkPackageLayoutRunner",
    "GeneratedCodeSdkAsyncPackageLayoutProvider",
    "LocalCatalogCodeSdkPackageLayoutProvider",
    "source_ownership_package_binding_from_layout_contract",
    "source_ownership_package_bindings_from_layout_contracts",
]
