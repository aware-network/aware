from __future__ import annotations

from dataclasses import dataclass

from aware_code.language_service_capability_contract import (
    LanguageServiceModuleCapabilityContract,
)
from aware_code.language_service_execution_contract import (
    LanguageServiceModuleCapabilityExecutionContract,
)
from aware_code.language_service_provider_descriptor import (
    LanguageServiceProviderDescriptor,
)
from aware_code.module_code_package_materialization_contract import (
    ModuleCodePackageMaterializationContract,
    ModuleCodePackageMaterializationDescriptor,
)
from aware_code.module_plugin import (
    AwareModulePackageContract,
    AwareModulePluginCapabilityPolicy,
)
from aware_code.module_semantic_contract import ModuleSemanticContract


@dataclass(frozen=True, slots=True)
class CodeModuleContract:
    """Runtime aggregate for module-owned code/product contract truth.

    This intentionally wraps today's Python runtime contract modules first. The
    same shape is the migration target for a later ontology-backed
    `code_module.aware` contract without forcing Workspace or LSP consumers to
    keep calling each specialized registry rail independently.
    """

    provider_key: str
    capability_contract_module: str | None = None
    capability_execution_module: str | None = None
    semantic_contract_module: str | None = None
    code_package_materialization_contract_module: str | None = None
    packages: tuple[AwareModulePackageContract, ...] = ()
    capability_policy: tuple[AwareModulePluginCapabilityPolicy, ...] = ()
    language_service_capability_contract: LanguageServiceModuleCapabilityContract | None = None
    language_service_capability_execution_contract: (
        LanguageServiceModuleCapabilityExecutionContract | None
    ) = None
    semantic_contract: ModuleSemanticContract | None = None
    code_package_materialization_contract: (
        ModuleCodePackageMaterializationContract | None
    ) = None
    language_service_provider_descriptors: tuple[
        LanguageServiceProviderDescriptor,
        ...,
    ] = ()

    def package_materializations_for(
        self,
        *,
        surface: str,
    ) -> tuple[ModuleCodePackageMaterializationDescriptor, ...]:
        if self.code_package_materialization_contract is None:
            return ()
        return self.code_package_materialization_contract.package_materializations_for(
            surface=surface
        )

    def workspace_fallback_for(self, *, capability: str) -> bool:
        return any(
            policy.capability == capability and policy.workspace_fallback
            for policy in self.capability_policy
        )

    def packages_for_kind(
        self,
        *,
        kind: str,
    ) -> tuple[AwareModulePackageContract, ...]:
        return tuple(package for package in self.packages if package.kind == kind)


__all__ = ["CodeModuleContract"]
