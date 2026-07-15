from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)
from aware_node.semantic_contract import AWARE_NODE_SEMANTIC_CONTRACT


class _NodeSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_node"

    def resolve(
        self, code_package: CodePackageInfo
    ) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_node_toml":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="node",
                semantic_kind="node_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "package_kind": code_package.metadata.get("package_kind"),
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 700,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": True,
                    "semantic_projection_name": "NodePackage",
                    "semantic_root_kind": "node_config",
                },
                capability_participation=(
                    AWARE_NODE_SEMANTIC_CONTRACT.capability_participation
                ),
            ),
        )


_PROVIDER = _NodeSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_NODE_SEMANTIC_CONTRACT",
    "register_semantic_package_providers",
]
