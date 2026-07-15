from __future__ import annotations

from pathlib import Path

from aware_code.module_semantic_contract import (
    WorkspaceSemanticArtifactBinding,
    WorkspaceSemanticArtifactLeafOwnershipClaim,
    WorkspaceSemanticArtifactLeafOwnershipRequest,
    WorkspaceSemanticArtifactProduction,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec


def resolve_workspace_semantic_artifact_leaf_ownership(
    *,
    request: WorkspaceSemanticArtifactLeafOwnershipRequest,
) -> WorkspaceSemanticArtifactLeafOwnershipClaim | None:
    """Resolve Service-owned implementation package leaves for Workspace."""

    owner = request.owner
    leaf = request.leaf
    if owner.semantic_contract_provider_key != "aware_service":
        return None
    if owner.manifest_kind != "aware_service_toml":
        return None
    if leaf.manifest_kind != "pyproject_toml":
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

    spec = load_aware_service_toml_spec(
        toml_path=(request.workspace_root / owner_manifest_relative_path).resolve()
    )
    for implementation in spec.implementation.packages:
        implementation_package_root = _join_repo_path(
            owner_package_root,
            implementation.package_root,
        )
        if implementation_package_root != leaf_package_root:
            continue
        return WorkspaceSemanticArtifactLeafOwnershipClaim(
            owned=True,
            owner_semantic_package_manifest=owner_manifest_relative_path,
            ownership_role="service_implementation_package",
            artifact_manifest_kind=leaf.manifest_kind,
            artifact_package_root=leaf_package_root,
            production=_service_implementation_artifact_production(
                owner=owner,
                leaf=leaf,
                implementation_role=_enum_value_text(implementation.role),
            ),
        )
    return None


def _service_implementation_artifact_production(
    *,
    owner: WorkspaceSemanticArtifactBinding,
    leaf: WorkspaceSemanticArtifactBinding,
    implementation_role: str,
) -> WorkspaceSemanticArtifactProduction:
    return WorkspaceSemanticArtifactProduction(
        provider_key="aware_service",
        producer_key="aware_service.implementation_package",
        producer_kind="service_implementation_package",
        provider_payload={
            "owner_manifest_kind": owner.manifest_kind,
            "artifact_manifest_kind": leaf.manifest_kind,
            "implementation_role": implementation_role,
        },
    )


def _normalize_repo_path(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    normalized = Path(text).as_posix().strip("/")
    return normalized or "."


def _join_repo_path(*parts: str) -> str | None:
    normalized_parts = tuple(
        part
        for part in (_normalize_repo_path(value) for value in parts)
        if part is not None and part != "."
    )
    if not normalized_parts:
        return "."
    return Path(*normalized_parts).as_posix()


def _enum_value_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value)


__all__ = ["resolve_workspace_semantic_artifact_leaf_ownership"]
