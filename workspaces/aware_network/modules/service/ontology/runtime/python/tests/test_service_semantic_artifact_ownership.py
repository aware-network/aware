from __future__ import annotations

from pathlib import Path

from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
)
from aware_service_runtime.semantic_artifact_ownership import (
    resolve_workspace_semantic_artifact_leaf_ownership,
)


def test_service_semantic_artifact_ownership_claims_implementation_pyproject(
    tmp_path: Path,
) -> None:
    service_root = tmp_path / "services" / "environment"
    service_root.mkdir(parents=True)
    (service_root / "aware.service.toml").write_text(
        "\n".join(
            (
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-environment-service"',
                'fqn_prefix = "aware_environment_service"',
                "",
                "[build]",
                'compilation_mode = "service_ontology"',
                "",
                "[implementation]",
                "",
                "[[implementation.packages]]",
                'package_name = "aware-environment-service"',
                'language = "python"',
                'import_root = "aware_environment_service"',
                'manifest_path = "pyproject.toml"',
                'package_root = "."',
                'role = "service_bindings"',
                "",
            )
        ),
        encoding="utf-8",
    )
    (service_root / "pyproject.toml").write_text(
        '[project]\nname = "aware-environment-service"\n',
        encoding="utf-8",
    )

    claim = resolve_workspace_semantic_artifact_leaf_ownership(
        request=WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=tmp_path,
            owner=WorkspaceSemanticArtifactBinding(
                module_id=None,
                package_name="aware-environment-service",
                language="aware",
                surface="service",
                manifest_kind="aware_service_toml",
                manifest_relative_path="services/environment/aware.service.toml",
                package_root="services/environment",
                sources_root="services/environment/bindings",
                package_kind="service",
                semantic_contract_provider_key="aware_service",
                semantic_contract_role="aware_service.provider",
                semantic_contract_name="aware.semantic_provider",
                semantic_contract_module="aware_service_runtime.semantic_contract",
            ),
            leaf=WorkspaceSemanticArtifactBinding(
                module_id=None,
                package_name="aware-environment-service",
                language="python",
                surface="runtime",
                manifest_kind="pyproject_toml",
                manifest_relative_path="services/environment/pyproject.toml",
                package_root="services/environment",
                sources_root="services/environment",
                package_kind="python_package",
            ),
        )
    )

    assert claim is not None
    assert claim.owned is True
    assert claim.ownership_role == "service_implementation_package"
    assert claim.artifact_package_root == "services/environment"
    assert claim.production is not None
    assert claim.production.provider_key == "aware_service"


def test_service_semantic_artifact_ownership_rejects_unlisted_pyproject(
    tmp_path: Path,
) -> None:
    service_root = tmp_path / "services" / "environment"
    other_root = tmp_path / "services" / "environment" / "tools"
    service_root.mkdir(parents=True)
    other_root.mkdir(parents=True)
    (service_root / "aware.service.toml").write_text(
        "\n".join(
            (
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-environment-service"',
                'fqn_prefix = "aware_environment_service"',
                "",
                "[build]",
                'compilation_mode = "service_ontology"',
                "",
                "[implementation]",
                "",
                "[[implementation.packages]]",
                'package_name = "aware-environment-service"',
                'language = "python"',
                'import_root = "aware_environment_service"',
                'manifest_path = "pyproject.toml"',
                'package_root = "."',
                "",
            )
        ),
        encoding="utf-8",
    )

    claim = resolve_workspace_semantic_artifact_leaf_ownership(
        request=WorkspaceSemanticArtifactLeafOwnershipRequest(
            workspace_root=tmp_path,
            owner=WorkspaceSemanticArtifactBinding(
                module_id=None,
                package_name="aware-environment-service",
                language="aware",
                surface="service",
                manifest_kind="aware_service_toml",
                manifest_relative_path="services/environment/aware.service.toml",
                package_root="services/environment",
                sources_root="services/environment/bindings",
                semantic_contract_provider_key="aware_service",
            ),
            leaf=WorkspaceSemanticArtifactBinding(
                module_id=None,
                package_name="tooling",
                language="python",
                surface="runtime",
                manifest_kind="pyproject_toml",
                manifest_relative_path="services/environment/tools/pyproject.toml",
                package_root="services/environment/tools",
                sources_root="services/environment/tools",
            ),
        )
    )

    assert claim is None
