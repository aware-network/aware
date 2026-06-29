from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Coroutine, Protocol

from aware_code_sdk.dto import (
    CodeSemanticScopePackageRef,
    ResolveCodeSemanticScopeRequest,
    ResolveCodeSemanticScopeResponse,
)


class CodeSdkSemanticScopeProvider(Protocol):
    """Synchronous semantic-scope provider for local registry consumers."""

    def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse: ...


class CodeSdkAsyncSemanticScopeProvider(Protocol):
    """Async semantic-scope provider backed by generated Code API clients."""

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse: ...


CodeSdkSemanticScopeRunner = Callable[
    [Callable[[], Coroutine[Any, Any, ResolveCodeSemanticScopeResponse]]],
    ResolveCodeSemanticScopeResponse,
]


@dataclass(frozen=True, slots=True)
class LocalCatalogCodeSdkSemanticScopeProvider:
    """Fail-closed provider for catalog-only SDK clients."""

    def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse:
        resolved_request = _semantic_scope_request(
            request=request,
            package_ref=package_ref,
            workspace_root=workspace_root,
            provider_keys=provider_keys,
            scope_keys=scope_keys,
        )
        return ResolveCodeSemanticScopeResponse(
            request_id=resolved_request.request_id,
            success=False,
            error=(
                "Catalog-backed local Code SDK cannot execute semantic scope "
                "providers; provide a service-backed Code SDK client."
            ),
            resolved=False,
            diagnostics=["semantic_scope_requires_code_service"],
            resolution_count=0,
        )


@dataclass(frozen=True, slots=True)
class GeneratedCodeSdkAsyncSemanticScopeProvider:
    """Async provider over any generated-compatible Code SDK client facade."""

    client: CodeSdkAsyncSemanticScopeProvider

    async def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse:
        resolved_request = _semantic_scope_request(
            request=request,
            package_ref=package_ref,
            workspace_root=workspace_root,
            provider_keys=provider_keys,
            scope_keys=scope_keys,
        )
        return await self.client.resolve_semantic_scope(resolved_request)


def _run_semantic_scope_blocking(
    factory: Callable[[], Coroutine[Any, Any, ResolveCodeSemanticScopeResponse]],
) -> ResolveCodeSemanticScopeResponse:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    raise RuntimeError(
        "Blocking Code SDK semantic-scope provider cannot run inside an "
        "active event loop; use async_semantic_scope_provider instead."
    )


@dataclass(frozen=True, slots=True)
class BlockingCodeSdkSemanticScopeProvider:
    """Sync bridge for local consumers that receive an async Code SDK facade."""

    async_provider: CodeSdkAsyncSemanticScopeProvider
    runner: CodeSdkSemanticScopeRunner = _run_semantic_scope_blocking

    def resolve_semantic_scope(
        self,
        request: ResolveCodeSemanticScopeRequest | None = None,
        *,
        package_ref: CodeSemanticScopePackageRef | None = None,
        workspace_root: str = ".",
        provider_keys: Sequence[str] = (),
        scope_keys: Sequence[str] = (),
    ) -> ResolveCodeSemanticScopeResponse:
        resolved_request = _semantic_scope_request(
            request=request,
            package_ref=package_ref,
            workspace_root=workspace_root,
            provider_keys=provider_keys,
            scope_keys=scope_keys,
        )
        return self.runner(
            lambda: self.async_provider.resolve_semantic_scope(resolved_request)
        )


def _semantic_scope_request(
    *,
    request: ResolveCodeSemanticScopeRequest | None,
    package_ref: CodeSemanticScopePackageRef | None,
    workspace_root: str,
    provider_keys: Sequence[str],
    scope_keys: Sequence[str],
) -> ResolveCodeSemanticScopeRequest:
    if request is not None:
        return request
    if package_ref is None:
        raise ValueError("package_ref is required.")
    return ResolveCodeSemanticScopeRequest(
        package_ref=package_ref,
        workspace_root=workspace_root,
        provider_keys=list(provider_keys),
        scope_keys=list(scope_keys),
    )


__all__ = [
    "BlockingCodeSdkSemanticScopeProvider",
    "CodeSdkAsyncSemanticScopeProvider",
    "CodeSdkSemanticScopeProvider",
    "CodeSdkSemanticScopeRunner",
    "GeneratedCodeSdkAsyncSemanticScopeProvider",
    "LocalCatalogCodeSdkSemanticScopeProvider",
]
