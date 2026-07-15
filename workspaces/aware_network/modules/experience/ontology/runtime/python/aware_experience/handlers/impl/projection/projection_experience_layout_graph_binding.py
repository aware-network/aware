from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_layout_graph_binding import (
    ProjectionExperienceLayoutGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_layout_section_graph_binding import (
    ProjectionExperienceLayoutSectionGraphBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.layout.layout_config_section_config import (
    LayoutConfigSectionConfig,
)
from aware_experience.stable_ids import (
    stable_projection_experience_layout_graph_binding_id,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_section_graph_binding(
    projection_experience_layout_graph_binding: ProjectionExperienceLayoutGraphBinding, section_graph_binding_id: UUID
) -> ProjectionExperienceLayoutSectionGraphBinding:
    """
    Attach one existing section graph binding to this layout composition.

    Contract:
    - The section binding remains the source of view + section + graph anchor truth.
    - This row only groups section bindings under one layout-level Experience target.
    - Ordering is resolved from the Attention LayoutConfigSectionConfig relation.
    """

    # --- AWARE: LOGIC START add_section_graph_binding
    session = current_handler_session()
    section_graph_binding = session.imap_get(
        ProjectionExperienceSectionGraphBinding,
        section_graph_binding_id,
    )
    if section_graph_binding is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.add_section_graph_binding requires known "
            + "ProjectionExperienceSectionGraphBinding: "
            + f"section_graph_binding_id={section_graph_binding_id}"
        )
    if (
        section_graph_binding.projection_experience_id
        != projection_experience_layout_graph_binding.projection_experience_id
    ):
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.add_section_graph_binding projection mismatch: "
            + f"layout_binding_id={projection_experience_layout_graph_binding.id} "
            + f"section_graph_binding_id={section_graph_binding_id}"
        )

    layout_config_section_config = session.imap_get(
        LayoutConfigSectionConfig,
        section_graph_binding.layout_config_section_config_id,
    )
    if layout_config_section_config is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.add_section_graph_binding requires loaded "
            + "Attention LayoutConfigSectionConfig: "
            + f"layout_config_section_config_id={section_graph_binding.layout_config_section_config_id}"
        )
    if layout_config_section_config.layout_config_id != projection_experience_layout_graph_binding.layout_config_id:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.add_section_graph_binding layout mismatch: "
            + f"layout_config_id={projection_experience_layout_graph_binding.layout_config_id} "
            + "does not own "
            + f"layout_config_section_config_id={layout_config_section_config.id}"
        )

    created = await ProjectionExperienceLayoutSectionGraphBinding.build_via_projection_experience_layout_graph_binding(
        projection_experience_layout_graph_binding_id=projection_experience_layout_graph_binding.id,
        section_graph_binding_id=section_graph_binding_id,
    )
    for existing in projection_experience_layout_graph_binding.layout_section_graph_bindings:
        if existing.id == created.id:
            return existing
    projection_experience_layout_graph_binding.layout_section_graph_bindings.append(created)
    return created
    # --- AWARE: LOGIC END add_section_graph_binding


async def build_via_projection_experience(
    projection_experience_id: UUID, layout_config_id: UUID, binding_key: str
) -> ProjectionExperienceLayoutGraphBinding:
    """
    Create deterministic ProjectionExperienceLayoutGraphBinding under one ProjectionExperience.

    Contract:
    - `binding_key` is the stable service-facing layout composition handle.
    - `layout_config` is the canonical portal to Attention-owned layout truth.
    - Child section rows must target sections that belong to this layout.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    normalized_binding_key = (binding_key or "").strip()
    if not normalized_binding_key:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.build_via_projection_experience requires non-empty binding_key"
        )

    session = current_handler_session()
    projection_experience = session.imap_get(ProjectionExperience, projection_experience_id)
    if projection_experience is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.build_via_projection_experience requires known "
            + f"ProjectionExperience: projection_experience_id={projection_experience_id}"
        )

    layout_config = session.imap_get(LayoutConfig, layout_config_id)
    if layout_config is None:
        raise RuntimeError(
            "ProjectionExperienceLayoutGraphBinding.build_via_projection_experience requires loaded "
            + f"Attention LayoutConfig: layout_config_id={layout_config_id}"
        )

    layout_binding_id = stable_projection_experience_layout_graph_binding_id(
        projection_experience_id=projection_experience_id,
        layout_config_id=layout_config_id,
        binding_key=normalized_binding_key,
    )
    existing = session.imap_get(
        ProjectionExperienceLayoutGraphBinding,
        layout_binding_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.layout_config_id != layout_config_id
            or (existing.binding_key or "").strip() != normalized_binding_key
        ):
            raise RuntimeError(
                "ProjectionExperienceLayoutGraphBinding.build_via_projection_experience payload mismatch "
                + f"for existing layout binding: layout_binding_id={layout_binding_id}"
            )
        return existing

    return ProjectionExperienceLayoutGraphBinding(
        id=layout_binding_id,
        projection_experience_id=projection_experience_id,
        layout_config_id=layout_config_id,
        layout_config=layout_config,
        binding_key=normalized_binding_key,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
