from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import SdkPackageObjectConfigGraphPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import (
    stable_sdk_package_object_config_graph_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_sdk_package(
    sdk_package_id: UUID,
    object_config_graph_package_id: UUID,
    manifest_relative_path: str,
    role: str = "local_state",
    package_kind: str = "state",
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> SdkPackageObjectConfigGraphPackage:
    """
    Attach one SDK-owned ObjectConfigGraphPackage to this SdkPackage.

    Contract:
    - Parent `SdkPackage` scope is injected by propagation.
    - Identity is keyed by the owned ObjectConfigGraphPackage.
    - `manifest_relative_path` preserves the SDK-authored child package manifest path.
    - `object_config_graph_package_object_instance_graph_commit_id`, when present,
      pins the exact committed OCG package truth included in a WorkspaceRevision.
    """

    # --- AWARE: LOGIC START build_via_sdk_package
    normalized_manifest_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_path:
        raise RuntimeError(
            "SdkPackageObjectConfigGraphPackage.build_via_sdk_package " "requires manifest_relative_path"
        )
    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None and (
        len(normalized_expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_expected_hash)
    ):
        raise RuntimeError(
            "SdkPackageObjectConfigGraphPackage.expected_hash_sha256 must be a "
            "lowercase 64-character SHA-256 hex digest"
        )
    return SdkPackageObjectConfigGraphPackage(
        id=stable_sdk_package_object_config_graph_package_id(
            sdk_package_id=sdk_package_id,
            object_config_graph_package_id=object_config_graph_package_id,
        ),
        sdk_package_id=sdk_package_id,
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
    # --- AWARE: LOGIC END build_via_sdk_package
