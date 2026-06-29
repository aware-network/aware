from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_package_dependency import SdkPackageDependency

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_package_dependency_id

# --- AWARE: USER_IMPORTS END


async def build_via_sdk_package(
    sdk_package_id: UUID,
    target_sdk_package_id: UUID,
    target_package_name: str,
    target_sdk_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> SdkPackageDependency:
    """
    Create one package-level SDK dependency edge.

    Contract:
    - Parent `SdkPackage` scope is injected by propagation.
    - Identity is keyed by the target `SdkPackage`; package name is retained as authored selector text.
    - `target_version_number` is compatibility/selector metadata, not reproducibility authority.
    - `target_sdk_package_object_instance_graph_commit_id`, when present, pins exact semantic package
    truth.
    - This bridge enables later SDK operation composition without turning API endpoints into
    orchestration truth.
    """

    # --- AWARE: LOGIC START build_via_sdk_package
    normalized_target_package_name = (target_package_name or "").strip()
    if not normalized_target_package_name:
        raise RuntimeError("SdkPackageDependency.build_via_sdk_package requires non-empty target_package_name")
    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None and (
        len(normalized_expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_expected_hash)
    ):
        raise RuntimeError(
            "SdkPackageDependency.expected_hash_sha256 must be a lowercase " + "64-character SHA-256 hex digest"
        )
    return SdkPackageDependency(
        id=stable_sdk_package_dependency_id(
            sdk_package_id=sdk_package_id,
            target_sdk_package_id=target_sdk_package_id,
        ),
        sdk_package_id=sdk_package_id,
        target_sdk_package_id=target_sdk_package_id,
        target_package_name=normalized_target_package_name,
        target_sdk_package_object_instance_graph_commit_id=(target_sdk_package_object_instance_graph_commit_id),
        target_version_number=target_version_number,
        expected_hash_sha256=normalized_expected_hash,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_sdk_package
