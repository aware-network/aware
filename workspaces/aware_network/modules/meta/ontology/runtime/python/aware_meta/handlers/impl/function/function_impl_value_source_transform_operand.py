from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_value_source_transform_operand import (
    FunctionImplValueSourceTransformOperand,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_function_impl_value_source_transform(
    function_impl_value_source_transform_id: UUID, position: int, value_source_id: UUID
) -> FunctionImplValueSourceTransformOperand:
    """
    Create deterministic operand binding under one transform payload.
    """

    # --- AWARE: LOGIC START build_via_function_impl_value_source_transform
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_function_impl_value_source_transform
