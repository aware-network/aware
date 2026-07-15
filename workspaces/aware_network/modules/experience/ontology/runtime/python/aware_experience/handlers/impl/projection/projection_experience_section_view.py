from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_section_view import ProjectionExperienceSectionView

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_projection_experience_section_view_id
from aware_experience_ontology.projection.projection_experience_view_instance import (
    ProjectionExperienceViewInstance,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_section(
    projection_experience_section_id: UUID, projection_experience_view_instance_id: UUID, status: str = "active"
) -> ProjectionExperienceSectionView:
    """
    Create one section+view-instance resolver.

    Contract:
    - Identity is scoped by parent ProjectionExperienceSection plus view instance.
    - `projection_experience_view_instance` must be the concrete view fulfillment
      for the ApiView whose observable may be selected by Attention.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_section
    normalized_status = (status or "").strip() or "active"
    session = current_handler_session()

    view_instance = session.imap_get(
        ProjectionExperienceViewInstance,
        projection_experience_view_instance_id,
    )
    if view_instance is None:
        raise RuntimeError(
            "ProjectionExperienceSectionView requires an existing linked view instance: "
            + f"projection_experience_view_instance_id={projection_experience_view_instance_id}"
        )

    section_view_id = stable_projection_experience_section_view_id(
        projection_experience_section_id=projection_experience_section_id,
        projection_experience_view_instance_id=projection_experience_view_instance_id,
    )
    existing = session.imap_get(ProjectionExperienceSectionView, section_view_id)
    if existing is not None:
        if (
            existing.projection_experience_section_id != projection_experience_section_id
            or existing.projection_experience_view_instance_id != projection_experience_view_instance_id
            or existing.status != normalized_status
        ):
            raise RuntimeError(
                "ProjectionExperienceSectionView payload mismatch for existing resolver: "
                + f"projection_experience_section_view_id={section_view_id}"
            )
        return existing

    return ProjectionExperienceSectionView(
        id=section_view_id,
        projection_experience_section_id=projection_experience_section_id,
        projection_experience_view_instance_id=projection_experience_view_instance_id,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_section
