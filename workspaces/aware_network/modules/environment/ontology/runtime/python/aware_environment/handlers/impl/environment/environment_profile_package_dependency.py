from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.environment.environment_profile_package_dependency import (
    EnvironmentProfilePackageDependency,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_environment_ontology.environment.environment_profile_package import (
    EnvironmentProfilePackage,
)
from aware_environment_ontology.stable_ids import (
    stable_environment_profile_package_dependency_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_profile_package(
    environment_profile_package_id: UUID,
    target_environment_profile_package_id: UUID,
    target_package_name: str,
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> EnvironmentProfilePackageDependency:
    """
    Create one package-level EnvironmentProfilePackage dependency edge.

    Contract:
    - Parent `EnvironmentProfilePackage` scope is injected by propagation.
    - Identity is keyed by the target package.
    - `target_package_name` is retained as authored selector text.
    - The optional OIG commit pin is the exact reproducibility authority for
      WorkspaceRevision and Hub consumers.
    """

    # --- AWARE: LOGIC START build_via_environment_profile_package
    normalized_target_package_name = (target_package_name or "").strip()
    if not normalized_target_package_name:
        raise RuntimeError(
            "EnvironmentProfilePackageDependency.build_via_environment_profile_package "
            "requires non-empty target_package_name"
        )

    dependency_id = stable_environment_profile_package_dependency_id(
        environment_profile_package_id=environment_profile_package_id,
        target_environment_profile_package_id=target_environment_profile_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_target_package = (
        session.imap_get(
            EnvironmentProfilePackage,
            target_environment_profile_package_id,
        )
        if session is not None
        else None
    )
    resolved_target_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            target_environment_profile_package_object_instance_graph_commit_id,
        )
        if session is not None and target_environment_profile_package_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(
            EnvironmentProfilePackageDependency,
            dependency_id,
        )
        if existing is not None:
            if existing.environment_profile_package_id != environment_profile_package_id:
                raise RuntimeError(
                    "EnvironmentProfilePackageDependency.build parent mismatch " f"for dependency_id={dependency_id}"
                )
            if existing.target_environment_profile_package_id != target_environment_profile_package_id:
                raise RuntimeError(
                    "EnvironmentProfilePackageDependency.build target mismatch " f"for dependency_id={dependency_id}"
                )
            if target_environment_profile_package_object_instance_graph_commit_id is not None:
                existing_commit_id = existing.target_environment_profile_package_object_instance_graph_commit_id
                if existing_commit_id is None:
                    existing.target_environment_profile_package_object_instance_graph_commit_id = (
                        target_environment_profile_package_object_instance_graph_commit_id
                    )
                    existing.target_environment_profile_package_object_instance_graph_commit = (
                        resolved_target_oig_commit
                    )
                elif existing_commit_id != target_environment_profile_package_object_instance_graph_commit_id:
                    raise RuntimeError(
                        "EnvironmentProfilePackageDependency.build target OIG commit mismatch "
                        f"for dependency_id={dependency_id} "
                        f"existing={existing_commit_id} "
                        "provided="
                        f"{target_environment_profile_package_object_instance_graph_commit_id}"
                    )
            existing.target_package_name = normalized_target_package_name
            existing.target_version_number = target_version_number
            existing.expected_hash_sha256 = (expected_hash_sha256 or "").strip() or None
            existing.description = (description or "").strip() or None
            return existing

    return EnvironmentProfilePackageDependency(
        id=dependency_id,
        environment_profile_package_id=environment_profile_package_id,
        target_environment_profile_package=resolved_target_package,
        target_environment_profile_package_id=target_environment_profile_package_id,
        target_environment_profile_package_object_instance_graph_commit=(resolved_target_oig_commit),
        target_environment_profile_package_object_instance_graph_commit_id=(
            target_environment_profile_package_object_instance_graph_commit_id
        ),
        target_package_name=normalized_target_package_name,
        target_version_number=target_version_number,
        expected_hash_sha256=(expected_hash_sha256 or "").strip() or None,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_environment_profile_package
