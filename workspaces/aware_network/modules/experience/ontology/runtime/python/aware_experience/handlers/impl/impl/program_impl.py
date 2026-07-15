from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_enums import ProgramImplInvokeTargetKind
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
from aware_experience_ontology.program.impl.program_impl_instruction import ProgramImplInstruction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_id
from aware_experience.program.program_impl_mechanism import (
    attach_created_instruction as _attach_created_instruction,
    require_program_impl_id as _require_program_impl_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(program_config_id: UUID, key: str) -> ProgramImpl:
    """
    Create a deterministic ProgramImpl.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramImpl.build requires non-empty key")

    program_impl_id = stable_program_impl_id(
        program_config_id=program_config_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImpl, program_impl_id)
    if existing is not None:
        if existing.program_config_id != program_config_id:
            raise RuntimeError(
                "ProgramImpl.build config mismatch for existing program impl: " f"program_impl_id={program_impl_id}"
            )
        if (existing.key or "").strip() != normalized_key:
            raise RuntimeError(
                "ProgramImpl.build key mismatch for existing program impl: " f"program_impl_id={program_impl_id}"
            )
        return existing

    return ProgramImpl(
        id=program_impl_id,
        program_config_id=program_config_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END build


async def create_input_instruction(
    program_impl: ProgramImpl, sequence: int, program_config_input_config_id: UUID
) -> ProgramImplInstruction:
    """
    Create one `input` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_input_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_input_instruction")
    created_instruction = await ProgramImplInstruction.create_input_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        program_config_input_config_id=program_config_input_config_id,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_input_instruction",
    )
    # --- AWARE: LOGIC END create_input_instruction


async def create_let_instruction(
    program_impl: ProgramImpl, sequence: int, name: str, value_expr: JsonObject
) -> ProgramImplInstruction:
    """
    Create one `let` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_let_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_let_instruction")
    created_instruction = await ProgramImplInstruction.create_let_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        name=name,
        value_expr=value_expr,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_let_instruction",
    )
    # --- AWARE: LOGIC END create_let_instruction


async def create_bind_instruction(
    program_impl: ProgramImpl, sequence: int, program_config_port_id: UUID, view_key: str, is_active: bool = True
) -> ProgramImplInstruction:
    """
    Create one `bind` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_bind_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_bind_instruction")
    created_instruction = await ProgramImplInstruction.create_bind_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        program_config_port_id=program_config_port_id,
        view_key=view_key,
        is_active=is_active,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_bind_instruction",
    )
    # --- AWARE: LOGIC END create_bind_instruction


async def create_invoke_instruction(
    program_impl: ProgramImpl,
    sequence: int,
    function_config_id: UUID,
    program_config_actor_config_id: UUID,
    program_config_port_projection_experience_node_id: UUID,
    target_kind: ProgramImplInvokeTargetKind = ProgramImplInvokeTargetKind.instance,
) -> ProgramImplInstruction:
    """
    Create one `invoke` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_invoke_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_invoke_instruction")
    created_instruction = await ProgramImplInstruction.create_invoke_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        function_config_id=function_config_id,
        program_config_actor_config_id=program_config_actor_config_id,
        program_config_port_projection_experience_node_id=program_config_port_projection_experience_node_id,
        target_kind=target_kind,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_invoke_instruction",
    )
    # --- AWARE: LOGIC END create_invoke_instruction


async def create_expect_instruction(
    program_impl: ProgramImpl, sequence: int, event_config_id: UUID, required: bool = True
) -> ProgramImplInstruction:
    """
    Create one `expect` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_expect_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_expect_instruction")
    created_instruction = await ProgramImplInstruction.create_expect_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        event_config_id=event_config_id,
        required=required,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_expect_instruction",
    )
    # --- AWARE: LOGIC END create_expect_instruction


async def create_intent_instruction(
    program_impl: ProgramImpl, sequence: int, action_config_id: UUID, event_config_id: UUID
) -> ProgramImplInstruction:
    """
    Create one `intent` instruction under this ProgramImpl.
    """

    # --- AWARE: LOGIC START create_intent_instruction
    program_impl_id = _require_program_impl_id(program_impl, fn_name="create_intent_instruction")
    created_instruction = await ProgramImplInstruction.create_intent_via_program_impl(
        program_impl_id=program_impl_id,
        sequence=sequence,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
    )
    return _attach_created_instruction(
        program_impl=program_impl,
        created_instruction=created_instruction,
        fn_name="create_intent_instruction",
    )
    # --- AWARE: LOGIC END create_intent_instruction
