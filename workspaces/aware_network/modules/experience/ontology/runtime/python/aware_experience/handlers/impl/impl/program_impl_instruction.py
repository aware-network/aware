from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind
from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience_ontology.program.impl.program_impl_instruction_bind import (
    ProgramImplInstructionBind,
)
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
)
from aware_experience_ontology.program.impl.program_impl_instruction_expect import (
    ProgramImplInstructionExpect,
)
from aware_experience_ontology.program.impl.program_impl_instruction_input import (
    ProgramImplInstructionInput,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.program.impl.program_impl_instruction_invoke import (
    ProgramImplInstructionInvoke,
)
from aware_experience_ontology.program.impl.program_impl_instruction_let import (
    ProgramImplInstructionLet,
)
from aware_experience.program.program_impl_instruction_mechanism import (
    create_typed_instruction as _create_typed_instruction,
)

# --- AWARE: USER_IMPORTS END


async def create_bind_via_program_impl(
    program_impl_id: UUID, sequence: int, program_config_port_id: UUID, view_key: str, is_active: bool = True
) -> ProgramImplInstruction:
    """
    Create one `bind` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_bind_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionBind.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            program_config_port_id=program_config_port_id,
            view_key=view_key,
            is_active=is_active,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.bind,
        slot_name="instruction_bind",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_bind_via_program_impl


async def create_expect_via_program_impl(
    program_impl_id: UUID, sequence: int, event_config_id: UUID, required: bool = True
) -> ProgramImplInstruction:
    """
    Create one `expect` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_expect_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionExpect.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            event_config_id=event_config_id,
            required=required,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.expect,
        slot_name="instruction_expect",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_expect_via_program_impl


async def create_input_via_program_impl(
    program_impl_id: UUID, sequence: int, program_config_input_config_id: UUID
) -> ProgramImplInstruction:
    """
    Create one `input` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_input_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionInput.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            program_config_input_config_id=program_config_input_config_id,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.input,
        slot_name="instruction_input",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_input_via_program_impl


async def create_intent_via_program_impl(
    program_impl_id: UUID, sequence: int, action_config_id: UUID, event_config_id: UUID
) -> ProgramImplInstruction:
    """
    Create one `intent` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_intent_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionIntent.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            action_config_id=action_config_id,
            event_config_id=event_config_id,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.intent,
        slot_name="instruction_intent",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_intent_via_program_impl


async def create_invoke_via_program_impl(
    program_impl_id: UUID,
    sequence: int,
    function_config_id: UUID,
    program_config_actor_config_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
) -> ProgramImplInstruction:
    """
    Create one `invoke` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_invoke_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionInvoke.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            function_config_id=function_config_id,
            program_config_actor_config_id=program_config_actor_config_id,
            program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
            target_kind=target_kind,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.invoke,
        slot_name="instruction_invoke",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_invoke_via_program_impl


async def create_let_via_program_impl(
    program_impl_id: UUID, sequence: int, name: str, value_expr: JsonObject
) -> ProgramImplInstruction:
    """
    Create one `let` ProgramImplInstruction with its typed payload.
    """

    # --- AWARE: LOGIC START create_let_via_program_impl
    async def _payload_builder(instruction_id: UUID):
        return await ProgramImplInstructionLet.build_via_program_impl_instruction(
            program_impl_instruction_id=instruction_id,
            name=name,
            value_expr=value_expr,
        )

    return await _create_typed_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=ProgramImplInstructionType.let,
        slot_name="instruction_let",
        payload_builder=_payload_builder,
    )
    # --- AWARE: LOGIC END create_let_via_program_impl
