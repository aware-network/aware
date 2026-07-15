from __future__ import annotations

from pathlib import Path

from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipClaim,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
    WorkspaceSemanticArtifactProduction,
)
from aware_ontology.manifest.loader import load_aware_ontology_toml_spec


_OWNER_MANIFEST_KIND = "aware_ontology_toml"
_PYPROJECT_MANIFEST_KIND = "pyproject_toml"


def resolve_workspace_semantic_artifact_leaf_ownership(
    *,
    request: WorkspaceSemanticArtifactLeafOwnershipRequest,
) -> WorkspaceSemanticArtifactLeafOwnershipClaim | None:
    """Resolve Ontology-owned Python package leaves for Workspace."""

    owner = request.owner
    leaf = request.leaf
    if owner.semantic_contract_provider_key != "aware_ontology":
        return None
    if owner.manifest_kind != _OWNER_MANIFEST_KIND:
        return None
    if leaf.manifest_kind != _PYPROJECT_MANIFEST_KIND:
        return None

    owner_manifest_relative_path = _normalize_repo_path(owner.manifest_relative_path)
    owner_package_root = _normalize_repo_path(owner.package_root)
    leaf_package_root = _normalize_repo_path(leaf.package_root)
    if (
        owner_manifest_relative_path is None
        or owner_package_root is None
        or leaf_package_root is None
    ):
        return None

    spec = load_aware_ontology_toml_spec(
        toml_path=(request.workspace_root / owner_manifest_relative_path).resolve()
    )
    expected_package_root = _generated_python_package_root(
        owner_package_root=owner_package_root,
        source_manifest=spec.ontology.source_manifest,
    )
    if expected_package_root is not None and leaf_package_root == expected_package_root:
        return _claim(
            owner_manifest_relative_path=owner_manifest_relative_path,
            leaf=leaf,
            leaf_package_root=leaf_package_root,
            ownership_role="semantic_generated_artifact",
            producer_key="aware_ontology.language_materialization",
            producer_kind="generated_language_package",
            provider_payload={
                "source_manifest": spec.ontology.source_manifest,
                "source_package_name": spec.ontology.package_name,
                "target_language": "python",
            },
        )

    runtime = spec.runtime
    runtime_package_root = (
        None
        if runtime is None
        else _runtime_python_package_root(
            owner_package_root=owner_package_root,
            runtime_manifest=runtime.manifest,
        )
    )
    if (
        runtime is not None
        and runtime_package_root is not None
        and leaf_package_root == runtime_package_root
        and leaf.package_name == runtime.project_name
    ):
        return _claim(
            owner_manifest_relative_path=owner_manifest_relative_path,
            leaf=leaf,
            leaf_package_root=leaf_package_root,
            ownership_role="semantic_runtime_handler_package",
            producer_key="aware_ontology.runtime_handler_package",
            producer_kind="declared_runtime_package",
            provider_payload={
                "runtime_manifest": runtime.manifest,
                "runtime_project_name": runtime.project_name,
                "runtime_import_root": runtime.import_root,
                "source_package_name": spec.ontology.package_name,
            },
        )

    return None


def _generated_python_package_root(
    *,
    owner_package_root: str,
    source_manifest: str,
) -> str | None:
    source_manifest_path = _safe_join_relative(
        base=Path(owner_package_root),
        relative=source_manifest,
    )
    if source_manifest_path is None:
        return None
    return (source_manifest_path.parent / "python").as_posix()


def _runtime_python_package_root(
    *,
    owner_package_root: str,
    runtime_manifest: str,
) -> str | None:
    runtime_manifest_path = _safe_join_relative(
        base=Path(owner_package_root),
        relative=runtime_manifest,
    )
    if runtime_manifest_path is None:
        return None
    return runtime_manifest_path.parent.as_posix()


def _claim(
    *,
    owner_manifest_relative_path: str,
    leaf: WorkspaceSemanticArtifactBinding,
    leaf_package_root: str,
    ownership_role: str,
    producer_key: str,
    producer_kind: str,
    provider_payload: dict[str, object],
) -> WorkspaceSemanticArtifactLeafOwnershipClaim:
    return WorkspaceSemanticArtifactLeafOwnershipClaim(
        owned=True,
        owner_semantic_package_manifest=owner_manifest_relative_path,
        ownership_role=ownership_role,
        artifact_manifest_kind=leaf.manifest_kind,
        artifact_package_root=leaf_package_root,
        production=WorkspaceSemanticArtifactProduction(
            provider_key="aware_ontology",
            producer_key=producer_key,
            producer_kind=producer_kind,
            provider_payload=provider_payload,
        ),
    )


def _safe_join_relative(*, base: Path, relative: str) -> Path | None:
    path = Path(relative.strip())
    if path.is_absolute() or _has_unsafe_path_part(path):
        return None
    return base / path


def _normalize_repo_path(value: str) -> str | None:
    path = Path(value.strip())
    if not value.strip() or path.is_absolute() or _has_unsafe_path_part(path):
        return None
    return path.as_posix()


def _has_unsafe_path_part(path: Path) -> bool:
    return any(part in {"", ".", ".."} for part in path.parts)


__all__ = ["resolve_workspace_semantic_artifact_leaf_ownership"]
