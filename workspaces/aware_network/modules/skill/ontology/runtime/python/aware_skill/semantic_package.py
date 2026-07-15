from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_skill.semantic_contract import (
    AWARE_SKILL_SEMANTIC_CONTRACT,
    SKILL_API_OWNER,
    SKILL_CAPABILITY_BUNDLES,
    SKILL_CAPABILITY_PARTICIPATION,
    SKILL_CAPABILITY_PROFILES,
    SKILL_CONFIG_OWNER,
    SKILL_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    SKILL_DIAGNOSTICS_CAPABILITY_PROFILES,
    SKILL_ENDPOINT_OWNER,
    SKILL_SEMANTIC_SCOPE_KEYS,
    SKILL_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
    SKILL_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
    SKILL_STEP_OWNER,
)


class _SkillSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_skill"

    def resolve(
        self,
        code_package: CodePackageInfo,
    ) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_skill_toml":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="skill",
                semantic_kind="skill_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "package_kind": code_package.metadata.get("package_kind"),
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 400,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": True,
                    "semantic_projection_name": "SkillPackage",
                    "semantic_root_kind": "skill_config",
                },
                semantic_scope_keys=AWARE_SKILL_SEMANTIC_CONTRACT.semantic_scope_keys,
                capability_participation=(
                    AWARE_SKILL_SEMANTIC_CONTRACT.capability_participation
                ),
                capability_profiles=AWARE_SKILL_SEMANTIC_CONTRACT.capability_profiles,
                capability_bundles=AWARE_SKILL_SEMANTIC_CONTRACT.capability_bundles,
            ),
        )


_PROVIDER = _SkillSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_SKILL_SEMANTIC_CONTRACT",
    "SKILL_API_OWNER",
    "SKILL_CAPABILITY_BUNDLES",
    "SKILL_CAPABILITY_PARTICIPATION",
    "SKILL_CAPABILITY_PROFILES",
    "SKILL_CONFIG_OWNER",
    "SKILL_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "SKILL_DIAGNOSTICS_CAPABILITY_PROFILES",
    "SKILL_ENDPOINT_OWNER",
    "SKILL_SEMANTIC_SCOPE_KEYS",
    "SKILL_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "SKILL_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "SKILL_STEP_OWNER",
    "register_semantic_package_providers",
]
