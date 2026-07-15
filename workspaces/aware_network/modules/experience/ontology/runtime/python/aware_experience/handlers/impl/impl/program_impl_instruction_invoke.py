from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import ProgramImplInstructionInvoke
from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
    ProgramImplInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Experience Ontology
from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig
from aware_experience_ontology.program.program_config_port_projection_experience_node import (
    ProgramConfigPortProjectionExperienceNode,
)
from aware_experience.stable_ids import stable_program_impl_instruction_invoke_id
from aware_experience.stable_ids import (
    stable_program_impl_instruction_invoke_attribute_config_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_attribute_config(
    program_impl_instruction_invoke: ProgramImplInstructionInvoke,
    attribute_config_id: UUID,
    value_expr: JsonObject,
    position: int | None = None,
) -> ProgramImplInstructionInvokeAttributeConfig:
    """
    Attach one deterministic invoke argument binding by AttributeConfig contract.
    """

    # --- AWARE: LOGIC START add_attribute_config
    if position is not None and position < 0:
        raise RuntimeError("ProgramImplInstructionInvoke.add_attribute_config requires position >= 0")

    instruction_invoke_id = program_impl_instruction_invoke.id
    if instruction_invoke_id is None:
        raise RuntimeError("ProgramImplInstructionInvoke.add_attribute_config requires id")

    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "ProgramImplInstructionInvoke.add_attribute_config requires AttributeConfig to exist. "
            "Create it first via AttributeConfig.create(...)."
        )

    assoc_id = stable_program_impl_instruction_invoke_attribute_config_id(
        program_impl_instruction_invoke_id=instruction_invoke_id,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(ProgramImplInstructionInvokeAttributeConfig, assoc_id)
    if existing is None:
        created = await ProgramImplInstructionInvokeAttributeConfig.build_via_program_impl_instruction_invoke(
            program_impl_instruction_invoke_id=instruction_invoke_id,
            attribute_config_id=attribute_config_id,
            value_expr=value_expr,
            position=position,
        )
    else:
        if (
            existing.program_impl_instruction_invoke_id != instruction_invoke_id
            or existing.attribute_config_id != attribute_config_id
            or existing.value_expr != value_expr
            or existing.position != position
        ):
            raise RuntimeError(
                "ProgramImplInstructionInvoke.add_attribute_config payload mismatch for existing association: "
                f"association_id={assoc_id}"
            )
        created = existing

    for existing_assoc in program_impl_instruction_invoke.attribute_configs:
        if existing_assoc.id == created.id:
            return existing_assoc
    program_impl_instruction_invoke.attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_attribute_config


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID,
    function_config_id: UUID,
    program_config_actor_config_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
) -> ProgramImplInstructionInvoke:
    """
    Create deterministic invoke payload for one ProgramImplInstruction.

    Contract:
    - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction

    instruction_invoke_id = stable_program_impl_instruction_invoke_id(
        program_impl_instruction_id=program_impl_instruction_id,
    )
    session = current_handler_session()
    actor_config = session.imap_get(ProgramConfigActorConfig, program_config_actor_config_id)
    if actor_config is None:
        raise RuntimeError(
            "ProgramImplInstructionInvoke.build requires ProgramConfigActorConfig to exist. "
            "Create it first via ProgramConfig.create_actor_config(...)."
        )
    port_projection_node = session.imap_get(
        ProgramConfigPortProjectionExperienceNode,
        program_config_port_projection_experience_node_id,
    )
    if port_projection_node is None:
        raise RuntimeError(
            "ProgramImplInstructionInvoke.build requires ProgramConfigPortProjectionExperienceNode to exist. "
            "Create it first via ProgramConfigPort.create_projection_node(...)."
        )
    existing = session.imap_get(ProgramImplInstructionInvoke, instruction_invoke_id)
    if existing is not None:
        if (
            existing.function_config_id != function_config_id
            or existing.program_config_actor_config_id != program_config_actor_config_id
            or (
                existing.program_config_port_projection_experience_node_id
                != program_config_port_projection_experience_node_id
            )
            or existing.target_kind != target_kind
        ):
            raise RuntimeError(
                "ProgramImplInstructionInvoke.build payload mismatch for existing instruction invoke: "
                f"instruction_invoke_id={instruction_invoke_id}"
            )
        return existing

    return ProgramImplInstructionInvoke(
        id=instruction_invoke_id,
        function_config_id=function_config_id,
        program_config_actor_config_id=program_config_actor_config_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        target_kind=target_kind,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
