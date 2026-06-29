from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_construct import FunctionImplInstructionConstruct
from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
    FunctionImplInstructionConstructAssignment,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.stable_ids import (
    stable_function_impl_instruction_construct_id,
)

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_assignment(
    function_impl_instruction_construct: FunctionImplInstructionConstruct,
    target_class_config_attribute_config_id: UUID,
    value_source_id: UUID,
    position: int | None = None,
) -> FunctionImplInstructionConstructAssignment:
    """
    Attach one deterministic class-attribute assignment under this construct payload.
    """

    # --- AWARE: LOGIC START add_assignment
    function_impl_instruction_construct_id = function_impl_instruction_construct.id
    if function_impl_instruction_construct_id is None:
        raise RuntimeError(
            "FunctionImplInstructionConstruct.add_assignment requires FunctionImplInstructionConstruct.id"
        )

    created = await FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct(
        function_impl_instruction_construct_id=function_impl_instruction_construct_id,
        target_class_config_attribute_config_id=target_class_config_attribute_config_id,
        value_source_id=value_source_id,
        position=position,
    )
    if all(existing.id != created.id for existing in function_impl_instruction_construct.assignments):
        function_impl_instruction_construct.assignments.append(created)
    return created
    # --- AWARE: LOGIC END add_assignment


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID, target_class_config_id: UUID
) -> FunctionImplInstructionConstruct:
    """
    Create deterministic explicit construct payload for one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    session = current_handler_session()
    parent_instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionConstruct.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "construct":
        raise RuntimeError(
            "FunctionImplInstructionConstruct.build_via_function requires parent instruction type 'construct': "
            f"function_impl_instruction_id={function_impl_instruction_id} type={parent_instruction.type.value}"
        )

    target_class_config = session.imap_get(ClassConfig, target_class_config_id)
    if target_class_config is None:
        raise RuntimeError(
            "FunctionImplInstructionConstruct.build_via_function requires existing ClassConfig: "
            f"target_class_config_id={target_class_config_id}"
        )

    function_impl_instruction_construct_id = stable_function_impl_instruction_construct_id(
        function_impl_instruction_id=function_impl_instruction_id,
    )
    existing = session.imap_get(FunctionImplInstructionConstruct, function_impl_instruction_construct_id)
    if existing is not None:
        if existing.target_class_config_id != target_class_config_id:
            raise RuntimeError(
                "FunctionImplInstructionConstruct.build_via_function payload mismatch for existing construct payload: "
                f"function_impl_instruction_construct_id={function_impl_instruction_construct_id}"
            )
        return existing

    return FunctionImplInstructionConstruct(
        id=function_impl_instruction_construct_id,
        target_class_config=target_class_config,
        target_class_config_id=target_class_config.id,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
