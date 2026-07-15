from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_package_object_config_graph_package import (
    ServicePackageObjectConfigGraphPackage,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_service_ontology.stable_ids import (
    stable_service_package_object_config_graph_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_package(
    service_package_id: UUID,
    object_config_graph_package_id: UUID,
    manifest_relative_path: str,
    role: str = "local_state",
    package_kind: str = "state",
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ServicePackageObjectConfigGraphPackage:
    """
    Attach one Service-owned ObjectConfigGraphPackage to this ServicePackage.

    Contract:
    - Parent `ServicePackage` scope is injected by propagation.
    - Identity is keyed by the owned ObjectConfigGraphPackage.
    - `manifest_relative_path` preserves the Service-authored child package manifest path.
    - `object_config_graph_package_object_instance_graph_commit_id`, when present,
      pins the exact committed OCG package truth included in a WorkspaceRevision.
    """

    # --- AWARE: LOGIC START build_via_service_package
    normalized_manifest_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_path:
        raise RuntimeError(
            "ServicePackageObjectConfigGraphPackage.build_via_service_package " "requires manifest_relative_path"
        )
    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None and (
        len(normalized_expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_expected_hash)
    ):
        raise RuntimeError(
            "ServicePackageObjectConfigGraphPackage.expected_hash_sha256 must be a "
            "lowercase 64-character SHA-256 hex digest"
        )
    return ServicePackageObjectConfigGraphPackage(
        id=stable_service_package_object_config_graph_package_id(
            service_package_id=service_package_id,
            object_config_graph_package_id=object_config_graph_package_id,
        ),
        service_package_id=service_package_id,
        object_config_graph_package_id=object_config_graph_package_id,
        object_config_graph_package_object_instance_graph_commit_id=(
            object_config_graph_package_object_instance_graph_commit_id
        ),
        role=(role or "").strip() or "local_state",
        manifest_relative_path=normalized_manifest_path,
        package_kind=(package_kind or "").strip() or "state",
        expected_hash_sha256=normalized_expected_hash,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_service_package
