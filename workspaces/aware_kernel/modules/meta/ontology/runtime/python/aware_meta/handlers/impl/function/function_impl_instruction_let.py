from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_let_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID, name: str, value_expr: JsonObject
) -> FunctionImplInstructionLet:
    """
    Create deterministic `let` payload for one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    session = current_handler_session()
    parent_instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionLet.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "let":
        raise RuntimeError(
            "FunctionImplInstructionLet.build_via_function requires parent instruction type 'let': "
            f"function_impl_instruction_id={function_impl_instruction_id} type={parent_instruction.type.value}"
        )

    function_impl_instruction_let_id = stable_function_impl_instruction_let_id(
        function_impl_instruction_id=function_impl_instruction_id
    )
    existing = session.imap_get(FunctionImplInstructionLet, function_impl_instruction_let_id)
    if existing is not None:
        if existing.name != name or existing.value_expr != value_expr:
            raise RuntimeError(
                "FunctionImplInstructionLet.build_via_function payload mismatch for existing let payload: "
                f"function_impl_instruction_let_id={function_impl_instruction_let_id}"
            )
        return existing

    return FunctionImplInstructionLet(
        id=function_impl_instruction_let_id,
        name=name,
        value_expr=value_expr,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
