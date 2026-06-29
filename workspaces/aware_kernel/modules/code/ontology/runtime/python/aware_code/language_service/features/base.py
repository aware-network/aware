from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Protocol

from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor as CapabilityProviderDescriptor,
)
from aware_code.package.semantic_binding import (
    package_semantic_contract_provider_map,
    package_semantic_binding_provider_map,
)

from aware_code.language_service.capability_scope import (
    CapabilityExecutionPlan,
    WorkspaceCapabilitySelection,
    build_capability_execution_plan_from_workspace_owner_plan,
)
from aware_workspace.compiler.workspace import Workspace, WorkspaceSnapshot

from aware_code.language_service.document import DocumentContext
from aware_code.language_service.perf import PerfTracer


class AvailableProviderKeysResolver(Protocol):
    def __call__(
        self,
        *,
        module_provider_keys: Iterable[str] | None = None,
    ) -> tuple[str, ...]: ...


class ServiceMixinBase(ABC):
    """Typed contract for LanguageService mixins.

    Mixin methods are type-checked in isolation, so they must declare the shared
    service state + internal helpers they rely on.
    """

    _workspace: Workspace
    _snapshot: WorkspaceSnapshot | None
    _last_build_error: str | None
    _perf: PerfTracer

    @abstractmethod
    def _ensure_snapshot_for_uri(self, *, uri: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def _rebuild_full(self, *, focus_uri: str | None = None, reason: str = "change") -> None:
        raise NotImplementedError

    @abstractmethod
    def _document_context(self, *, uri: str, document_text: str) -> DocumentContext:
        raise NotImplementedError

    @abstractmethod
    def _cached_capability_execution_plan(
        self,
        *,
        capability: str,
        uri: str,
        build: Callable[[], CapabilityExecutionPlan],
    ) -> CapabilityExecutionPlan:
        raise NotImplementedError

    def _capability_execution_plan_for_uri(
        self,
        *,
        capability: str,
        uri: str,
        configured_selection: WorkspaceCapabilitySelection,
        ensure_providers_registered: Callable[[], None],
        get_registered_descriptors: Callable[[], tuple[CapabilityProviderDescriptor, ...]],
        get_available_provider_keys: AvailableProviderKeysResolver,
    ) -> CapabilityExecutionPlan:
        ensure_providers_registered()

        def _build_plan() -> CapabilityExecutionPlan:
            workspace_owner_plan = self._workspace.capability_owner_plan_for_uri(uri=uri)
            return build_capability_execution_plan_from_workspace_owner_plan(
                capability=capability,
                configured_selection=configured_selection,
                workspace_owner_plan=workspace_owner_plan,
                registered_descriptors=get_registered_descriptors(),
                available_provider_keys=get_available_provider_keys(
                    module_provider_keys=workspace_owner_plan.plugin_provider_keys
                ),
            )

        return self._cached_capability_execution_plan(
            capability=capability,
            uri=uri,
            build=_build_plan,
        )

    def _language_service_binding_overlay_providers(
        self,
        *,
        capability: str,
        uri: str,
        provider_keys: Iterable[str],
    ) -> dict[str, Callable[..., object]]:
        owner_plan = self._workspace.capability_owner_plan_for_uri(uri=uri)
        resolution = owner_plan.module_package_resolution
        if resolution is None:
            return {}
        if resolution.semantic_contract is not None:
            return package_semantic_contract_provider_map(
                capability=capability,
                workspace_root=self._workspace.workspace_root,
                module_root_relative_path=resolution.module_root_relative_path,
                semantic_contract=resolution.semantic_contract,
                provider_keys=provider_keys,
            )
        return package_semantic_binding_provider_map(
            capability=capability,
            workspace_root=self._workspace.workspace_root,
            module_root_relative_path=resolution.module_root_relative_path,
            semantic_bindings=resolution.semantic_bindings,
            provider_keys=provider_keys,
        )

    def _is_aware_config_uri(self, uri: str) -> bool:
        return uri.endswith(
            (
                "aware.toml",
                "aware.workflows.toml",
                "aware.module.toml",
                "aware.environment.toml",
                "aware.programs.toml",
            )
        )
