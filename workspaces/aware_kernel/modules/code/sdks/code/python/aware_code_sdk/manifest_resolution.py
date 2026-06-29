from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Coroutine, Protocol

from aware_code_sdk.dto import (
    CodeSemanticManifestResolutionMatch,
    FindCodeSemanticManifestResolutionRequest,
    FindCodeSemanticManifestResolutionResponse,
)

from aware_code_sdk.local_semantic_contract import CodeSdkSemanticContractCatalog


class CodeSdkManifestResolutionProvider(Protocol):
    """Synchronous manifest-resolution provider for local registry consumers."""

    def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse: ...


class CodeSdkAsyncManifestResolutionProvider(Protocol):
    """Async manifest-resolution provider backed by generated Code API clients."""

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse: ...


CodeSdkManifestResolutionRunner = Callable[
    [Callable[[], Coroutine[Any, Any, FindCodeSemanticManifestResolutionResponse]]],
    FindCodeSemanticManifestResolutionResponse,
]


@dataclass(frozen=True, slots=True)
class LocalCatalogCodeSdkManifestResolutionProvider:
    """Synchronous provider over an SDK-owned semantic contract catalog."""

    catalog: CodeSdkSemanticContractCatalog

    def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse:
        resolved_request = _manifest_resolution_request(
            request=request,
            provider_key=provider_key,
            manifest_kind=manifest_kind,
            filename=filename,
            workspace_manifest_kind=workspace_manifest_kind,
        )
        return FindCodeSemanticManifestResolutionResponse(
            request_id=resolved_request.request_id,
            success=True,
            matches=[
                CodeSemanticManifestResolutionMatch(
                    provider_key=match.provider_key,
                    semantic_contract=match.semantic_contract,
                    manifest_resolution=match.manifest_resolution,
                    semantic_contract_module=match.semantic_contract_module,
                )
                for match in self.catalog.matching_manifest_resolution(
                    provider_key=resolved_request.provider_key,
                    manifest_kind=resolved_request.manifest_kind,
                    filename=resolved_request.filename,
                    workspace_manifest_kind=resolved_request.workspace_manifest_kind,
                )
            ],
        )


@dataclass(frozen=True, slots=True)
class GeneratedCodeSdkAsyncManifestResolutionProvider:
    """Async provider over any generated-compatible Code SDK client facade."""

    client: CodeSdkAsyncManifestResolutionProvider

    async def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse:
        resolved_request = _manifest_resolution_request(
            request=request,
            provider_key=provider_key,
            manifest_kind=manifest_kind,
            filename=filename,
            workspace_manifest_kind=workspace_manifest_kind,
        )
        return await self.client.find_manifest_resolution(resolved_request)


def _run_manifest_resolution_blocking(
    factory: Callable[[], Coroutine[Any, Any, FindCodeSemanticManifestResolutionResponse]],
) -> FindCodeSemanticManifestResolutionResponse:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    raise RuntimeError(
        "Blocking Code SDK manifest-resolution provider cannot run inside an "
        "active event loop; use async_manifest_resolution_provider instead."
    )


@dataclass(frozen=True, slots=True)
class BlockingCodeSdkManifestResolutionProvider:
    """Sync bridge for local consumers that receive an async Code SDK facade."""

    async_provider: CodeSdkAsyncManifestResolutionProvider
    runner: CodeSdkManifestResolutionRunner = _run_manifest_resolution_blocking

    def find_manifest_resolution(
        self,
        request: FindCodeSemanticManifestResolutionRequest | None = None,
        *,
        provider_key: str | None = None,
        manifest_kind: str | None = None,
        filename: str | None = None,
        workspace_manifest_kind: str | None = None,
    ) -> FindCodeSemanticManifestResolutionResponse:
        resolved_request = _manifest_resolution_request(
            request=request,
            provider_key=provider_key,
            manifest_kind=manifest_kind,
            filename=filename,
            workspace_manifest_kind=workspace_manifest_kind,
        )
        return self.runner(
            lambda: self.async_provider.find_manifest_resolution(resolved_request)
        )


def _manifest_resolution_request(
    *,
    request: FindCodeSemanticManifestResolutionRequest | None,
    provider_key: str | None,
    manifest_kind: str | None,
    filename: str | None,
    workspace_manifest_kind: str | None,
) -> FindCodeSemanticManifestResolutionRequest:
    if request is not None:
        return request
    return FindCodeSemanticManifestResolutionRequest(
        provider_key=provider_key,
        manifest_kind=manifest_kind,
        filename=filename,
        workspace_manifest_kind=workspace_manifest_kind,
    )


__all__ = [
    "BlockingCodeSdkManifestResolutionProvider",
    "CodeSdkAsyncManifestResolutionProvider",
    "CodeSdkManifestResolutionProvider",
    "CodeSdkManifestResolutionRunner",
    "GeneratedCodeSdkAsyncManifestResolutionProvider",
    "LocalCatalogCodeSdkManifestResolutionProvider",
]
