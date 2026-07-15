from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramSlotOnBind
from aware_experience_ontology.program.program_config_layout import ProgramConfigLayout
from aware_experience_ontology.program.program_config_layout_port_section import ProgramConfigLayoutPortSection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention.stable_ids import stable_layout_id
from aware_attention_ontology.layout.layout import Layout
from aware_experience.stable_ids import stable_program_config_layout_id
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_port_section(
    program_config_layout: ProgramConfigLayout,
    program_config_port_id: UUID,
    layout_section_id: UUID,
    on_bind: ProgramSlotOnBind = ProgramSlotOnBind.replace,
    is_visible_default: bool | None = None,
) -> ProgramConfigLayoutPortSection:
    """
    Attach one deterministic ProgramConfigLayoutPortSection under this ProgramConfigLayout.
    """

    # --- AWARE: LOGIC START add_port_section
    layout_id = program_config_layout.id
    if layout_id is None:
        raise RuntimeError("ProgramConfigLayout.add_port_section requires id")

    session = current_handler_session()
    program_config_port = session.imap_get(ProgramConfigPort, program_config_port_id)
    if program_config_port is None:
        raise RuntimeError(
            "ProgramConfigLayout.add_port_section requires ProgramConfigPort to exist. "
            "Create it first via ProgramConfig.create_port(...)."
        )

    created = await ProgramConfigLayoutPortSection.build_via_program_config_layout(
        program_config_layout_id=layout_id,
        program_config_port_id=program_config_port_id,
        layout_section_id=layout_section_id,
        on_bind=on_bind,
        is_visible_default=is_visible_default,
    )

    for existing in program_config_layout.port_sections:
        if existing.id == created.id:
            return existing
    program_config_layout.port_sections.append(created)
    return created
    # --- AWARE: LOGIC END add_port_section


async def build_via_program_config(program_config_id: UUID, key: str, is_default: bool = False) -> ProgramConfigLayout:
    """
    Create a deterministic ProgramConfigLayout under a ProgramConfig.
    """

    # --- AWARE: LOGIC START build_via_program_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramConfigLayout.build_via_program_config requires non-empty key")

    layout_id = stable_layout_id(layout_key=normalized_key)
    layout = await Layout.build(
        key=normalized_key,
        title=normalized_key,
        description=None,
    )
    if layout.id != layout_id:
        raise RuntimeError(
            "ProgramConfigLayout.build_via_program_config layout identity mismatch: "
            f"expected={layout_id} actual={layout.id}"
        )

    session = current_handler_session()

    layout_config_id = stable_program_config_layout_id(
        program_config_id=program_config_id,
        key=normalized_key,
    )
    existing = session.imap_get(ProgramConfigLayout, layout_config_id)
    if existing is not None:
        if (
            existing.program_config_id != program_config_id
            or existing.layout_id != layout_id
            or existing.key != normalized_key
            or existing.is_default != is_default
        ):
            raise RuntimeError(
                "ProgramConfigLayout.build_via_program_config payload mismatch for existing layout: "
                f"program_config_layout_id={layout_config_id}"
            )
        return existing

    return ProgramConfigLayout(
        id=layout_config_id,
        program_config_id=program_config_id,
        layout_id=layout_id,
        key=normalized_key,
        is_default=is_default,
    )
    # --- AWARE: LOGIC END build_via_program_config
