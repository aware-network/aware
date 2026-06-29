from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_primitive_type(code_primitive_type_id: UUID, position: int) -> CodePrimitiveTypeUnionType:
    """
    Create one ordered union member slot under a CodePrimitiveType.
    """

    # --- AWARE: LOGIC START build_via_code_primitive_type
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_primitive_type
