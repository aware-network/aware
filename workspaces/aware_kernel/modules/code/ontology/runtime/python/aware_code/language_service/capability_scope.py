from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar, overload

from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor as CapabilityProviderDescriptor,
    WorkspaceActivation,
    merge_language_service_provider_descriptors,
)
from aware_code.package.discovery import CodePackagePathResolution
from aware_code.package.semantic_binding import (
    package_semantic_contract_provider_descriptors,
    package_semantic_binding_provider_descriptors,
)
from aware_code.semantic_scope.schemas import (
    SemanticScopePayloadValue,
    SemanticScopeResolution,
)
from aware_workspace.compiler.workspace import WorkspaceCapabilityOwnerPlan


def _normalize_scope_values(values: Iterable[str] | None) -> frozenset[str] | None:
    if values is None:
        return None

    normalized = {
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    }
    return frozenset(normalized)


def _normalize_selection_values(values: Iterable[str] | None) -> tuple[str, ...] | None:
    if values is None:
        return None

    normalized = sorted(
        {
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        }
    )
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class CapabilityExecutionScope:
    semantic_owners: frozenset[str] | None = None
    provider_keys: frozenset[str] | None = None

    @classmethod
    def from_iterables(
        cls,
        *,
        semantic_owners: Iterable[str] | None = None,
        provider_keys: Iterable[str] | None = None,
    ) -> "CapabilityExecutionScope":
        return cls(
            semantic_owners=_normalize_scope_values(semantic_owners),
            provider_keys=_normalize_scope_values(provider_keys),
        )

    def allows(self, *, descriptor: CapabilityProviderDescriptor) -> bool:
        if self.semantic_owners is not None and descriptor.semantic_owner not in self.semantic_owners:
            return False
        if self.provider_keys is not None and descriptor.provider_key not in self.provider_keys:
            return False
        return True


@dataclass(frozen=True, slots=True)
class WorkspaceCapabilitySelection:
    owner_presets: tuple[str, ...] | None = None
    semantic_owners: frozenset[str] | None = None
    provider_keys: frozenset[str] | None = None

    @classmethod
    def from_iterables(
        cls,
        *,
        owner_presets: Iterable[str] | None = None,
        semantic_owners: Iterable[str] | None = None,
        provider_keys: Iterable[str] | None = None,
    ) -> "WorkspaceCapabilitySelection":
        return cls(
            owner_presets=_normalize_selection_values(owner_presets),
            semantic_owners=_normalize_scope_values(semantic_owners),
            provider_keys=_normalize_scope_values(provider_keys),
        )

    def execution_scope(
        self,
        *,
        resolved_semantic_owners: Iterable[str] | None = None,
    ) -> CapabilityExecutionScope:
        semantic_owners = self.semantic_owners
        if semantic_owners is None and self.owner_presets is not None:
            semantic_owners = _normalize_scope_values(resolved_semantic_owners)
        return CapabilityExecutionScope(
            semantic_owners=semantic_owners,
            provider_keys=self.provider_keys,
        )


@dataclass(frozen=True, slots=True)
class WorkspaceCapabilityConfiguration:
    diagnostics: WorkspaceCapabilitySelection = field(default_factory=WorkspaceCapabilitySelection)
    semantic_tokens: WorkspaceCapabilitySelection = field(default_factory=WorkspaceCapabilitySelection)


@dataclass(frozen=True, slots=True)
class CapabilityProviderExecutionStatus:
    provider_key: str
    semantic_owner: str
    required_semantic_scope_keys: tuple[str, ...]
    missing_semantic_scope_keys: tuple[str, ...]
    priority: int
    applies_when: str
    workspace_activation: WorkspaceActivation
    activated_by_workspace_owner_scope: bool = True
    allowed_by_configured_scope: bool = True
    provider_available: bool = True
    required_semantic_scopes_resolved: bool = True
    active: bool = True


