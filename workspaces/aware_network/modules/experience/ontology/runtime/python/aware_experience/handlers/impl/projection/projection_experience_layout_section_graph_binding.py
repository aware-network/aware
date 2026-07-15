from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
    ProjectionExperienceLayoutSectionGraphBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.layout.layout_config_section_config import (
    LayoutConfigSectionConfig,
)
from aware_experience.stable_ids import (
    stable_projection_experience_layout_section_graph_binding_id,
)
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_layout_graph_binding(
    projection_experience_layout_graph_binding_id: UUID, section_graph_binding_id: UUID
) -> ProjectionExperienceLayoutSectionGraphBinding:
    """
    Create deterministic ProjectionExperienceLayoutSectionGraphBinding.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_layout_graph_binding
    session = current_handler_session()
    layout_binding = session.imap_get(
        ProjectionExperienceLayoutGraphBinding,
        projection_experience_layout_graph_binding_id,
    )
    if layout_binding is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
            + "requires known ProjectionExperienceLayoutGraphBinding: "
            + f"projection_experience_layout_graph_binding_id={projection_experience_layout_graph_binding_id}"
        )

    section_graph_binding = session.imap_get(
        ProjectionExperienceSectionGraphBinding,
        section_graph_binding_id,
    )
    if section_graph_binding is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
            + "requires known ProjectionExperienceSectionGraphBinding: "
            + f"section_graph_binding_id={section_graph_binding_id}"
        )
    if section_graph_binding.projection_experience_id != layout_binding.projection_experience_id:
        raise RuntimeError(
            "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
            + "projection mismatch: "
            + f"layout_binding_id={projection_experience_layout_graph_binding_id} "
            + f"section_graph_binding_id={section_graph_binding_id}"
        )

    layout_config_section_config = session.imap_get(
        LayoutConfigSectionConfig,
        section_graph_binding.layout_config_section_config_id,
    )
    if layout_config_section_config is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
            + "requires loaded Attention LayoutConfigSectionConfig: "
            + f"layout_config_section_config_id={section_graph_binding.layout_config_section_config_id}"
        )
    if layout_config_section_config.layout_config_id != layout_binding.layout_config_id:
        raise RuntimeError(
            "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
            + "layout mismatch: "
            + f"layout_config_id={layout_binding.layout_config_id} "
            + "does not own "
            + f"layout_config_section_config_id={layout_config_section_config.id}"
        )

    row_id = stable_projection_experience_layout_section_graph_binding_id(
        projection_experience_layout_graph_binding_id=projection_experience_layout_graph_binding_id,
        section_graph_binding_id=section_graph_binding_id,
    )
    existing = session.imap_get(
        ProjectionExperienceLayoutSectionGraphBinding,
        row_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_layout_graph_binding_id != projection_experience_layout_graph_binding_id
            or existing.section_graph_binding_id != section_graph_binding_id
        ):
            raise RuntimeError(
                "ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding "
                + f"payload mismatch for existing row: row_id={row_id}"
            )
        return existing

    return ProjectionExperienceLayoutSectionGraphBinding(
        id=row_id,
        projection_experience_layout_graph_binding_id=projection_experience_layout_graph_binding_id,
        section_graph_binding_id=section_graph_binding_id,
        section_graph_binding=section_graph_binding,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_layout_graph_binding
