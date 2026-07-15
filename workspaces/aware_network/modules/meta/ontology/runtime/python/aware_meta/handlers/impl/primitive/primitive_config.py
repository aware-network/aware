from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.primitive.code_primitive_type import CodePrimitiveType

# Code Runtime
from aware_code.primitive_signature import build_code_primitive_signature

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    primitive_config_id: UUID, primitive_type_id: UUID, primitive_base_type: CodePrimitiveBaseType
) -> PrimitiveConfig:
    """
    Create deterministic PrimitiveConfig with explicit identity.
    """

    # --- AWARE: LOGIC START create
    session = current_handler_session()
    existing = session.imap_get(PrimitiveConfig, primitive_config_id)
    if existing is not None:
        if existing.primitive_type_id != primitive_type_id:
            raise RuntimeError(
                "PrimitiveConfig.create primitive_type_id mismatch for existing config: "
                f"primitive_config_id={primitive_config_id}"
            )
        if existing.primitive_type is not None and existing.primitive_type.base_type != primitive_base_type:
            raise RuntimeError(
                "PrimitiveConfig.create primitive_base_type mismatch for existing config: "
                f"primitive_config_id={primitive_config_id}"
            )
        return existing

    primitive_signature = build_code_primitive_signature(base_type=primitive_base_type)
    primitive_type = await CodePrimitiveType.create(
        signature=primitive_signature,
        base_type=primitive_base_type,
    )
    if primitive_type.id != primitive_type_id:
        raise RuntimeError(
            "PrimitiveConfig.create primitive_type_id mismatch for canonical primitive signature: "
            f"primitive_config_id={primitive_config_id} primitive_type_id={primitive_type_id} "
            f"canonical_primitive_type_id={primitive_type.id}"
        )

    config = PrimitiveConfig(
        id=primitive_config_id,
        primitive_type=primitive_type,
        primitive_type_id=primitive_type_id,
    )
    return config
    # --- AWARE: LOGIC END create