@dataclass(frozen=True, slots=True)
class CapabilityExecutionPlan:
    configured_scope: CapabilityExecutionScope
    workspace_owner_scope: CapabilityExecutionScope | None
    workspace_resolved_scope: CapabilityExecutionScope | None
    effective_scope: CapabilityExecutionScope
    workspace_semantic_package_provider_keys: frozenset[str] | None
    workspace_plugin_provider_keys: frozenset[str] | None
    workspace_fallback_plugin_provider_keys: frozenset[str] | None
    workspace_package_resolution: CodePackagePathResolution | None = None
    workspace_semantic_scope_resolutions: tuple[SemanticScopeResolution, ...] = ()
    workspace_binding_provider_descriptors: tuple[CapabilityProviderDescriptor, ...] = ()
    providers: tuple[CapabilityProviderExecutionStatus, ...] = ()


T_SemanticScopeRuntime = TypeVar("T_SemanticScopeRuntime")


@dataclass(frozen=True, slots=True)
class CapabilityProviderExecutionContext:
    capability: str
    uri: str
    workspace_root: Path
    document_path: Path
    plan: CapabilityExecutionPlan

    @property
    def package_resolution(self) -> CodePackagePathResolution | None:
        return self.plan.workspace_package_resolution

    @property
    def workspace_semantic_package_provider_keys(self) -> frozenset[str] | None:
        return self.plan.workspace_semantic_package_provider_keys

    @property
    def workspace_plugin_provider_keys(self) -> frozenset[str] | None:
        return self.plan.workspace_plugin_provider_keys

    @property
    def workspace_fallback_plugin_provider_keys(self) -> frozenset[str] | None:
        return self.plan.workspace_fallback_plugin_provider_keys

    @property
    def workspace_semantic_scope_resolutions(self) -> tuple[SemanticScopeResolution, ...]:
        return self.plan.workspace_semantic_scope_resolutions

    @property
    def workspace_owner_scope(self) -> CapabilityExecutionScope | None:
        return self.plan.workspace_owner_scope

    @property
    def workspace_resolved_scope(self) -> CapabilityExecutionScope | None:
        return self.plan.workspace_resolved_scope

    @property
    def effective_scope(self) -> CapabilityExecutionScope:
        return self.plan.effective_scope

    def semantic_scope_resolution(self, *, scope_key: str) -> SemanticScopeResolution | None:
        for resolution in self.workspace_semantic_scope_resolutions:
            if resolution.scope_key == scope_key:
                return resolution
        return None

    def semantic_scope_payload(
        self,
        *,
        scope_key: str,
    ) -> dict[str, SemanticScopePayloadValue] | None:
        resolution = self.semantic_scope_resolution(scope_key=scope_key)
        if resolution is None:
            return None
        return dict(resolution.payload)

    @overload
    def semantic_scope_runtime(
        self,
        *,
        scope_key: str,
        expected_type: type[T_SemanticScopeRuntime],
    ) -> T_SemanticScopeRuntime | None: ...

    @overload
    def semantic_scope_runtime(
        self,
        *,
        scope_key: str,
        expected_type: None = None,
    ) -> object | None: ...

    def semantic_scope_runtime(
        self,
        *,
        scope_key: str,
        expected_type: type[T_SemanticScopeRuntime] | None = None,
    ) -> T_SemanticScopeRuntime | object | None:
        resolution = self.semantic_scope_resolution(scope_key=scope_key)
        if resolution is None:
            return None
        runtime_value = resolution.runtime_value
        if expected_type is None or runtime_value is None:
            return runtime_value
        if isinstance(runtime_value, expected_type):
            return runtime_value
        return None

    def resolve_workspace_path(self, path: Path | None) -> Path | None:
        if path is None:
            return None
        if path.is_absolute():
            return path.resolve()
        return (self.workspace_root.resolve() / path).resolve()

    def nearest_package_root(self) -> Path | None:
        resolution = self.package_resolution
        return self.resolve_workspace_path(
            resolution.nearest_package_root if resolution is not None else None
        )

    def nearest_manifest_path(self, *, filename: str | None = None) -> Path | None:
        resolution = self.package_resolution
        manifest_path = self.resolve_workspace_path(
            resolution.nearest_manifest_path if resolution is not None else None
        )
        if filename is not None and (manifest_path is None or manifest_path.name != filename):
            return None
        return manifest_path

    def owning_package_root(self) -> Path | None:
        resolution = self.package_resolution
        return self.resolve_workspace_path(
            resolution.owning_package_root if resolution is not None else None
        )

    def owning_manifest_path(self, *, filename: str | None = None) -> Path | None:
        resolution = self.package_resolution
        manifest_path = self.resolve_workspace_path(
            resolution.owning_manifest_path if resolution is not None else None
        )
        if filename is not None and (manifest_path is None or manifest_path.name != filename):
            return None
        return manifest_path


