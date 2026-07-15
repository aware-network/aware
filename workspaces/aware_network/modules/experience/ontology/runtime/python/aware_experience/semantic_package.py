from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_experience.semantic_contract import (
    AWARE_EXPERIENCE_SEMANTIC_CONTRACT,
    EXPERIENCE_ACTION_OWNER,
    EXPERIENCE_ACTOR_OWNER,
    EXPERIENCE_CAPABILITY_BUNDLES,
    EXPERIENCE_CAPABILITY_PARTICIPATION,
    EXPERIENCE_CAPABILITY_PROFILES,
    EXPERIENCE_DIAGNOSTICS_CAPABILITY_PROFILES,
    EXPERIENCE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    EXPERIENCE_ENVIRONMENT_OWNER,
    EXPERIENCE_EVENT_OWNER,
    EXPERIENCE_GRAPH_OWNER,
    EXPERIENCE_PROGRAM_OWNER,
    EXPERIENCE_PROJECTION_OWNER,
    EXPERIENCE_ROLE_OWNER,
    EXPERIENCE_SEMANTIC_SCOPE_KEYS,
    EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
    EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)


class _ExperienceSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_experience"

    def resolve(self, code_package: CodePackageInfo) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_experience_toml":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="experience",
                semantic_kind="experience_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "package_kind": code_package.metadata.get("package_kind"),
                    "environment_handle": code_package.metadata.get("environment_handle"),
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 200,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": True,
                    "workspace_materialization_runtime_index": "workspace_experience",
                    "semantic_projection_name": "ExperiencePackage",
                    "semantic_root_kind": "environment_experience",
                },
                semantic_scope_keys=AWARE_EXPERIENCE_SEMANTIC_CONTRACT.semantic_scope_keys,
                capability_participation=AWARE_EXPERIENCE_SEMANTIC_CONTRACT.capability_participation,
                capability_profiles=AWARE_EXPERIENCE_SEMANTIC_CONTRACT.capability_profiles,
                capability_bundles=AWARE_EXPERIENCE_SEMANTIC_CONTRACT.capability_bundles,
            ),
        )


_PROVIDER = _ExperienceSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_EXPERIENCE_SEMANTIC_CONTRACT",
    "EXPERIENCE_ACTION_OWNER",
    "EXPERIENCE_ACTOR_OWNER",
    "EXPERIENCE_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_CAPABILITY_BUNDLES",
    "EXPERIENCE_CAPABILITY_PROFILES",
    "EXPERIENCE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "EXPERIENCE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_ENVIRONMENT_OWNER",
    "EXPERIENCE_EVENT_OWNER",
    "EXPERIENCE_GRAPH_OWNER",
    "EXPERIENCE_PROGRAM_OWNER",
    "EXPERIENCE_PROJECTION_OWNER",
    "EXPERIENCE_ROLE_OWNER",
    "EXPERIENCE_SEMANTIC_SCOPE_KEYS",
    "EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "register_semantic_package_providers",
]
