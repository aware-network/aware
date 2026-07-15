from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology_package_dependency import OntologyPackageDependency

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Ontology Ontology
from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
from aware_ontology_ontology.stable_ids import stable_ontology_package_dependency_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_ontology_package(
    ontology_package_id: UUID,
    target_ontology_package_id: UUID,
    target_package_name: str,
    target_ontology_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> OntologyPackageDependency:
    """
    Attach one ontology package dependency.

    Contract:
    - Parent `OntologyPackage` scope is injected by propagation.
    - Identity is keyed by the target `OntologyPackage`.
    - The optional OIG commit pin is the exact reproducibility authority for
      WorkspaceRevision and Hub consumers.
    """

    # --- AWARE: LOGIC START build_via_ontology_package
    normalized_target_package_name = (target_package_name or "").strip()
    if not normalized_target_package_name:
        raise RuntimeError(
            "OntologyPackageDependency.build_via_ontology_package requires " "non-empty target_package_name"
        )
    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None and (
        len(normalized_expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_expected_hash)
    ):
        raise RuntimeError(
            "OntologyPackageDependency.expected_hash_sha256 must be a lowercase " "64-character SHA-256 hex digest"
        )

    dependency_id = stable_ontology_package_dependency_id(
        ontology_package_id=ontology_package_id,
        target_ontology_package_id=target_ontology_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_target_package = (
        session.imap_get(OntologyPackage, target_ontology_package_id) if session is not None else None
    )
    resolved_target_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            target_ontology_package_object_instance_graph_commit_id,
        )
        if session is not None and target_ontology_package_object_instance_graph_commit_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(OntologyPackageDependency, dependency_id)
        if existing is not None:
            if (
                existing.ontology_package_id != ontology_package_id
                or existing.target_ontology_package_id != target_ontology_package_id
            ):
                raise RuntimeError(
                    "OntologyPackageDependency.build_via_ontology_package payload "
                    f"mismatch for ontology_package_dependency_id={dependency_id}"
                )
            if (
                target_ontology_package_object_instance_graph_commit_id is not None
                and existing.target_ontology_package_object_instance_graph_commit_id
                not in {
                    None,
                    target_ontology_package_object_instance_graph_commit_id,
                }
            ):
                raise RuntimeError(
                    "OntologyPackageDependency.build_via_ontology_package target "
                    "commit mismatch for "
                    f"ontology_package_dependency_id={dependency_id}"
                )
            existing.target_package_name = normalized_target_package_name
            if target_ontology_package_object_instance_graph_commit_id is not None:
                existing.target_ontology_package_object_instance_graph_commit_id = (
                    target_ontology_package_object_instance_graph_commit_id
                )
                existing.target_ontology_package_object_instance_graph_commit = resolved_target_commit
            if existing.target_ontology_package is None:
                existing.target_ontology_package = resolved_target_package
            existing.target_version_number = target_version_number
            existing.expected_hash_sha256 = normalized_expected_hash
            existing.description = (description or "").strip() or None
            return existing

    return OntologyPackageDependency.model_construct(
        id=dependency_id,
        ontology_package_id=ontology_package_id,
        target_ontology_package=resolved_target_package,
        target_ontology_package_id=target_ontology_package_id,
        target_ontology_package_object_instance_graph_commit=resolved_target_commit,
        target_ontology_package_object_instance_graph_commit_id=(
            target_ontology_package_object_instance_graph_commit_id
        ),
        target_package_name=normalized_target_package_name,
        target_version_number=target_version_number,
        expected_hash_sha256=normalized_expected_hash,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_ontology_package
