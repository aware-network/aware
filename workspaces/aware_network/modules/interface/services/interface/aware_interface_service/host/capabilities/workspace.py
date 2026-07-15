from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Protocol

from aware_interface import InterfaceHostCapabilitySnapshot
from aware_interface_service.models import (
    InterfaceHostServiceSelectedSemanticPackageState,
    InterfaceHostServiceSelectedWorkspaceState,
    InterfaceHostServiceWorkspaceCandidate,
    InterfaceHostServiceWorkspaceDiscoveryState,
    InterfaceHostServiceWorkspaceLifecycleState,
    InterfaceHostServiceWorkspaceSemanticSourceState,
)


SEMANTIC_PREVIEW_LOAD_TIMEOUT_S = 5.0
SEMANTIC_SOURCE_LOAD_TIMEOUT_S = 120.0


class WorkspaceClientProvider(Protocol):
    async def invoke_with_client(
        self,
        *,
        repository_root: Path,
        invoke: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class InterfaceHostWorkspaceRefreshResult:
    workspace_registry: object | None
    workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState
    selected_workspace_root: Path | None
    joined_workspace_root: Path | None
    selected_workspace: InterfaceHostServiceSelectedWorkspaceState | None
    selected_workspace_semantic_source_root: Path | None
    selected_workspace_semantic_source: InterfaceHostServiceWorkspaceSemanticSourceState | None
    selected_workspace_semantic_source_invocation_id: str | None
    selected_semantic_package_selector: str | None
    selected_semantic_package_selector_explicit: bool
    selected_semantic_package: InterfaceHostServiceSelectedSemanticPackageState | None


@dataclass(frozen=True, slots=True)
class InProcessWorkspaceClientProvider:
    implementation_toml_paths: tuple[Path, ...] = ()
    request_timeout_s: float = SEMANTIC_SOURCE_LOAD_TIMEOUT_S
    host_build_timeout_s: float = 60.0

    async def invoke_with_client(
        self,
        *,
        repository_root: Path,
        invoke: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        _ = repository_root, invoke
        _raise_removed_workspace_capability()


@dataclass(frozen=True, slots=True)
class LocalServiceHostWorkspaceClientProvider:
    local_runtime: object
    request_timeout_s: float = SEMANTIC_SOURCE_LOAD_TIMEOUT_S

    async def invoke_with_client(
        self,
        *,
        repository_root: Path,
        invoke: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        _ = repository_root, invoke
        _raise_removed_workspace_capability()


@dataclass(frozen=True, slots=True)
class TransportSessionWorkspaceClientProvider:
    transport_session: object

    async def invoke_with_client(
        self,
        *,
        repository_root: Path,
        invoke: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        _ = repository_root, invoke
        _raise_removed_workspace_capability()


def _raise_removed_workspace_capability() -> NoReturn:
    raise RuntimeError(
        "Workspace control-plane capability is not part of the generic InterfaceHost. "
        "Mount the Workspace interface/pane package and invoke its declared API or "
        "SDK operation instead."
    )


def build_workspace_capability_snapshot(
    *,
    workspace_discovery: InterfaceHostServiceWorkspaceDiscoveryState | None,
    selected_workspace: InterfaceHostServiceSelectedWorkspaceState | None,
) -> InterfaceHostCapabilitySnapshot | None:
    _ = workspace_discovery, selected_workspace
    return None


def workspace_label(registry: object) -> str:
    _ = registry
    _raise_removed_workspace_capability()


def workspace_summary(*, registry: object) -> str:
    _ = registry
    _raise_removed_workspace_capability()


def workspace_candidate_from_registry(
    registry: object,
) -> InterfaceHostServiceWorkspaceCandidate:
    _ = registry
    _raise_removed_workspace_capability()


def selected_workspace_state_from_candidate(
    candidate: InterfaceHostServiceWorkspaceCandidate,
    *,
    semantic_source: InterfaceHostServiceWorkspaceSemanticSourceState | None = None,
) -> InterfaceHostServiceSelectedWorkspaceState:
    _ = candidate, semantic_source
    _raise_removed_workspace_capability()


def derive_workspace_lifecycle_state(
    *,
    candidate: InterfaceHostServiceWorkspaceCandidate,
    joined_workspace_root: Path | None,
    attached_namespace_counts_by_workspace: object,
    local_service_host: object,
    local_node_runtime: object,
    hosted_services: object,
) -> InterfaceHostServiceWorkspaceLifecycleState:
    _ = (
        candidate,
        joined_workspace_root,
        attached_namespace_counts_by_workspace,
        local_service_host,
        local_node_runtime,
        hosted_services,
    )
    _raise_removed_workspace_capability()


def load_workspace_registry(
    *,
    workspace_root: Path,
    cached: object | None,
) -> object | None:
    _ = workspace_root, cached
    return None


async def load_workspace_semantic_source_via_service(
    *,
    repository_root: Path,
    workspace_root: Path,
    workspace_client_provider: WorkspaceClientProvider | None = None,
) -> object:
    _ = repository_root, workspace_root, workspace_client_provider
    _raise_removed_workspace_capability()


async def read_workspace_semantic_object_config_graph_via_service(
    *,
    repository_root: Path,
    workspace_root: Path,
    selector_key: str,
    workspace_client_provider: WorkspaceClientProvider | None = None,
) -> object:
    _ = repository_root, workspace_root, selector_key, workspace_client_provider
    _raise_removed_workspace_capability()


async def load_workspace_semantic_source(
    *,
    repository_root: Path,
    registry: object,
    workspace_client_provider: WorkspaceClientProvider | None = None,
) -> InterfaceHostServiceWorkspaceSemanticSourceState:
    _ = repository_root, registry, workspace_client_provider
    _raise_removed_workspace_capability()


async def load_selected_workspace_semantic_package_state(
    *,
    repository_root: Path,
    registry: object,
    semantic_source: InterfaceHostServiceWorkspaceSemanticSourceState,
    selector_key: str | None,
    selector_explicit: bool,
    workspace_client_provider: WorkspaceClientProvider | None = None,
) -> InterfaceHostServiceSelectedSemanticPackageState | None:
    _ = (
        repository_root,
        registry,
        semantic_source,
        selector_key,
        selector_explicit,
        workspace_client_provider,
    )
    _raise_removed_workspace_capability()


async def refresh_workspace_entry_state(
    *,
    repository_root: Path,
    cached_registry: object | None,
    selected_workspace_root: Path | None,
    joined_workspace_root: Path | None,
    selected_semantic_package_selector: str | None,
    selected_semantic_package_selector_explicit: bool,
    lifecycle_resolver: object,
    registry_loader: object,
    semantic_source_loader: object,
    semantic_package_loader: object,
) -> InterfaceHostWorkspaceRefreshResult:
    _ = (
        repository_root,
        cached_registry,
        selected_workspace_root,
        joined_workspace_root,
        selected_semantic_package_selector,
        selected_semantic_package_selector_explicit,
        lifecycle_resolver,
        registry_loader,
        semantic_source_loader,
        semantic_package_loader,
    )
    return InterfaceHostWorkspaceRefreshResult(
        workspace_registry=None,
        workspace_discovery=InterfaceHostServiceWorkspaceDiscoveryState(
            error=(
                "Workspace discovery is not part of the generic InterfaceHost. "
                "Mount the Workspace interface package to use Workspace features."
            ),
            candidates=(),
        ),
        selected_workspace_root=None,
        joined_workspace_root=None,
        selected_workspace=None,
        selected_workspace_semantic_source_root=None,
        selected_workspace_semantic_source=None,
        selected_workspace_semantic_source_invocation_id=None,
        selected_semantic_package_selector=None,
        selected_semantic_package_selector_explicit=False,
        selected_semantic_package=None,
    )


async def _invoke_workspace_service_api(
    *,
    repository_root: Path,
    workspace_client_provider: WorkspaceClientProvider | None = None,
    invoke: Callable[[Any], Awaitable[Any]],
) -> Any:
    _ = repository_root, workspace_client_provider, invoke
    _raise_removed_workspace_capability()


__all__ = [
    "InterfaceHostWorkspaceRefreshResult",
    "InProcessWorkspaceClientProvider",
    "LocalServiceHostWorkspaceClientProvider",
    "SEMANTIC_PREVIEW_LOAD_TIMEOUT_S",
    "SEMANTIC_SOURCE_LOAD_TIMEOUT_S",
    "TransportSessionWorkspaceClientProvider",
    "WorkspaceClientProvider",
    "_invoke_workspace_service_api",
    "build_workspace_capability_snapshot",
    "derive_workspace_lifecycle_state",
    "load_selected_workspace_semantic_package_state",
    "load_workspace_registry",
    "load_workspace_semantic_source",
    "load_workspace_semantic_source_via_service",
    "read_workspace_semantic_object_config_graph_via_service",
    "refresh_workspace_entry_state",
    "selected_workspace_state_from_candidate",
    "workspace_candidate_from_registry",
    "workspace_label",
    "workspace_summary",
]