def build_capability_execution_plan(
    *,
    configured_scope: CapabilityExecutionScope,
    descriptors: Iterable[CapabilityProviderDescriptor],
    workspace_owner_scope: CapabilityExecutionScope | None,
    workspace_semantic_package_provider_keys: Iterable[str] | None = None,
    workspace_plugin_provider_keys: Iterable[str] | None = None,
    workspace_fallback_plugin_provider_keys: Iterable[str] | None = None,
    workspace_package_resolution: CodePackagePathResolution | None = None,
    workspace_semantic_scope_resolutions: Iterable[SemanticScopeResolution] | None = None,
    workspace_binding_provider_descriptors: Iterable[CapabilityProviderDescriptor] | None = None,
    available_provider_keys: Iterable[str] | None = None,
) -> CapabilityExecutionPlan:
    descriptor_tuple = tuple(descriptors)
    package_provider_keys = _normalize_scope_values(workspace_semantic_package_provider_keys)
    plugin_provider_keys = _normalize_scope_values(workspace_plugin_provider_keys)
    fallback_plugin_provider_keys = _normalize_scope_values(
        workspace_fallback_plugin_provider_keys
    )
    semantic_scope_resolution_tuple = tuple(workspace_semantic_scope_resolutions or ())
    binding_provider_descriptor_tuple = tuple(workspace_binding_provider_descriptors or ())
    available_provider_key_set = _normalize_scope_values(available_provider_keys)
    available_semantic_scope_keys = frozenset(
        resolution.scope_key
        for resolution in semantic_scope_resolution_tuple
    )
    workspace_resolved_scope = CapabilityExecutionScope.from_iterables(
        semantic_owners=[
            descriptor.semantic_owner
            for descriptor in descriptor_tuple
            if _descriptor_activated_by_workspace_owner_scope(
                descriptor=descriptor,
                workspace_owner_scope=workspace_owner_scope,
            )
            and _descriptor_provider_available(
                descriptor=descriptor,
                available_provider_keys=available_provider_key_set,
            )
            and _descriptor_required_semantic_scopes_resolved(
                descriptor=descriptor,
                available_semantic_scope_keys=available_semantic_scope_keys,
            )
        ],
        provider_keys=[
            descriptor.provider_key
            for descriptor in descriptor_tuple
            if _descriptor_activated_by_workspace_owner_scope(
                descriptor=descriptor,
                workspace_owner_scope=workspace_owner_scope,
            )
            and _descriptor_provider_available(
                descriptor=descriptor,
                available_provider_keys=available_provider_key_set,
            )
            and _descriptor_required_semantic_scopes_resolved(
                descriptor=descriptor,
                available_semantic_scope_keys=available_semantic_scope_keys,
            )
        ],
    )

    active_descriptors = [
        descriptor
        for descriptor in descriptor_tuple
        if _descriptor_activated_by_workspace_owner_scope(
            descriptor=descriptor,
            workspace_owner_scope=workspace_owner_scope,
        )
        and _descriptor_provider_available(
            descriptor=descriptor,
            available_provider_keys=available_provider_key_set,
        )
        and _descriptor_required_semantic_scopes_resolved(
            descriptor=descriptor,
            available_semantic_scope_keys=available_semantic_scope_keys,
        )
        and configured_scope.allows(descriptor=descriptor)
    ]
    effective_scope = CapabilityExecutionScope.from_iterables(
        semantic_owners=[descriptor.semantic_owner for descriptor in active_descriptors],
        provider_keys=[descriptor.provider_key for descriptor in active_descriptors],
    )

    providers = tuple(
        CapabilityProviderExecutionStatus(
            provider_key=descriptor.provider_key,
            semantic_owner=descriptor.semantic_owner,
            required_semantic_scope_keys=descriptor.required_semantic_scope_keys,
            missing_semantic_scope_keys=_descriptor_missing_semantic_scope_keys(
                descriptor=descriptor,
                available_semantic_scope_keys=available_semantic_scope_keys,
            ),
            priority=descriptor.priority,
            applies_when=descriptor.applies_when,
            workspace_activation=descriptor.workspace_activation,
            activated_by_workspace_owner_scope=_descriptor_activated_by_workspace_owner_scope(
                descriptor=descriptor,
                workspace_owner_scope=workspace_owner_scope,
            ),
            allowed_by_configured_scope=configured_scope.allows(descriptor=descriptor),
            provider_available=_descriptor_provider_available(
                descriptor=descriptor,
                available_provider_keys=available_provider_key_set,
            ),
            required_semantic_scopes_resolved=_descriptor_required_semantic_scopes_resolved(
                descriptor=descriptor,
                available_semantic_scope_keys=available_semantic_scope_keys,
            ),
            active=effective_scope.allows(descriptor=descriptor),
        )
        for descriptor in descriptor_tuple
    )
    return CapabilityExecutionPlan(
        configured_scope=configured_scope,
        workspace_owner_scope=workspace_owner_scope,
        workspace_resolved_scope=workspace_resolved_scope,
        effective_scope=effective_scope,
        workspace_semantic_package_provider_keys=package_provider_keys,
        workspace_plugin_provider_keys=plugin_provider_keys,
        workspace_fallback_plugin_provider_keys=fallback_plugin_provider_keys,
        workspace_package_resolution=workspace_package_resolution,
        workspace_semantic_scope_resolutions=semantic_scope_resolution_tuple,
        workspace_binding_provider_descriptors=binding_provider_descriptor_tuple,
        providers=providers,
    )


