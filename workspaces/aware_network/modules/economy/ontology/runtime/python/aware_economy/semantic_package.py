from __future__ import annotations

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)


class _EconomySemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_economy"

    def resolve(self, code_package: CodePackageInfo) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_economy_toml":
            return ()
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="economy",
                semantic_kind="economy_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata={
                    "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                    "package_kind": code_package.metadata.get("package_kind"),
                    "workspace_materialization_primary": True,
                    "workspace_materialization_order": 800,
                    "workspace_materialization_branch": "semantic",
                    "workspace_materialization_commit": True,
                    "semantic_projection_name": "EconomyPackage",
                    "semantic_root_kind": "economy_package",
                },
            ),
        )


_PROVIDER = _EconomySemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = ["register_semantic_package_providers"]
