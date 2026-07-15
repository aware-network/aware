from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplValueTransformKind
from aware_meta_ontology.function.function_impl_value_source_transform import FunctionImplValueSourceTransform
from aware_meta_ontology.function.function_impl_value_source_transform_operand import (
    FunctionImplValueSourceTransformOperand,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def add_operand(
    function_impl_value_source_transform: FunctionImplValueSourceTransform, position: int, value_source_id: UUID
) -> FunctionImplValueSourceTransformOperand:
    """
    Add one deterministic transform operand source.
    """

    # --- AWARE: LOGIC START add_operand
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END add_operand


async def build_via_function_impl_value_source(
    function_impl_value_source_id: UUID,
    operation: FunctionImplValueTransformKind,
    output_primitive_config_id: UUID | None = None,
) -> FunctionImplValueSourceTransform:
    """
    Create deterministic transform payload under one FunctionImplValueSource.

    Contract:
    - Parent context (`function_impl_value_source_id`) is injected by parent-edge lowering.
    - Identity is parent-scoped and unique for the owning value source.
    """

    # --- AWARE: LOGIC START build_via_function_impl_value_source
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_function_impl_value_source
