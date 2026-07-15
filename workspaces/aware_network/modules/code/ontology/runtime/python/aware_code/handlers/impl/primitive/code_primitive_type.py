from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType
from aware_code_ontology.primitive.code_primitive_type_element_type import CodePrimitiveTypeElementType
from aware_code_ontology.primitive.code_primitive_type_union_type import CodePrimitiveTypeUnionType

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_code.stable_ids import stable_code_primitive_type_id

# --- AWARE: USER_IMPORTS END


async def create(
    signature: str, base_type: CodePrimitiveBaseType, constraints: JsonObject | None = None
) -> CodePrimitiveType:
    """
    Create deterministic primitive type root from canonical structural signature.
    """

    # --- AWARE: LOGIC START create
    normalized_signature = signature.strip()
    if not normalized_signature:
        raise RuntimeError("CodePrimitiveType.create requires a non-empty signature")
    code_primitive_type_id = stable_code_primitive_type_id(signature=normalized_signature)
    session = current_handler_session()
    existing = session.imap_get(CodePrimitiveType, code_primitive_type_id)
    if existing is not None:
        if existing.base_type != base_type or existing.signature != normalized_signature:
            raise RuntimeError(
                "CodePrimitiveType.create signature/base_type mismatch for existing primitive type: "
                + f"code_primitive_type_id={code_primitive_type_id}"
            )
        if existing.constraints != constraints:
            raise RuntimeError(
                "CodePrimitiveType.create constraints mismatch for existing primitive type: "
                + f"code_primitive_type_id={code_primitive_type_id}"
            )
        return existing

    return CodePrimitiveType(
        id=code_primitive_type_id,
        signature=normalized_signature,
        base_type=base_type,
        constraints=constraints,
    )
    # --- AWARE: LOGIC END create


async def create_item_type(
    code_primitive_type: CodePrimitiveType,
    signature: str,
    base_type: CodePrimitiveBaseType,
    constraints: JsonObject | None = None,
) -> CodePrimitiveType:
    """
    Create the item type for array/set-like primitive shapes.
    """

    # --- AWARE: LOGIC START create_item_type
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_item_type


async def create_key_type(
    code_primitive_type: CodePrimitiveType,
    signature: str,
    base_type: CodePrimitiveBaseType,
    constraints: JsonObject | None = None,
) -> CodePrimitiveType:
    """
    Create the key type for dict-like primitive shapes.
    """

    # --- AWARE: LOGIC START create_key_type
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_key_type


async def create_value_type(
    code_primitive_type: CodePrimitiveType,
    signature: str,
    base_type: CodePrimitiveBaseType,
    constraints: JsonObject | None = None,
) -> CodePrimitiveType:
    """
    Create the value type for dict-like primitive shapes.
    """

    # --- AWARE: LOGIC START create_value_type
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_value_type


async def create_element_slot(code_primitive_type: CodePrimitiveType, position: int) -> CodePrimitiveTypeElementType:
    """
    Create one ordered tuple element slot under this primitive type.
    """

    # --- AWARE: LOGIC START create_element_slot
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_element_slot


async def create_union_slot(code_primitive_type: CodePrimitiveType, position: int) -> CodePrimitiveTypeUnionType:
    """
    Create one ordered union member slot under this primitive type.
    """

    # --- AWARE: LOGIC START create_union_slot
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_union_slot
