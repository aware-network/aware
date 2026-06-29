from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_set import FunctionImplInstructionSet

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_set_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def update_assignment(
    function_impl_instruction_set: FunctionImplInstructionSet,
    target_class_config_attribute_config_id: UUID,
    value_source_id: UUID,
) -> None:
    """
    Update the mutable assignment payload for an existing `set` instruction.

    Contract:
    - The FunctionImplInstructionSet identity is stable for the parent instruction.
    - The target attribute and value source must already exist as ontology truth.
    - The value source must belong to the same FunctionImplInstruction.
    """

    # --- AWARE: LOGIC START update_assignment
    if not isinstance(target_class_config_attribute_config_id, UUID):
        try:
            target_class_config_attribute_config_id = UUID(str(target_class_config_attribute_config_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.update_assignment requires "
                "UUID-compatible target_class_config_attribute_config_id: "
                "target_class_config_attribute_config_id="
                f"{target_class_config_attribute_config_id!r}"
            ) from exc
    if not isinstance(value_source_id, UUID):
        try:
            value_source_id = UUID(str(value_source_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.update_assignment requires "
                "UUID-compatible value_source_id: "
                f"value_source_id={value_source_id!r}"
            ) from exc

    function_impl_instruction_id = function_impl_instruction_set.function_impl_instruction_id
    if function_impl_instruction_id is not None and not isinstance(
        function_impl_instruction_id,
        UUID,
    ):
        try:
            function_impl_instruction_id = UUID(str(function_impl_instruction_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.update_assignment requires "
                "UUID-compatible function_impl_instruction_id: "
                f"function_impl_instruction_id={function_impl_instruction_id!r}"
            ) from exc
    if function_impl_instruction_id is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires "
            "FunctionImplInstructionSet.function_impl_instruction_id"
        )

    session = current_handler_session()
    parent_instruction = session.imap_get(
        FunctionImplInstruction,
        function_impl_instruction_id,
    )
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires existing "
            "FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "set":
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires parent "
            "instruction type 'set': "
            f"function_impl_instruction_id={function_impl_instruction_id} "
            f"type={parent_instruction.type.value}"
        )

    target_class_config_attribute_config = session.imap_get(
        ClassConfigAttributeConfig,
        target_class_config_attribute_config_id,
    )
    if target_class_config_attribute_config is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires existing "
            "ClassConfigAttributeConfig: "
            f"target_class_config_attribute_config_id={target_class_config_attribute_config_id}"
        )

    value_source = session.imap_get(FunctionImplValueSource, value_source_id)
    if value_source is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires existing "
            f"FunctionImplValueSource: value_source_id={value_source_id}"
        )
    if value_source.function_impl_instruction_id != function_impl_instruction_id:
        raise RuntimeError(
            "FunctionImplInstructionSet.update_assignment requires value source "
            "from same instruction: "
            f"function_impl_instruction_id={function_impl_instruction_id} "
            f"value_source_instruction_id={value_source.function_impl_instruction_id}"
        )

    function_impl_instruction_set.target_class_config_attribute_config = target_class_config_attribute_config
    function_impl_instruction_set.target_class_config_attribute_config_id = target_class_config_attribute_config.id
    function_impl_instruction_set.value_source = value_source
    function_impl_instruction_set.value_source_id = value_source.id
    return None
    # --- AWARE: LOGIC END update_assignment


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID, target_class_config_attribute_config_id: UUID, value_source_id: UUID
) -> FunctionImplInstructionSet:
    """
    Create deterministic `set` payload for one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    if not isinstance(function_impl_instruction_id, UUID):
        try:
            function_impl_instruction_id = UUID(str(function_impl_instruction_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.build_via_function requires "
                "UUID-compatible function_impl_instruction_id: "
                f"function_impl_instruction_id={function_impl_instruction_id!r}"
            ) from exc
    if not isinstance(target_class_config_attribute_config_id, UUID):
        try:
            target_class_config_attribute_config_id = UUID(str(target_class_config_attribute_config_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.build_via_function requires "
                "UUID-compatible target_class_config_attribute_config_id: "
                "target_class_config_attribute_config_id="
                f"{target_class_config_attribute_config_id!r}"
            ) from exc
    if not isinstance(value_source_id, UUID):
        try:
            value_source_id = UUID(str(value_source_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplInstructionSet.build_via_function requires "
                "UUID-compatible value_source_id: "
                f"value_source_id={value_source_id!r}"
            ) from exc

    session = current_handler_session()
    parent_instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if parent_instruction is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )
    if parent_instruction.type.value != "set":
        raise RuntimeError(
            "FunctionImplInstructionSet.build_via_function requires parent instruction type 'set': "
            f"function_impl_instruction_id={function_impl_instruction_id} type={parent_instruction.type.value}"
        )

    target_class_config_attribute_config = session.imap_get(
        ClassConfigAttributeConfig,
        target_class_config_attribute_config_id,
    )
    if target_class_config_attribute_config is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.build_via_function requires existing ClassConfigAttributeConfig: "
            f"target_class_config_attribute_config_id={target_class_config_attribute_config_id}"
        )

    value_source = session.imap_get(FunctionImplValueSource, value_source_id)
    if value_source is None:
        raise RuntimeError(
            "FunctionImplInstructionSet.build_via_function requires existing FunctionImplValueSource: "
            f"value_source_id={value_source_id}"
        )
    if value_source.function_impl_instruction_id != function_impl_instruction_id:
        raise RuntimeError(
            "FunctionImplInstructionSet.build_via_function requires value source from same instruction: "
            f"function_impl_instruction_id={function_impl_instruction_id} "
            f"value_source_instruction_id={value_source.function_impl_instruction_id}"
        )

    function_impl_instruction_set_id = stable_function_impl_instruction_set_id(
        function_impl_instruction_id=function_impl_instruction_id
    )
    existing = session.imap_get(FunctionImplInstructionSet, function_impl_instruction_set_id)
    if existing is not None:
        if (
            existing.target_class_config_attribute_config_id != target_class_config_attribute_config_id
            or existing.value_source_id != value_source_id
        ):
            raise RuntimeError(
                "FunctionImplInstructionSet.build_via_function payload mismatch for existing set payload: "
                f"function_impl_instruction_set_id={function_impl_instruction_set_id}"
            )
        return existing

    return FunctionImplInstructionSet(
        id=function_impl_instruction_set_id,
        function_impl_instruction_id=function_impl_instruction_id,
        target_class_config_attribute_config=target_class_config_attribute_config,
        target_class_config_attribute_config_id=target_class_config_attribute_config.id,
        value_source=value_source,
        value_source_id=value_source.id,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
