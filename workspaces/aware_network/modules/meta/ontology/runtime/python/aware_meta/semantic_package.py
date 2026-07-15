from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_meta.semantic_contract import (
    AWARE_META_SEMANTIC_CONTRACT,
    META_ANNOTATION_OWNER,
    META_CAPABILITY_BUNDLES,
    META_CAPABILITY_PARTICIPATION,
    META_CAPABILITY_PROFILES,
    META_DEFAULTS_OWNER,
    META_DIAGNOSTICS_CAPABILITY_PROFILES,
    META_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    META_IDENTITY_OWNER,
    META_PROJECTION_OWNER,
    META_SEMANTIC_SCOPE_KEYS,
    META_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
    META_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
    META_TYPE_MIRROR_OWNER,
)


class _MetaSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_meta"

    def resolve(
        self, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        manifest_kind = code_package.metadata.get("manifest_kind")
        if manifest_kind != "aware_toml":
            return ()
        package_kind = code_package.metadata.get("package_kind")
        if package_kind != "ontology":
            return ()

        semantic_kind = "object_config_graph_package"
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="meta",
                semantic_kind=semantic_kind,
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "manifest_kind": manifest_kind,
                    "package_kind": package_kind,
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 50,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": False,
                    "semantic_projection_name": "ObjectConfigGraphPackage",
                    "semantic_root_kind": "object_config_graph",
                },
                semantic_scope_keys=AWARE_META_SEMANTIC_CONTRACT.semantic_scope_keys,
                capability_participation=AWARE_META_SEMANTIC_CONTRACT.capability_participation,
                capability_profiles=AWARE_META_SEMANTIC_CONTRACT.capability_profiles,
                capability_bundles=AWARE_META_SEMANTIC_CONTRACT.capability_bundles,
            ),
        )


_PROVIDER = _MetaSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_META_SEMANTIC_CONTRACT",
    "META_ANNOTATION_OWNER",
    "META_CAPABILITY_PARTICIPATION",
    "META_CAPABILITY_BUNDLES",
    "META_CAPABILITY_PROFILES",
    "META_DEFAULTS_OWNER",
    "META_DIAGNOSTICS_CAPABILITY_PROFILES",
    "META_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "META_IDENTITY_OWNER",
    "META_PROJECTION_OWNER",
    "META_SEMANTIC_SCOPE_KEYS",
    "META_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "META_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "META_TYPE_MIRROR_OWNER",
    "register_semantic_package_providers",
]
