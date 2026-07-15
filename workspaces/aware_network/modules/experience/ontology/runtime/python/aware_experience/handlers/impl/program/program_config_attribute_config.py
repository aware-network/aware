from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramAttributeType
from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience.stable_ids import (
    stable_program_config_attribute_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_program_config(
    program_config_id: UUID,
    attribute_config_id: UUID,
    type: ProgramAttributeType = ProgramAttributeType.input,
    position: int | None = None,
    required: bool = True,
) -> ProgramConfigAttributeConfig:
    """
    Create deterministic ProgramConfigAttributeConfig association edge.
    """

    # --- AWARE: LOGIC START create_via_program_config
    if position is not None and position < 0:
        raise RuntimeError("ProgramConfigAttributeConfig.create_via_program_config requires position >= 0")

    assoc_id = stable_program_config_attribute_config_id(
        program_config_id=program_config_id,
        attribute_config_id=attribute_config_id,
        type=type.value,
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramConfigAttributeConfig, assoc_id)
    if existing is not None:
        if (
            existing.program_config_id != program_config_id
            or existing.attribute_config_id != attribute_config_id
            or existing.type != type
            or existing.position != position
            or existing.required != required
        ):
            raise RuntimeError(
                "ProgramConfigAttributeConfig.create_via_program_config payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramConfigAttributeConfig(
        id=assoc_id,
        program_config_id=program_config_id,
        attribute_config_id=attribute_config_id,
        type=type,
        position=position,
        required=required,
    )
    # --- AWARE: LOGIC END create_via_program_config
