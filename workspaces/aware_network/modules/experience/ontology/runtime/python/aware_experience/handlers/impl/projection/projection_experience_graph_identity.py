from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph_identity import ProjectionExperienceGraphIdentity
from aware_experience_ontology.projection.projection_experience_graph_identity_profile import (
    ProjectionExperienceGraphIdentityProfile,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_projection_experience_graph_identity_id,
    stable_projection_experience_graph_identity_profile_id,
)

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph import ProjectionExperienceGraph

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_profile(
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity,
    review_label: str,
    resolution_prompts: list[str] = [],
    aliases: list[str] = [],
    summary: str | None = None,
    notes: str | None = None,
) -> ProjectionExperienceGraphIdentityProfile:
    """
    Attach the canonical graph-identity profile under this ProjectionExperienceGraphIdentity.

    Contract:
    - Graph occurrence identity is the canonical anchor for profile truth.
    - The profile remains Experience-owned and perception-agnostic.
    - Future API/Service rails should consume this profile rather than direct ontology search.
    """

    # --- AWARE: LOGIC START create_profile
    projection_experience_graph_identity_id = projection_experience_graph_identity.id
    if projection_experience_graph_identity_id is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentity.create_profile requires ProjectionExperienceGraphIdentity.id"
        )

    existing = projection_experience_graph_identity.projection_experience_graph_identity_profile
    if existing is None:
        session = current_handler_session()
        expected_profile_id = stable_projection_experience_graph_identity_profile_id(
            projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        )
        existing = session.imap_get(ProjectionExperienceGraphIdentityProfile, expected_profile_id)
    if existing is not None:
        projection_experience_graph_identity.projection_experience_graph_identity_profile = existing
        return existing

    created = await ProjectionExperienceGraphIdentityProfile.build_via_projection_experience_graph_identity(
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        review_label=review_label,
        resolution_prompts=resolution_prompts,
        aliases=aliases,
        summary=summary,
        notes=notes,
    )

    projection_experience_graph_identity.projection_experience_graph_identity_profile = created
    return created
    # --- AWARE: LOGIC END create_profile


async def build_via_projection_experience_graph(
    projection_experience_graph_id: UUID, projection_experience_node_identity_id: UUID, key: str, is_root: bool = False
) -> ProjectionExperienceGraphIdentity:
    """
    Create deterministic ProjectionExperienceGraphIdentity.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_graph
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentity.build_via_projection_experience_graph requires non-empty key"
        )

    session = current_handler_session()
    projection_experience_graph = session.imap_get(ProjectionExperienceGraph, projection_experience_graph_id)
    if projection_experience_graph is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentity.build_via_projection_experience_graph requires known "
            + f"ProjectionExperienceGraph: projection_experience_graph_id={projection_experience_graph_id}"
        )

    projection_experience_graph_identity_id = stable_projection_experience_graph_identity_id(
        projection_experience_graph_id=projection_experience_graph_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=normalized_key,
    )
    existing = session.imap_get(
        ProjectionExperienceGraphIdentity,
        projection_experience_graph_identity_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_graph_id != projection_experience_graph_id
            or existing.projection_experience_node_identity_id != projection_experience_node_identity_id
            or existing.key != normalized_key
            or existing.is_root != is_root
        ):
            raise RuntimeError(
                "ProjectionExperienceGraphIdentity.build_via_projection_experience_graph payload mismatch "
                + "for existing identity: "
                + f"projection_experience_graph_identity_id={projection_experience_graph_identity_id}"
            )
        return existing

    return ProjectionExperienceGraphIdentity(
        id=projection_experience_graph_identity_id,
        projection_experience_graph_id=projection_experience_graph_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        key=normalized_key,
        is_root=is_root,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_graph
