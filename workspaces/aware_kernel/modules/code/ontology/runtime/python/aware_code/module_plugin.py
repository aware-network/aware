from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from typing import Literal


RegistrationHook = Callable[[], None]
WorkspaceActivation = Literal["always", "owner"]


@dataclass(frozen=True, slots=True)
class AwareModulePluginCapabilityPolicy:
    capability: str
    workspace_activation: WorkspaceActivation = "owner"
    workspace_fallback: bool = False


@dataclass(frozen=True, slots=True)
class AwareModulePackageContract:
    id: str
    kind: str
    manifest: str
    visibility: str = "module"
    semantic_contract: "AwareModulePackageSemanticContract | None" = None
    semantic_bindings: tuple["AwareModulePackageSemanticBindingContract", ...] = ()
    mirrors_ontology: bool = False


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticContractBinding:
    capability: str
    module: str
    callable: str


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticContract:
    role: str
    contract: str
    provider_key: str
    module: str
    owns_manifest_kinds: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    bindings: tuple[AwareModulePackageSemanticContractBinding, ...] = ()


@dataclass(frozen=True, slots=True)
class AwareModulePackageSemanticBindingContract:
    role: str
    contract: str
    binding_module: str | None = None
    capabilities: tuple[str, ...] = ()
    callable_name: str | None = None


@dataclass(frozen=True, slots=True)
class AwareModulePlugin:
    """Shared module/plugin contract for Workspace semantic truth and LSP execution."""

    provider_key: str
    capability_contract_module: str | None = None
    capability_execution_module: str | None = None
    semantic_contract_module: str | None = None
    code_package_materialization_contract_module: str | None = None
    packages: tuple[AwareModulePackageContract, ...] = ()
    capability_policy: tuple[AwareModulePluginCapabilityPolicy, ...] = ()
    register_semantic_package_providers: RegistrationHook | None = None
    register_semantic_scope_providers: RegistrationHook | None = None


__all__ = [
    "AwareModulePlugin",
    "AwareModulePluginCapabilityPolicy",
    "AwareModulePackageContract",
    "AwareModulePackageSemanticBindingContract",
    "AwareModulePackageSemanticContract",
    "AwareModulePackageSemanticContractBinding",
    "WorkspaceActivation",
]
