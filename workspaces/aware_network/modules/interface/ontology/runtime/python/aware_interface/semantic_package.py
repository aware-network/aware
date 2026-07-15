from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_interface.semantic_contract import (
    AWARE_INTERFACE_SEMANTIC_CONTRACT,
    INTERFACE_API_OWNER,
    INTERFACE_CAPABILITY_BUNDLES,
    INTERFACE_CAPABILITY_PARTICIPATION,
    INTERFACE_CAPABILITY_PROFILES,
    INTERFACE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    INTERFACE_ENDPOINT_OWNER,
    INTERFACE_LAYOUT_OWNER,
    INTERFACE_MOUNT_OWNER,
    INTERFACE_NARRATIVE_OWNER,
    INTERFACE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    INTERFACE_PACKAGE_CAPABILITY_PARTICIPATION,
    INTERFACE_PACKAGE_CAPABILITY_PROFILES,
    INTERFACE_PANE_COMPOSITION_OWNER,
    INTERFACE_PANE_OWNER,
    INTERFACE_ROOT_OWNER,
    INTERFACE_SECTION_OWNER,
    INTERFACE_SEMANTIC_SCOPE_KEYS,
    INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
    INTERFACE_VIEW_OWNER,
    INTERFACE_WINDOW_OWNER,
    PANE_DIAGNOSTICS_CAPABILITY_PROFILES,
    PANE_PACKAGE_CAPABILITY_PARTICIPATION,
    PANE_PACKAGE_CAPABILITY_PROFILES,
    PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)


class _InterfaceSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_interface"

    def resolve(
        self, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        manifest_kind = code_package.metadata.get("manifest_kind")
        if manifest_kind == "aware_interface_toml":
            return (
                SemanticPackageDescriptor(
                    provider_key=self.provider_key,
                    family="interface",
                    semantic_kind="interface_package",
                    package_name=code_package.name,
                    manifest_relative_path=code_package.manifest_path.as_posix(),
                    metadata={
                        "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                        "package_kind": code_package.metadata.get("package_kind"),
                        "config_bundle_path": code_package.metadata.get(
                            "config_bundle_path"
                        ),
                        "workspace_materialization_primary": True,
                        "workspace_materialization_order": 600,
                        "workspace_materialization_branch": "semantic",
                        "workspace_materialization_commit": True,
                        "workspace_materialization_runtime_index": "workspace_experience",
                        "semantic_projection_name": "InterfacePackage",
                        "semantic_root_kind": "interface_config",
                    },
                    semantic_scope_keys=AWARE_INTERFACE_SEMANTIC_CONTRACT.semantic_scope_keys,
                    capability_participation=INTERFACE_PACKAGE_CAPABILITY_PARTICIPATION,
                    capability_profiles=INTERFACE_PACKAGE_CAPABILITY_PROFILES,
                    capability_bundles=INTERFACE_CAPABILITY_BUNDLES,
                ),
            )
        if manifest_kind == "aware_pane_toml":
            return (
                SemanticPackageDescriptor(
                    provider_key=self.provider_key,
                    family="interface",
                    semantic_kind="pane_package",
                    package_name=code_package.name,
                    manifest_relative_path=code_package.manifest_path.as_posix(),
                    metadata={
                        "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                        "package_kind": code_package.metadata.get("package_kind"),
                        "pane_name": code_package.metadata.get("pane_name"),
                        "workspace_materialization_primary": True,
                        "workspace_materialization_order": 500,
                        "workspace_materialization_branch": "none",
                        "workspace_materialization_commit": False,
                        "semantic_projection_name": "PanePackage",
                        "semantic_root_kind": "pane_package",
                    },
                    semantic_scope_keys=AWARE_INTERFACE_SEMANTIC_CONTRACT.semantic_scope_keys,
                    capability_participation=PANE_PACKAGE_CAPABILITY_PARTICIPATION,
                    capability_profiles=PANE_PACKAGE_CAPABILITY_PROFILES,
                    capability_bundles=INTERFACE_CAPABILITY_BUNDLES,
                ),
            )
        if manifest_kind == "aware_app_toml":
            return (
                SemanticPackageDescriptor(
                    provider_key=self.provider_key,
                    family="interface",
                    semantic_kind="app_package",
                    package_name=code_package.name,
                    manifest_relative_path=code_package.manifest_path.as_posix(),
                    metadata={
                        "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                        "package_kind": code_package.metadata.get("package_kind"),
                        "app_name": code_package.metadata.get("app_name"),
                        "dart_package_name": code_package.metadata.get(
                            "dart_package_name"
                        ),
                        "dart_package_path": code_package.metadata.get(
                            "dart_package_path"
                        ),
                        "dart_entrypoint": code_package.metadata.get("dart_entrypoint"),
                        "platforms": code_package.metadata.get("platforms"),
                        "platform_runners": code_package.metadata.get(
                            "platform_runners"
                        ),
                        "workspace_materialization_primary": True,
                        "workspace_materialization_order": 700,
                        "workspace_materialization_branch": "semantic",
                        "workspace_materialization_commit": True,
                        "workspace_materialization_runtime_index": (
                            "workspace_experience"
                        ),
                        "semantic_projection_name": "AppPackage",
                        "semantic_root_kind": "app_package",
                    },
                    semantic_scope_keys=AWARE_INTERFACE_SEMANTIC_CONTRACT.semantic_scope_keys,
                    capability_participation=INTERFACE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
                    capability_profiles=(),
                    capability_bundles=(),
                ),
            )
        return ()


_PROVIDER = _InterfaceSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_INTERFACE_SEMANTIC_CONTRACT",
    "INTERFACE_API_OWNER",
    "INTERFACE_CAPABILITY_PARTICIPATION",
    "INTERFACE_CAPABILITY_BUNDLES",
    "INTERFACE_CAPABILITY_PROFILES",
    "INTERFACE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "INTERFACE_ENDPOINT_OWNER",
    "INTERFACE_LAYOUT_OWNER",
    "INTERFACE_MOUNT_OWNER",
    "INTERFACE_NARRATIVE_OWNER",
    "INTERFACE_PANE_COMPOSITION_OWNER",
    "INTERFACE_PANE_OWNER",
    "INTERFACE_ROOT_OWNER",
    "INTERFACE_SECTION_OWNER",
    "INTERFACE_SEMANTIC_SCOPE_KEYS",
    "INTERFACE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "INTERFACE_VIEW_OWNER",
    "INTERFACE_WINDOW_OWNER",
    "PANE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "PANE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "register_semantic_package_providers",
]
