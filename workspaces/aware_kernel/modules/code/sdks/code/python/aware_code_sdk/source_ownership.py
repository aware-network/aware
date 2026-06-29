from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Coroutine, Protocol

from aware_code_sdk.dto import (
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipRequest,
)


class CodeSdkSourceOwnershipProvider(Protocol):
    """Synchronous source-ownership provider for local Workspace consumers."""

    def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse: ...


class CodeSdkAsyncSourceOwnershipProvider(Protocol):
    """Async source-ownership provider backed by generated Code API clients."""

    async def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse: ...


CodeSdkSourceOwnershipRunner = Callable[
    [Callable[[], Coroutine[Any, Any, ClassifyCodeSourceOwnershipResponse]]],
    ClassifyCodeSourceOwnershipResponse,
]


@dataclass(frozen=True, slots=True)
class GeneratedCodeSdkAsyncSourceOwnershipProvider:
    """Async provider over any generated-compatible Code SDK client facade."""

    client: CodeSdkAsyncSourceOwnershipProvider

    async def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse:
        resolved_request = _source_ownership_request(
            request=request,
            workspace_root=workspace_root,
            package_bindings=package_bindings,
            observed_paths=observed_paths,
            strict=strict,
        )
        return await self.client.classify_source_ownership(resolved_request)


def _run_source_ownership_blocking(
    factory: Callable[[], Coroutine[Any, Any, ClassifyCodeSourceOwnershipResponse]],
) -> ClassifyCodeSourceOwnershipResponse:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    raise RuntimeError(
        "Blocking Code SDK source-ownership provider cannot run inside an "
        "active event loop; use async_source_ownership_provider instead."
    )


@dataclass(frozen=True, slots=True)
class BlockingCodeSdkSourceOwnershipProvider:
    """Sync bridge for local consumers that receive an async Code SDK facade."""

    async_provider: CodeSdkAsyncSourceOwnershipProvider
    runner: CodeSdkSourceOwnershipRunner = _run_source_ownership_blocking

    def classify_source_ownership(
        self,
        request: ClassifyCodeSourceOwnershipRequest | None = None,
        *,
        workspace_root: str | None = None,
        package_bindings: Sequence[CodeSourceOwnershipPackageBinding] = (),
        observed_paths: Sequence[CodeSourceOwnershipObservedPath] = (),
        strict: bool = True,
    ) -> ClassifyCodeSourceOwnershipResponse:
        resolved_request = _source_ownership_request(
            request=request,
            workspace_root=workspace_root,
            package_bindings=package_bindings,
            observed_paths=observed_paths,
            strict=strict,
        )
        return self.runner(
            lambda: self.async_provider.classify_source_ownership(resolved_request)
        )


def _source_ownership_request(
    *,
    request: ClassifyCodeSourceOwnershipRequest | None,
    workspace_root: str | None,
    package_bindings: Sequence[CodeSourceOwnershipPackageBinding],
    observed_paths: Sequence[CodeSourceOwnershipObservedPath],
    strict: bool,
) -> ClassifyCodeSourceOwnershipRequest:
    if request is not None:
        return request
    return ClassifyCodeSourceOwnershipRequest(
        ownership_request=CodeSourceOwnershipRequest(
            workspace_root=workspace_root,
            package_bindings=list(package_bindings),
            observed_paths=list(observed_paths),
            strict=strict,
        )
    )


__all__ = [
    "BlockingCodeSdkSourceOwnershipProvider",
    "CodeSdkAsyncSourceOwnershipProvider",
    "CodeSdkSourceOwnershipProvider",
    "CodeSdkSourceOwnershipRunner",
    "GeneratedCodeSdkAsyncSourceOwnershipProvider",
]
