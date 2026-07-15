from __future__ import annotations

from pathlib import Path

from aware_code.semantic_capability import SemanticAnalysisCapabilityRequest
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_node_package_fixture(*, workspace_root: Path) -> Path:
    node_toml_path = workspace_root / "aware.node.toml"
    _write(
        node_toml_path,
        "\n".join(
            [
                "aware_node = 1",
                "",
                "[node]",
                'package_name = "kernel-node"',
                'fqn_prefix = "aware_kernel_node"',
                "version_number = 11",
                'title = "Kernel Node"',
                'description = "Canonical node package"',
                "",
                "[build]",
                'sources_dir = "nodes"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "node_ontology"',
                "",
                "[[dependencies]]",
                'package_name = "kernel-environment"',
                'kind = "environment_package"',
                "",
                "[[dependencies]]",
                'package_name = "aware-attention-service"',
                'kind = "service_package"',
                "",
                "[[dependencies]]",
                'package_name = "aware-workspace-interface"',
                'kind = "interface_package"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "nodes" / "kernel_node.aware",
        "\n".join(
            [
                "node kernel_host {",
                "    environment kernel {",
                "        profile os.default package aware-workspace-environment-profile",
                "    }",
                "    service aware_attention;",
                "    interface aware_workspace;",
                "}",
                "",
            ]
        ),
    )
    return node_toml_path


def test_node_semantic_analysis_emits_delta_contract(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "node_semantic_analysis"
    workspace_root.mkdir(parents=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    from aware_node.semantic_analysis import analyze_node_semantic_capability

    result = analyze_node_semantic_capability(
        SemanticAnalysisCapabilityRequest(
            package_root=workspace_root,
            source_files=(Path("nodes/kernel_node.aware"),),
            manifest_path=node_toml_path,
            workspace_root=workspace_root,
            code_package_delta=CodePackageDelta(
                package_name="kernel-node",
                package_root=".",
                sources_root="nodes",
                manifest_relative_path="aware.node.toml",
                paths=[
                    CodePackageDeltaPath(
                        relative_path="nodes/kernel_node.aware",
                        kind=CodePackageDeltaKind.update,
                    )
                ],
            ),
        )
    )

    assert result.provider_key == "aware_node"
    assert result.semantic_owner == "aware_node.provider"
    assert result.diagnostics == ()
    preview = result.change_preview
    assert preview.changed_source_files == ("nodes/kernel_node.aware",)
    assert preview.affected_semantic_keys == ("node_package:kernel-node",)
    assert preview.required_materializations == (
        "node_compile_plan",
        "node_package_plan",
    )
    assert {delta.subject_type for delta in preview.semantic_deltas} == {
        "aware_node.NodePackage",
        "aware_node.NodeConfig",
        "aware_node.NodeConfigEnvironmentTarget",
        "aware_node.NodeConfigServiceTarget",
        "aware_node.NodeConfigInterfaceTarget",
    }
    assert {
        dependency.provider_key for dependency in preview.required_semantic_dependencies
    } == {
        "aware_environment",
        "aware_service",
        "aware_interface",
    }
    assert {
        dependency.manifest_kind
        for dependency in preview.required_semantic_dependencies
    } == {
        "aware_environment_toml",
        "aware_service_toml",
        "aware_interface_toml",
    }
    dependencies_by_provider = {
        dependency.provider_key: dependency
        for dependency in preview.required_semantic_dependencies
    }
    assert dependencies_by_provider["aware_environment"].package_selector == {
        "semantic_package_family": "environment",
        "semantic_package_name": "kernel-environment",
    }
    assert (
        dependencies_by_provider["aware_environment"].semantic_owner
        == "aware_environment.environment_config.provider"
    )
    assert dependencies_by_provider["aware_service"].package_selector == {
        "semantic_package_family": "service",
        "semantic_package_name": "aware-attention-service",
    }
    assert dependencies_by_provider["aware_interface"].package_selector == {
        "semantic_package_family": "interface",
        "semantic_package_name": "aware-workspace-interface",
    }
    assert preview.metadata["environment_target_count"] == 1
    assert preview.metadata["service_target_count"] == 1
    assert preview.metadata["interface_target_count"] == 1