def build_capability_execution_plan_from_workspace_owner_plan(
    *,
    capability: str,
    configured_selection: WorkspaceCapabilitySelection,
    workspace_owner_plan: WorkspaceCapabilityOwnerPlan,
    registered_descriptors: Iterable[CapabilityProviderDescriptor] = (),
    available_provider_keys: Iterable[str] | None = None,
) -> CapabilityExecutionPlan:
    owner_policy = workspace_owner_plan.owner_policy_plan(
        capability=capability,
        configured_owner_presets=configured_selection.owner_presets,
    )
    binding_provider_descriptors = _workspace_module_package_binding_provider_descriptors(
        capability=capability,
        workspace_owner_plan=workspace_owner_plan,
    )
    descriptors = merge_language_service_provider_descriptors(
        capability=capability,
        provider_descriptors=(
            *workspace_owner_plan.capability_provider_descriptors_for_capability(
                capability=capability
            ),
            *binding_provider_descriptors,
        ),
        registered_descriptors=registered_descriptors,
    )
    resolved_available_provider_keys = (
        *(available_provider_keys or ()),
        *(descriptor.provider_key for descriptor in binding_provider_descriptors),
    )
    return build_capability_execution_plan(
        configured_scope=configured_selection.execution_scope(
            resolved_semantic_owners=owner_policy.effective_semantic_owners
        ),
        descriptors=descriptors,
        workspace_owner_scope=CapabilityExecutionScope.from_iterables(
            semantic_owners=owner_policy.effective_semantic_owners
        )
        if owner_policy.effective_semantic_owners is not None
        else None,
        workspace_semantic_package_provider_keys=workspace_owner_plan.semantic_package_provider_keys,
        workspace_plugin_provider_keys=workspace_owner_plan.plugin_provider_keys,
        workspace_fallback_plugin_provider_keys=(
            workspace_owner_plan.fallback_plugin_provider_keys_for_capability(
                capability=capability
            )
        ),
        workspace_package_resolution=workspace_owner_plan.package_resolution,
        workspace_semantic_scope_resolutions=workspace_owner_plan.semantic_scope_resolutions,
        workspace_binding_provider_descriptors=binding_provider_descriptors,
        available_provider_keys=resolved_available_provider_keys,
    )


