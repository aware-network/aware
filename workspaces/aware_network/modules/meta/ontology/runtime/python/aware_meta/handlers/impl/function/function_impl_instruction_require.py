from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
)
from aware_meta_ontology.function.function_impl_instruction_require import FunctionImplInstructionRequire
from aware_meta_ontology.function.function_impl_instruction_require_operand import FunctionImplInstructionRequireOperand

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_require_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_operand(
    function_impl_instruction_require: FunctionImplInstructionRequire, position: int, value_source_id: UUID
) -> FunctionImplInstructionRequireOperand:
    """
    Attach one deterministic operand source under this `require` payload.
    """

    # --- AWARE: LOGIC START add_operand
    function_impl_instruction_require_id = function_impl_instruction_require.id
    if function_impl_instruction_require_id is None:
        raise RuntimeError("FunctionImplInstructionRequire.add_operand requires FunctionImplInstructionRequire.id")

    created = await FunctionImplInstructionRequireOperand.create_via_function_impl_instruction_require(
        function_impl_instruction_require_id=function_impl_instruction_require_id,
        position=position,
        value_source_id=value_source_id,
    )
    if all(existing.id != created.id for existing in function_impl_instruction_require.operands):
        function_impl_instruction_require.operands.append(created)
    return created
    # --- AWARE: LOGIC END add_operand


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID,
    kind: FunctionImplRequireKind,
    compare_operator: FunctionImplRequireCompareOperator | None = None,
    expected_count: int | None = None,
    message: str | None = None,
) -> FunctionImplInstructionRequire:
    """
    Create deterministic `require` payload for one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    if expected_count is not None and expected_count < 0:
        raise RuntimeError("FunctionImplInstructionRequire.build_via_function requires expected_count >= 0")

    if kind in {FunctionImplRequireKind.compare, FunctionImplRequireKind.cardinality} and compare_operator is None:
        raise RuntimeError(
            "FunctionImplInstructionRequire.build_via_function requires compare_operator for kind " f"{kind.value!r}"
        )
    if kind == FunctionImplRequireKind.cardinality and expected_count is None:
        raise RuntimeError(
            "FunctionImplInstructionRequire.build_via_function requires expected_count for kind 'cardinality'"
        )

    session = current_handler_session()
    parent_instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionRequire.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "require":
        raise RuntimeError(
            "FunctionImplInstructionRequire.build_via_function requires parent instruction type 'require': "
            f"function_impl_instruction_id={function_impl_instruction_id} type={parent_instruction.type.value}"
        )

    function_impl_instruction_require_id = stable_function_impl_instruction_require_id(
        function_impl_instruction_id=function_impl_instruction_id
    )
    existing = session.imap_get(FunctionImplInstructionRequire, function_impl_instruction_require_id)
    if existing is not None:
        if (
            existing.kind != kind
            or existing.compare_operator != compare_operator
            or existing.expected_count != expected_count
            or (existing.message or None) != (message or None)
        ):
            raise RuntimeError(
                "FunctionImplInstructionRequire.build_via_function payload mismatch for existing require payload: "
                f"function_impl_instruction_require_id={function_impl_instruction_require_id}"
            )
        return existing

    return FunctionImplInstructionRequire(
        id=function_impl_instruction_require_id,
        kind=kind,
        compare_operator=compare_operator,
        expected_count=expected_count,
        message=message,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
