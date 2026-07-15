from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_require_operand import FunctionImplInstructionRequireOperand

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_require import FunctionImplInstructionRequire
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_require_operand_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_function_impl_instruction_require(
    function_impl_instruction_require_id: UUID, position: int, value_source_id: UUID
) -> FunctionImplInstructionRequireOperand:
    """
    Create deterministic operand binding under one `require` payload.
    """

    # --- AWARE: LOGIC START create_via_function_impl_instruction_require
    if position < 0:
        raise RuntimeError("FunctionImplInstructionRequireOperand.create_via_function requires position >= 0")

    session = current_handler_session()
    require_payload = session.imap_get(FunctionImplInstructionRequire, function_impl_instruction_require_id)
    if require_payload is None:
        raise RuntimeError(
            "FunctionImplInstructionRequireOperand.create_via_function requires existing require payload: "
            f"function_impl_instruction_require_id={function_impl_instruction_require_id}"
        )

    value_source = session.imap_get(FunctionImplValueSource, value_source_id)
    if value_source is None:
        raise RuntimeError(
            "FunctionImplInstructionRequireOperand.create_via_function requires existing FunctionImplValueSource: "
            f"value_source_id={value_source_id}"
        )

    function_impl_instruction_require_operand_id = stable_function_impl_instruction_require_operand_id(
        function_impl_instruction_require_id=function_impl_instruction_require_id,
        position=position,
    )
    existing = session.imap_get(
        FunctionImplInstructionRequireOperand,
        function_impl_instruction_require_operand_id,
    )
    if existing is not None:
        if (
            existing.function_impl_instruction_require_id != function_impl_instruction_require_id
            or existing.position != position
            or existing.value_source_id != value_source_id
        ):
            raise RuntimeError(
                "FunctionImplInstructionRequireOperand.create_via_function payload mismatch for existing operand: "
                f"function_impl_instruction_require_operand_id={function_impl_instruction_require_operand_id}"
            )
        return existing

    return FunctionImplInstructionRequireOperand(
        id=function_impl_instruction_require_operand_id,
        function_impl_instruction_require_id=function_impl_instruction_require_id,
        value_source=value_source,
        value_source_id=value_source.id,
        position=position,
    )
    # --- AWARE: LOGIC END create_via_function_impl_instruction_require
