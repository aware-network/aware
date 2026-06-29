from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
    FunctionImplInstructionConstructAssignment,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.function.function_impl_instruction_construct import FunctionImplInstructionConstruct
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_construct_assignment_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_function_impl_instruction_construct(
    function_impl_instruction_construct_id: UUID,
    target_class_config_attribute_config_id: UUID,
    value_source_id: UUID,
    position: int | None = None,
) -> FunctionImplInstructionConstructAssignment:
    """
    Create deterministic construct assignment under one FunctionImplInstructionConstruct.

    Contract:
    - Parent context (`function_impl_instruction_construct_id`) is injected by parent-edge lowering.
    - Constructor identity keys are `(target_class_config_attribute_config_id, value_source_id)` plus
    parent scope.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction_construct
    if position is not None and position < 0:
        raise RuntimeError(
            "FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct requires "
            "position >= 0 when provided"
        )

    session = current_handler_session()
    parent_construct = session.imap_get(
        FunctionImplInstructionConstruct,
        function_impl_instruction_construct_id,
    )
    if parent_construct is None:
        raise RuntimeError(
            "FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct requires "
            "existing construct payload: "
            f"function_impl_instruction_construct_id={function_impl_instruction_construct_id}"
        )

    target_class_config_attribute_config = session.imap_get(
        ClassConfigAttributeConfig,
        target_class_config_attribute_config_id,
    )
    if target_class_config_attribute_config is None:
        raise RuntimeError(
            "FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct requires "
            "existing "
            "ClassConfigAttributeConfig: "
            f"target_class_config_attribute_config_id={target_class_config_attribute_config_id}"
        )

    value_source = session.imap_get(FunctionImplValueSource, value_source_id)
    if value_source is None:
        raise RuntimeError(
            "FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct requires "
            "existing FunctionImplValueSource: "
            f"value_source_id={value_source_id}"
        )

    function_impl_instruction_construct_assignment_id = stable_function_impl_instruction_construct_assignment_id(
        function_impl_instruction_construct_id=function_impl_instruction_construct_id,
        target_class_config_attribute_config_id=target_class_config_attribute_config_id,
        value_source_id=value_source_id,
    )
    existing = session.imap_get(
        FunctionImplInstructionConstructAssignment,
        function_impl_instruction_construct_assignment_id,
    )
    if existing is not None:
        if (
            existing.function_impl_instruction_construct_id != function_impl_instruction_construct_id
            or existing.target_class_config_attribute_config_id != target_class_config_attribute_config_id
            or existing.value_source_id != value_source_id
            or existing.position != position
        ):
            raise RuntimeError(
                "FunctionImplInstructionConstructAssignment.build_via_function_impl_instruction_construct payload "
                "mismatch for existing "
                "assignment: "
                "function_impl_instruction_construct_assignment_id="
                f"{function_impl_instruction_construct_assignment_id}"
            )
        return existing

    return FunctionImplInstructionConstructAssignment(
        id=function_impl_instruction_construct_assignment_id,
        function_impl_instruction_construct_id=function_impl_instruction_construct_id,
        target_class_config_attribute_config=target_class_config_attribute_config,
        target_class_config_attribute_config_id=target_class_config_attribute_config.id,
        value_source=value_source,
        value_source_id=value_source.id,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction_construct
