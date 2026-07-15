from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplInvokeKind
from aware_meta_ontology.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
from aware_meta_ontology.function.function_impl_instruction_invoke_attribute_config import (
    FunctionImplInstructionInvokeAttributeConfig,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_invoke_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_attribute_config(
    function_impl_instruction_invoke: FunctionImplInstructionInvoke,
    attribute_config_id: UUID,
    value_expr: JsonObject,
    position: int | None = None,
) -> FunctionImplInstructionInvokeAttributeConfig:
    """
    Attach one deterministic invoke argument binding by AttributeConfig contract.
    """

    # --- AWARE: LOGIC START add_attribute_config
    function_impl_instruction_invoke_id = function_impl_instruction_invoke.id
    if function_impl_instruction_invoke_id is None:
        raise RuntimeError(
            "FunctionImplInstructionInvoke.add_attribute_config requires FunctionImplInstructionInvoke.id"
        )

    if position is not None and position < 0:
        raise RuntimeError("FunctionImplInstructionInvoke.add_attribute_config requires position >= 0 when provided")

    created = await FunctionImplInstructionInvokeAttributeConfig.create_via_function_impl_instruction_invoke(
        function_impl_instruction_invoke_id=function_impl_instruction_invoke_id,
        attribute_config_id=attribute_config_id,
        value_expr=value_expr,
        position=position,
    )
    if all(existing.id != created.id for existing in function_impl_instruction_invoke.attribute_configs):
        function_impl_instruction_invoke.attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_attribute_config


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID,
    target_function_config_id: UUID,
    class_config_relationship_id: UUID | None = None,
    kind: FunctionImplInvokeKind = FunctionImplInvokeKind.call,
) -> FunctionImplInstructionInvoke:
    """
    Create deterministic `invoke` payload for one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    session = current_handler_session()
    parent_instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionInvoke.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "invoke":
        raise RuntimeError(
            "FunctionImplInstructionInvoke.build_via_function requires parent instruction type 'invoke': "
            f"function_impl_instruction_id={function_impl_instruction_id} type={parent_instruction.type.value}"
        )

    target_function_config = session.imap_get(FunctionConfig, target_function_config_id)
    if target_function_config is None:
        raise RuntimeError(
            "FunctionImplInstructionInvoke.build_via_function requires existing target FunctionConfig: "
            f"target_function_config_id={target_function_config_id}"
        )

    class_config_relationship = None
    if class_config_relationship_id is not None:
        class_config_relationship = session.imap_get(ClassConfigRelationship, class_config_relationship_id)
        if class_config_relationship is None:
            raise RuntimeError(
                "FunctionImplInstructionInvoke.build_via_function requires existing ClassConfigRelationship: "
                f"class_config_relationship_id={class_config_relationship_id}"
            )

    function_impl_instruction_invoke_id = stable_function_impl_instruction_invoke_id(
        function_impl_instruction_id=function_impl_instruction_id
    )
    existing = session.imap_get(FunctionImplInstructionInvoke, function_impl_instruction_invoke_id)
    if existing is not None:
        if (
            existing.target_function_config_id != target_function_config_id
            or existing.class_config_relationship_id != class_config_relationship_id
            or existing.kind != kind
        ):
            raise RuntimeError(
                "FunctionImplInstructionInvoke.build_via_function payload mismatch for existing invoke payload: "
                f"function_impl_instruction_invoke_id={function_impl_instruction_invoke_id}"
            )
        return existing

    return FunctionImplInstructionInvoke(
        id=function_impl_instruction_invoke_id,
        target_function_config=target_function_config,
        target_function_config_id=target_function_config_id,
        class_config_relationship=class_config_relationship,
        class_config_relationship_id=class_config_relationship_id,
        kind=kind,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
