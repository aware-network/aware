from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_projection_experience_section_graph_binding_id
from aware_experience.graph.resolver import (
    projection_experience_exists_via_lane,
    projection_experience_graph_owns_graph_identity_via_lane,
    projection_experience_owns_view_via_lane,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience(
    projection_experience_id: UUID,
    layout_config_section_config_id: UUID,
    projection_experience_view_id: UUID,
    projection_experience_graph_identity_id: UUID,
    binding_key: str,
    section_key: str,
) -> ProjectionExperienceSectionGraphBinding:
    """
    Create deterministic ProjectionExperienceSectionGraphBinding under one ProjectionExperience.

    Contract:
    - `binding_key` is the stable service-facing coordination handle.
    - `layout_config_section_config` is the canonical portal to Attention-owned layout section truth.
    - `section_key` is a denormalized lookup/cache key for service filters and must match the target
    layout section.
    - `projection_experience_graph_identity` is the explicit occurrence anchor for lawful coordination.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    normalized_binding_key = (binding_key or "").strip()
    if not normalized_binding_key:
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires non-empty binding_key"
        )

    normalized_section_key = (section_key or "").strip()
    if not normalized_section_key:
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires non-empty section_key"
        )

    if not await projection_experience_exists_via_lane(projection_experience_id=projection_experience_id):
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires known "
            + f"ProjectionExperience: projection_experience_id={projection_experience_id}"
        )

    if not await projection_experience_owns_view_via_lane(projection_experience_view_id=projection_experience_view_id):
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires known "
            + f"ProjectionExperienceView: projection_experience_view_id={projection_experience_view_id}"
        )

    if not await projection_experience_graph_owns_graph_identity_via_lane(
        projection_experience_graph_identity_id=projection_experience_graph_identity_id
    ):
        raise RuntimeError(
            "ProjectionExperienceSectionGraphBinding.build_via_projection_experience requires known "
            + "ProjectionExperienceGraphIdentity: "
            + f"projection_experience_graph_identity_id={projection_experience_graph_identity_id}"
        )

    session = current_handler_session()
    projection_experience_section_graph_binding_id = stable_projection_experience_section_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=layout_config_section_config_id,
        projection_experience_view_id=projection_experience_view_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        binding_key=normalized_binding_key,
    )

    existing = session.imap_get(
        ProjectionExperienceSectionGraphBinding,
        projection_experience_section_graph_binding_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.layout_config_section_config_id != layout_config_section_config_id
            or existing.projection_experience_view_id != projection_experience_view_id
            or existing.projection_experience_graph_identity_id != projection_experience_graph_identity_id
            or (existing.binding_key or "").strip() != normalized_binding_key
            or (existing.section_key or "").strip() != normalized_section_key
        ):
            raise RuntimeError(
                "ProjectionExperienceSectionGraphBinding.build_via_projection_experience payload mismatch "
                + "for existing section graph binding: "
                + f"projection_experience_section_graph_binding_id={projection_experience_section_graph_binding_id}"
            )
        return existing

    return ProjectionExperienceSectionGraphBinding(
        id=projection_experience_section_graph_binding_id,
        projection_experience_id=projection_experience_id,
        layout_config_section_config_id=layout_config_section_config_id,
        projection_experience_view_id=projection_experience_view_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        binding_key=normalized_binding_key,
        section_key=normalized_section_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
