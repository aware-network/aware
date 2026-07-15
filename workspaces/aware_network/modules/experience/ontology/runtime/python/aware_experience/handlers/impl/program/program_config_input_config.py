from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.program_config_input_config import ProgramConfigInputConfig
from aware_experience_ontology.program.program_config_input_config_attribute_config import (
    ProgramConfigInputConfigAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Experience Runtime
from aware_experience.stable_ids import stable_program_config_input_config_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_attribute_config(
    program_config_input_config: ProgramConfigInputConfig, attribute_config_id: UUID, position: int | None = None
) -> ProgramConfigInputConfigAttributeConfig:
    """
    Attach one typed input signature attribute under this ProgramConfigInputConfig.
    """

    # --- AWARE: LOGIC START add_attribute_config
    if position is not None and position < 0:
        raise RuntimeError("ProgramConfigInputConfig.add_attribute_config requires position >= 0")

    input_config_id = program_config_input_config.id
    if input_config_id is None:
        raise RuntimeError("ProgramConfigInputConfig.add_attribute_config requires id")

    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "ProgramConfigInputConfig.add_attribute_config requires AttributeConfig to exist. "
            "Create it first via AttributeConfig.create(...)."
        )

    created = await ProgramConfigInputConfigAttributeConfig.build_via_program_config_input_config(
        program_config_input_config_id=input_config_id,
        attribute_config_id=attribute_config_id,
        position=position,
    )

    for existing in program_config_input_config.attribute_configs:
        if existing.id == created.id:
            return existing
    program_config_input_config.attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_attribute_config


async def build_via_program_config(
    program_config_id: UUID, name: str, source: str, required: bool = True, default_expr: JsonObject | None = None
) -> ProgramConfigInputConfig:
    """
    Create deterministic ProgramConfigInputConfig under one ProgramConfig.
    """

    # --- AWARE: LOGIC START build_via_program_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProgramConfigInputConfig.build_via_program_config requires non-empty name")
    normalized_source = (source or "").strip()
    if not normalized_source:
        raise RuntimeError("ProgramConfigInputConfig.build_via_program_config requires non-empty source")

    input_config_id = stable_program_config_input_config_id(
        program_config_id=program_config_id,
        name=normalized_name,
        source=normalized_source,
    )

    session = current_handler_session()
    existing = session.imap_get(ProgramConfigInputConfig, input_config_id)
    if existing is not None:
        if (
            existing.program_config_id != program_config_id
            or existing.name != normalized_name
            or existing.source != normalized_source
            or existing.required != required
            or existing.default_expr != default_expr
        ):
            raise RuntimeError(
                "ProgramConfigInputConfig.build_via_program_config payload mismatch for existing input config: "
                f"program_config_input_config_id={input_config_id}"
            )
        return existing

    return ProgramConfigInputConfig(
        id=input_config_id,
        program_config_id=program_config_id,
        name=normalized_name,
        source=normalized_source,
        required=required,
        default_expr=default_expr,
    )
    # --- AWARE: LOGIC END build_via_program_config
