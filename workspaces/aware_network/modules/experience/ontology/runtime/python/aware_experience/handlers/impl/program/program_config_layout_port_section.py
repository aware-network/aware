from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramSlotOnBind
from aware_experience_ontology.program.program_config_layout_port_section import ProgramConfigLayoutPortSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_config_layout_port_section_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_layout(
    program_config_layout_id: UUID,
    program_config_port_id: UUID,
    layout_section_id: UUID,
    on_bind: ProgramSlotOnBind = ProgramSlotOnBind.replace,
    is_visible_default: bool | None = None,
) -> ProgramConfigLayoutPortSection:
    """
    Create a deterministic ProgramConfigLayoutPortSection under a ProgramConfigLayout.
    """

    # --- AWARE: LOGIC START build_via_program_config_layout
    assoc_id = stable_program_config_layout_port_section_id(
        program_config_layout_id=program_config_layout_id,
        program_config_port_id=program_config_port_id,
        layout_section_id=layout_section_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramConfigLayoutPortSection, assoc_id)
    if existing is not None:
        if (
            existing.program_config_layout_id != program_config_layout_id
            or existing.program_config_port_id != program_config_port_id
            or existing.layout_section_id != layout_section_id
            or existing.on_bind != on_bind
            or existing.is_visible_default != is_visible_default
        ):
            raise RuntimeError(
                "ProgramConfigLayoutPortSection.build_via_program_config_layout payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramConfigLayoutPortSection(
        id=assoc_id,
        program_config_layout_id=program_config_layout_id,
        program_config_port_id=program_config_port_id,
        layout_section_id=layout_section_id,
        on_bind=on_bind,
        is_visible_default=is_visible_default,
    )
    # --- AWARE: LOGIC END build_via_program_config_layout
