from __future__ import annotations

from typing import Protocol

from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
)
from aware_code.package.discovery import CodePackagePathResolution
from aware_code.semantic_scope.schemas import SemanticScopeResolution


class CodeLanguageServiceModulePackageSemanticContract(Protocol):
    role: str
    contract: str
    provider_key: str
    module: str


class CodeLanguageServiceModulePackageResolution(Protocol):
    semantic_contract: CodeLanguageServiceModulePackageSemanticContract | None


class CodeLanguageServiceOwnerPolicyPlan(Protocol):
    effective_semantic_owners: tuple[str, ...] | None


class CodeLanguageServiceCapabilityOwnerPlan(Protocol):
    semantic_package_provider_keys: tuple[str, ...]
    plugin_provider_keys: tuple[str, ...]
    package_resolution: CodePackagePathResolution | None
    semantic_scope_resolutions: tuple[SemanticScopeResolution, ...]
    module_package_resolution: CodeLanguageServiceModulePackageResolution | None

    def owner_policy_plan(
        self,
        *,
        capability: str,
        configured_owner_presets: tuple[str, ...] | None,
    ) -> CodeLanguageServiceOwnerPolicyPlan: ...

    def capability_provider_descriptors_for_capability(
        self,
        *,
        capability: str,
    ) -> tuple[LanguageServiceProviderDescriptor, ...]: ...

    def fallback_plugin_provider_keys_for_capability(
        self,
        *,
        capability: str,
    ) -> tuple[str, ...]: ...


__all__ = [
    "CodeLanguageServiceCapabilityOwnerPlan",
    "CodeLanguageServiceModulePackageResolution",
    "CodeLanguageServiceModulePackageSemanticContract",
    "CodeLanguageServiceOwnerPolicyPlan",
]
