from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.experience_package_dependency import ExperiencePackageDependency

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_dependency_id
from aware_experience_ontology.environment.experience_package import ExperiencePackage

# Meta Ontology
from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_package(
    experience_package_id: UUID,
    target_experience_package_id: UUID,
    target_package_name: str,
    target_experience_package_object_instance_graph_commit_id: UUID | None = None,
    target_version_number: int | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ExperiencePackageDependency:
    """
    Create one package-level Experience dependency edge.

    Contract:
    - Parent `ExperiencePackage` scope is injected by propagation.
    - Identity is keyed by the target `ExperiencePackage`.
    - `target_package_name` is retained as authored selector text.
    - `target_version_number` is compatibility/selector metadata, not reproducibility authority.
    - `target_experience_package_object_instance_graph_commit_id`, when present, pins exact
      semantic package truth.
    - Cross-Experience transitions and profile composition may resolve only through this
      dependency closure.
    """

    # --- AWARE: LOGIC START build_via_experience_package
    normalized_target_package_name = (target_package_name or "").strip()
    if not normalized_target_package_name:
        raise RuntimeError("ExperiencePackageDependency.build_via_experience_package requires target_package_name")

    normalized_description = (description or "").strip() or None
    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None:
        if len(normalized_expected_hash) != 64 or any(c not in "0123456789abcdef" for c in normalized_expected_hash):
            raise RuntimeError(
                "ExperiencePackageDependency.build_via_experience_package expected_hash_sha256 must be 64 hex chars"
            )

    if target_version_number is not None and target_version_number < 1:
        raise RuntimeError(
            "ExperiencePackageDependency.build_via_experience_package target_version_number must be >= 1"
        )

    assoc_id = stable_experience_package_dependency_id(
        experience_package_id=experience_package_id,
        target_experience_package_id=target_experience_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(ExperiencePackageDependency, assoc_id)
        if existing is not None:
            if existing.experience_package_id != experience_package_id:
                raise RuntimeError(
                    "ExperiencePackageDependency.build_via_experience_package "
                    f"experience_package mismatch: assoc_id={assoc_id}"
                )
            if existing.target_experience_package_id != target_experience_package_id:
                raise RuntimeError(
                    "ExperiencePackageDependency.build_via_experience_package "
                    f"target_experience_package mismatch: assoc_id={assoc_id}"
                )
            if (existing.target_package_name or "").strip() != normalized_target_package_name:
                raise RuntimeError(
                    "ExperiencePackageDependency.build_via_experience_package "
                    f"target_package_name mismatch: assoc_id={assoc_id}"
                )
            if (
                target_experience_package_object_instance_graph_commit_id is not None
                and existing.target_experience_package_object_instance_graph_commit_id is not None
                and existing.target_experience_package_object_instance_graph_commit_id
                != target_experience_package_object_instance_graph_commit_id
            ):
                raise RuntimeError(
                    "ExperiencePackageDependency.build_via_experience_package "
                    f"commit pin mismatch: assoc_id={assoc_id}"
                )
            if target_experience_package_object_instance_graph_commit_id is not None:
                existing.target_experience_package_object_instance_graph_commit_id = (
                    target_experience_package_object_instance_graph_commit_id
                )
                existing.target_experience_package_object_instance_graph_commit = session.imap_get(
                    ObjectInstanceGraphCommit,
                    target_experience_package_object_instance_graph_commit_id,
                )
            if target_version_number is not None:
                if existing.target_version_number is None:
                    existing.target_version_number = target_version_number
                elif existing.target_version_number != target_version_number:
                    raise RuntimeError(
                        "ExperiencePackageDependency.build_via_experience_package "
                        f"target_version_number mismatch: assoc_id={assoc_id}"
                    )
            if normalized_expected_hash is not None:
                existing_hash = (existing.expected_hash_sha256 or "").strip().lower() or None
                if existing_hash is None:
                    existing.expected_hash_sha256 = normalized_expected_hash
                elif existing_hash != normalized_expected_hash:
                    raise RuntimeError(
                        "ExperiencePackageDependency.build_via_experience_package "
                        f"expected_hash_sha256 mismatch: assoc_id={assoc_id}"
                    )
            if normalized_description is not None:
                existing_description = (existing.description or "").strip() or None
                if existing_description is None:
                    existing.description = normalized_description
                elif existing_description != normalized_description:
                    raise RuntimeError(
                        "ExperiencePackageDependency.build_via_experience_package "
                        f"description mismatch: assoc_id={assoc_id}"
                    )
            return existing

        resolved_target_experience_package = session.imap_get(ExperiencePackage, target_experience_package_id)
        resolved_commit = (
            session.imap_get(
                ObjectInstanceGraphCommit,
                target_experience_package_object_instance_graph_commit_id,
            )
            if target_experience_package_object_instance_graph_commit_id is not None
            else None
        )
    else:
        resolved_target_experience_package = None
        resolved_commit = None

    return ExperiencePackageDependency.model_construct(
        id=assoc_id,
        experience_package_id=experience_package_id,
        target_experience_package_id=target_experience_package_id,
        target_experience_package=resolved_target_experience_package,
        target_experience_package_object_instance_graph_commit_id=(
            target_experience_package_object_instance_graph_commit_id
        ),
        target_experience_package_object_instance_graph_commit=resolved_commit,
        target_package_name=normalized_target_package_name,
        target_version_number=target_version_number,
        expected_hash_sha256=normalized_expected_hash,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_package
