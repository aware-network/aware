from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_section import ProjectionExperienceSection
from aware_experience_ontology.projection.projection_experience_section_view import ProjectionExperienceSectionView

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_projection_experience_section_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def bind_view(
    projection_experience_section: ProjectionExperienceSection,
    projection_experience_view_instance_id: UUID,
    status: str = "active",
) -> ProjectionExperienceSectionView:
    """
    Bind one concrete view instance to this section.

    Contract:
    - Identity is section + view instance.
    - The linked view instance carries view/config/branch/action provenance.
    - Observable matching is derived from the linked view's ApiView contract.
    - FocusScope remains mutable Attention selection state and is not part of
      this bridge's identity.
    """

    # --- AWARE: LOGIC START bind_view
    section_view = await ProjectionExperienceSectionView.build_via_projection_experience_section(
        projection_experience_section_id=projection_experience_section.id,
        projection_experience_view_instance_id=projection_experience_view_instance_id,
        status=status,
    )

    for existing in projection_experience_section.section_views:
        if existing.id == section_view.id:
            if (
                existing.projection_experience_section_id != section_view.projection_experience_section_id
                or existing.projection_experience_view_instance_id
                != section_view.projection_experience_view_instance_id
                or existing.status != section_view.status
            ):
                raise RuntimeError(
                    "ProjectionExperienceSection already has a mismatched section view: "
                    + f"projection_experience_section_view_id={section_view.id}"
                )
            return existing

    projection_experience_section.section_views.append(section_view)
    return section_view
    # --- AWARE: LOGIC END bind_view


async def build_via_projection_experience(
    projection_experience_id: UUID, section_id: UUID, section_key: str | None = None
) -> ProjectionExperienceSection:
    """
    Create one ProjectionExperience-scoped Attention Section bridge.

    Contract:
    - The relationship to Attention Section is the only Attention-owned coordinate here.
    - Section-key text is denormalized for lookup/debugging only.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    normalized_section_key = (section_key or "").strip() or None
    projection_experience_section_id = stable_projection_experience_section_id(
        projection_experience_id=projection_experience_id,
        section_id=section_id,
    )

    session = current_handler_session()
    existing = session.imap_get(
        ProjectionExperienceSection,
        projection_experience_section_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.section_id != section_id
            or existing.section_key != normalized_section_key
        ):
            raise RuntimeError(
                "ProjectionExperienceSection payload mismatch for existing section: "
                + f"projection_experience_section_id={projection_experience_section_id}"
            )
        return existing

    return ProjectionExperienceSection(
        id=projection_experience_section_id,
        projection_experience_id=projection_experience_id,
        section_id=section_id,
        section_key=normalized_section_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