def _workspace_module_package_binding_provider_descriptors(
    *,
    capability: str,
    workspace_owner_plan: WorkspaceCapabilityOwnerPlan,
) -> tuple[CapabilityProviderDescriptor, ...]:
    module_package_resolution = workspace_owner_plan.module_package_resolution
    if module_package_resolution is None:
        return ()
    if module_package_resolution.semantic_contract is not None:
        return package_semantic_contract_provider_descriptors(
            capability=capability,
            semantic_contract=module_package_resolution.semantic_contract,
        )
    return package_semantic_binding_provider_descriptors(
        capability=capability,
        module_provider_key=module_package_resolution.module_id,
        semantic_bindings=module_package_resolution.semantic_bindings,
    )


def resolve_capability_execution_scope(
    *,
    configured_scope: CapabilityExecutionScope,
    descriptors: Iterable[CapabilityProviderDescriptor],
    workspace_owner_scope: CapabilityExecutionScope | None,
    workspace_semantic_package_provider_keys: Iterable[str] | None = None,
    workspace_plugin_provider_keys: Iterable[str] | None = None,
    workspace_fallback_plugin_provider_keys: Iterable[str] | None = None,
    workspace_package_resolution: CodePackagePathResolution | None = None,
    workspace_semantic_scope_resolutions: Iterable[SemanticScopeResolution] | None = None,
    available_provider_keys: Iterable[str] | None = None,
) -> CapabilityExecutionScope:
    return build_capability_execution_plan(
        configured_scope=configured_scope,
        descriptors=descriptors,
        workspace_owner_scope=workspace_owner_scope,
        workspace_semantic_package_provider_keys=workspace_semantic_package_provider_keys,
        workspace_plugin_provider_keys=workspace_plugin_provider_keys,
        workspace_fallback_plugin_provider_keys=workspace_fallback_plugin_provider_keys,
        workspace_package_resolution=workspace_package_resolution,
        workspace_semantic_scope_resolutions=workspace_semantic_scope_resolutions,
        available_provider_keys=available_provider_keys,
    ).effective_scope


def _descriptor_activated_by_workspace_owner_scope(
    *,
    descriptor: CapabilityProviderDescriptor,
    workspace_owner_scope: CapabilityExecutionScope | None,
) -> bool:
    if descriptor.workspace_activation == "always":
        return True
    owner_scope = workspace_owner_scope.semantic_owners if workspace_owner_scope is not None else None
    if owner_scope is None:
        return True
    return descriptor.semantic_owner in owner_scope


def _descriptor_missing_semantic_scope_keys(
    *,
    descriptor: CapabilityProviderDescriptor,
    available_semantic_scope_keys: frozenset[str],
) -> tuple[str, ...]:
    if not descriptor.required_semantic_scope_keys:
        return ()
    return tuple(
        sorted(
            scope_key
            for scope_key in descriptor.required_semantic_scope_keys
            if scope_key not in available_semantic_scope_keys
        )
    )


def _descriptor_required_semantic_scopes_resolved(
    *,
    descriptor: CapabilityProviderDescriptor,
    available_semantic_scope_keys: frozenset[str],
) -> bool:
    return not _descriptor_missing_semantic_scope_keys(
        descriptor=descriptor,
        available_semantic_scope_keys=available_semantic_scope_keys,
    )


def _descriptor_provider_available(
    *,
    descriptor: CapabilityProviderDescriptor,
    available_provider_keys: frozenset[str] | None,
) -> bool:
    if available_provider_keys is None:
        return True
    return descriptor.provider_key in available_provider_keys


def _intersect_capability_execution_scopes(
    *,
    configured_scope: CapabilityExecutionScope,
    resolved_scope: CapabilityExecutionScope,
) -> CapabilityExecutionScope:
    return CapabilityExecutionScope(
        semantic_owners=_intersect_scope_values(
            configured_scope.semantic_owners,
            resolved_scope.semantic_owners,
        ),
        provider_keys=_intersect_scope_values(
            configured_scope.provider_keys,
            resolved_scope.provider_keys,
        ),
    )


def _intersect_scope_values(
    configured_values: frozenset[str] | None,
    resolved_values: frozenset[str] | None,
) -> frozenset[str] | None:
    if configured_values is None:
        return resolved_values
    if resolved_values is None:
        return configured_values
    return frozenset(configured_values & resolved_values)
