from __future__ import annotations

from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import SemanticScopeRegistry
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_node.semantic_scope import (
    NODE_SEMANTIC_SCOPE_KEY,
    register_semantic_scope_providers,
)


def test_node_semantic_scope_emits_manifest_dependency_refs(tmp_path: Path) -> None:
    manifest_path = _write_node_manifest(tmp_path)
    register_semantic_scope_providers()

    resolutions = SemanticScopeRegistry.resolve(
        CodePackageInfo(
            name="kernel-node",
            root_path=Path("."),
            manifest_path=manifest_path.relative_to(tmp_path),
            language=CodeLanguage.aware,
            metadata={"manifest_kind": "aware_node_toml"},
        ),
        workspace_root=tmp_path,
        provider_keys=("aware_node",),
    )

    assert len(resolutions) == 1
    assert resolutions[0].scope_key == NODE_SEMANTIC_SCOPE_KEY
    dependencies_by_package = {
        dependency.package_name: dependency
        for dependency in resolutions[0].materialization_dependencies
    }
    service_dependency = dependencies_by_package["home-story-service"]
    assert service_dependency.provider_key == "aware_service"
    assert service_dependency.manifest_kind == "aware_service_toml"
    assert service_dependency.semantic_package_family == "service"
    assert service_dependency.semantic_package_kind == "service_package"
    generic_dependency = dependencies_by_package["shared-support-package"]
    assert generic_dependency.provider_key is None
    assert generic_dependency.dependency_kind == "semantic_package"


def _write_node_manifest(root: Path) -> Path:
    manifest_path = root / "aware.node.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware_node = 1",
                "",
                "[node]",
                'package_name = "kernel-node"',
                'fqn_prefix = "aware_kernel_node"',
                "",
                "[build]",
                'sources_dir = "nodes"',
                'include_paths = ["**/*.aware"]',
                "",
                "[[dependencies]]",
                'package_name = "home-story-service"',
                'kind = "service_package"',
                "",
                "[[dependencies]]",
                'package_name = "shared-support-package"',
                'kind = "package"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path
