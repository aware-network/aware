from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_invoke_attribute_config_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_function_impl_instruction_invoke(
    function_impl_instruction_invoke_id: UUID,
    attribute_config_id: UUID,
    value_expr: JsonObject,
    position: int | None = None,
) -> FunctionImplInstructionInvokeAttributeConfig:
    """
    Create deterministic invoke-argument binding under one invoke payload.
    """

    # --- AWARE: LOGIC START create_via_function_impl_instruction_invoke
    if position is not None and position < 0:
        raise RuntimeError(
            "FunctionImplInstructionInvokeAttributeConfig.create_via_function requires position >= 0 when provided"
        )

    session = current_handler_session()
    invoke_payload = session.imap_get(FunctionImplInstructionInvoke, function_impl_instruction_invoke_id)
    if invoke_payload is None:
        raise RuntimeError(
            "FunctionImplInstructionInvokeAttributeConfig.create_via_function requires existing invoke payload: "
            f"function_impl_instruction_invoke_id={function_impl_instruction_invoke_id}"
        )

    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "FunctionImplInstructionInvokeAttributeConfig.create_via_function requires existing AttributeConfig: "
            f"attribute_config_id={attribute_config_id}"
        )

    function_impl_instruction_invoke_attribute_config_id = stable_function_impl_instruction_invoke_attribute_config_id(
        function_impl_instruction_invoke_id=function_impl_instruction_invoke_id,
        attribute_config_id=attribute_config_id,
    )
    existing = session.imap_get(
        FunctionImplInstructionInvokeAttributeConfig,
        function_impl_instruction_invoke_attribute_config_id,
    )
    if existing is not None:
        if (
            existing.function_impl_instruction_invoke_id != function_impl_instruction_invoke_id
            or existing.attribute_config_id != attribute_config_id
            or existing.value_expr != value_expr
            or existing.position != position
        ):
            raise RuntimeError(
                "FunctionImplInstructionInvokeAttributeConfig.create_via_function payload mismatch for existing "
                "invoke binding: "
                f"function_impl_instruction_invoke_attribute_config_id="
                f"{function_impl_instruction_invoke_attribute_config_id}"
            )
        return existing

    return FunctionImplInstructionInvokeAttributeConfig(
        id=function_impl_instruction_invoke_attribute_config_id,
        function_impl_instruction_invoke_id=function_impl_instruction_invoke_id,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        value_expr=value_expr,
        position=position,
    )
    # --- AWARE: LOGIC END create_via_function_impl_instruction_invoke
