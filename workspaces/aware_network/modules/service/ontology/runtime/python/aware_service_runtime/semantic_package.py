from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_service_runtime.semantic_contract import (
    AWARE_SERVICE_SEMANTIC_CONTRACT,
    SERVICE_API_OWNER,
    SERVICE_CAPABILITY_BUNDLES,
    SERVICE_CAPABILITY_PARTICIPATION,
    SERVICE_CAPABILITY_PROFILES,
    SERVICE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    SERVICE_DIAGNOSTICS_CAPABILITY_PROFILES,
    SERVICE_ENDPOINT_OWNER,
    SERVICE_EXPERIENCE_OWNER,
    SERVICE_OPERATION_OWNER,
    SERVICE_PROJECTION_OWNER,
    SERVICE_ROOT_OWNER,
    SERVICE_SEMANTIC_SCOPE_KEYS,
    SERVICE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
    SERVICE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)


class _ServiceSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_service"

    def resolve(self, code_package: CodePackageInfo) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_service_toml":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="service",
                semantic_kind="service_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "package_kind": code_package.metadata.get("package_kind"),
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 300,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": True,
                    "semantic_projection_name": "ServicePackage",
                    "semantic_root_kind": "service_config",
                },
                semantic_scope_keys=AWARE_SERVICE_SEMANTIC_CONTRACT.semantic_scope_keys,
                capability_participation=(
                    AWARE_SERVICE_SEMANTIC_CONTRACT.capability_participation
                ),
                capability_profiles=AWARE_SERVICE_SEMANTIC_CONTRACT.capability_profiles,
                capability_bundles=AWARE_SERVICE_SEMANTIC_CONTRACT.capability_bundles,
            ),
        )


_PROVIDER = _ServiceSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_SERVICE_SEMANTIC_CONTRACT",
    "SERVICE_API_OWNER",
    "SERVICE_CAPABILITY_BUNDLES",
    "SERVICE_CAPABILITY_PARTICIPATION",
    "SERVICE_CAPABILITY_PROFILES",
    "SERVICE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "SERVICE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "SERVICE_ENDPOINT_OWNER",
    "SERVICE_EXPERIENCE_OWNER",
    "SERVICE_OPERATION_OWNER",
    "SERVICE_PROJECTION_OWNER",
    "SERVICE_ROOT_OWNER",
    "SERVICE_SEMANTIC_SCOPE_KEYS",
    "SERVICE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "SERVICE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "register_semantic_package_providers",
]
