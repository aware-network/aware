from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_config_input_config_attribute_config import (
    ProgramConfigInputConfigAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Experience Runtime
from aware_experience.stable_ids import (
    stable_program_config_input_config_attribute_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_config_input_config(
    program_config_input_config_id: UUID, attribute_config_id: UUID, position: int | None = None
) -> ProgramConfigInputConfigAttributeConfig:
    """
    Create deterministic input signature association edge for one
    ProgramConfigInputConfigAttributeConfig.
    """

    # --- AWARE: LOGIC START build_via_program_config_input_config
    if position is not None and position < 0:
        raise RuntimeError(
            "ProgramConfigInputConfigAttributeConfig.build_via_program_config_input_config requires position >= 0"
        )

    assoc_id = stable_program_config_input_config_attribute_config_id(
        program_config_input_config_id=program_config_input_config_id,
        attribute_config_id=attribute_config_id,
    )

    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "ProgramConfigInputConfigAttributeConfig.build requires AttributeConfig to exist. "
            "Create it first via AttributeConfig.create(...)."
        )

    existing = session.imap_get(ProgramConfigInputConfigAttributeConfig, assoc_id)
    if existing is not None:
        if (
            existing.program_config_input_config_id != program_config_input_config_id
            or existing.attribute_config_id != attribute_config_id
            or existing.position != position
        ):
            raise RuntimeError(
                "ProgramConfigInputConfigAttributeConfig.build_via_program_config_input_config payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        return existing

    return ProgramConfigInputConfigAttributeConfig(
        id=assoc_id,
        program_config_input_config_id=program_config_input_config_id,
        attribute_config_id=attribute_config_id,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_program_config_input_config
