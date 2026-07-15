from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramBranchBindingMode
from aware_experience_ontology.program.program_config_port import ProgramConfigPort
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import stable_program_config_port_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_projection_node(
    program_config_port: ProgramConfigPort, projection_experience_node_id: UUID, key: str
) -> ProgramConfigPortProjectionExperienceNode:
    """
    Attach one ProjectionExperienceNode contract under this ProgramConfigPort.
    """

    # --- AWARE: LOGIC START create_projection_node
    port_id = program_config_port.id
    if port_id is None:
        raise RuntimeError("ProgramConfigPort.create_projection_node requires id")
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramConfigPort.create_projection_node requires non-empty key")

    created = await ProgramConfigPortProjectionExperienceNode.build_via_program_config_port(
        program_config_port_id=port_id,
        projection_experience_node_id=projection_experience_node_id,
        key=normalized_key,
    )
    for existing in program_config_port.projection_nodes:
        if existing.id == created.id:
            return existing
    program_config_port.projection_nodes.append(created)
    return created
    # --- AWARE: LOGIC END create_projection_node


async def build_via_program_config(
    program_config_id: UUID,
    projection_id: UUID,
    key: str | None = None,
    intent: str | None = None,
    branch_binding_mode: ProgramBranchBindingMode = ProgramBranchBindingMode.reference,
) -> ProgramConfigPort:
    """
    Create a deterministic ProgramConfigPort under a ProgramConfig.
    """

    # --- AWARE: LOGIC START build_via_program_config
    normalized_key = (key or "").strip() or "default"
    normalized_intent = (intent or "").strip() or None

    session = current_handler_session()
    port_id = stable_program_config_port_id(
        program_config_id=program_config_id,
        key=normalized_key,
    )

    existing = session.imap_get(ProgramConfigPort, port_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or "default"
        existing_intent = (existing.intent or "").strip() or None
        if (
            existing.program_config_id != program_config_id
            or existing_key != normalized_key
            or existing.projection_id != projection_id
            or existing.branch_binding_mode != branch_binding_mode
        ):
            raise RuntimeError(
                "ProgramConfigPort.build_via_program_config payload mismatch for existing port: "
                f"program_config_port_id={port_id}"
            )
        if normalized_intent is not None:
            if existing_intent is None:
                existing.intent = normalized_intent
            elif existing_intent != normalized_intent:
                raise RuntimeError(
                    "ProgramConfigPort.build_via_program_config intent mismatch for existing port: "
                    f"program_config_port_id={port_id} "
                    f"existing={existing_intent!r} new={normalized_intent!r}"
                )
        return existing

    return ProgramConfigPort(
        id=port_id,
        program_config_id=program_config_id,
        projection_id=projection_id,
        key=normalized_key,
        intent=normalized_intent,
        branch_binding_mode=branch_binding_mode,
    )
    # --- AWARE: LOGIC END build_via_program_config
