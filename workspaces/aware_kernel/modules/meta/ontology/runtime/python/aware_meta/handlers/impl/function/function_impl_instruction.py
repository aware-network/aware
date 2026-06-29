from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplInstructionType,
    FunctionImplInvokeKind,
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
    FunctionImplValueSourceKind,
)
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.function.function_impl_instruction_construct import FunctionImplInstructionConstruct
from aware_meta_ontology.function.function_impl_instruction_invoke import FunctionImplInstructionInvoke
from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet
from aware_meta_ontology.function.function_impl_instruction_require import FunctionImplInstructionRequire
from aware_meta_ontology.function.function_impl_instruction_set import FunctionImplInstructionSet
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Runtime
from aware_meta_ontology.stable_ids import stable_function_impl_instruction_id

# Meta Ontology
from aware_meta_ontology.function.function_impl import FunctionImpl

# Aware Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def attach_let(
    function_impl_instruction: FunctionImplInstruction, name: str, value_expr: JsonObject
) -> FunctionImplInstructionLet:
    """
    Attach deterministic `let` payload under this instruction.
    """

    # --- AWARE: LOGIC START attach_let
    if function_impl_instruction.type != FunctionImplInstructionType.let:
        raise RuntimeError(
            "FunctionImplInstruction.attach_let requires instruction type 'let': "
            f"instruction_id={function_impl_instruction.id} type={function_impl_instruction.type.value}"
        )

    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.attach_let requires FunctionImplInstruction.id")

    created = await FunctionImplInstructionLet.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        name=name,
        value_expr=value_expr,
    )
    function_impl_instruction.instruction_let = created
    return created
    # --- AWARE: LOGIC END attach_let


async def attach_invoke(
    function_impl_instruction: FunctionImplInstruction,
    target_function_config_id: UUID,
    class_config_relationship_id: UUID | None = None,
    kind: FunctionImplInvokeKind = FunctionImplInvokeKind.call,
) -> FunctionImplInstructionInvoke:
    """
    Attach deterministic `invoke` payload under this instruction.
    """

    # --- AWARE: LOGIC START attach_invoke
    if function_impl_instruction.type != FunctionImplInstructionType.invoke:
        raise RuntimeError(
            "FunctionImplInstruction.attach_invoke requires instruction type 'invoke': "
            f"instruction_id={function_impl_instruction.id} type={function_impl_instruction.type.value}"
        )

    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.attach_invoke requires FunctionImplInstruction.id")

    created = await FunctionImplInstructionInvoke.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        target_function_config_id=target_function_config_id,
        class_config_relationship_id=class_config_relationship_id,
        kind=kind,
    )
    function_impl_instruction.instruction_invoke = created
    return created
    # --- AWARE: LOGIC END attach_invoke


async def attach_construct(
    function_impl_instruction: FunctionImplInstruction, target_class_config_id: UUID
) -> FunctionImplInstructionConstruct:
    """
    Attach deterministic object-construction payload under this instruction.
    """

    # --- AWARE: LOGIC START attach_construct
    if function_impl_instruction.type != FunctionImplInstructionType.construct:
        raise RuntimeError(
            "FunctionImplInstruction.attach_construct requires instruction type 'construct': "
            f"instruction_id={function_impl_instruction.id} type={function_impl_instruction.type.value}"
        )

    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.attach_construct requires FunctionImplInstruction.id")

    created = await FunctionImplInstructionConstruct.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        target_class_config_id=target_class_config_id,
    )
    function_impl_instruction.instruction_construct = created
    return created
    # --- AWARE: LOGIC END attach_construct


async def attach_set(
    function_impl_instruction: FunctionImplInstruction,
    target_class_config_attribute_config_id: UUID,
    value_source_id: UUID,
) -> FunctionImplInstructionSet:
    """
    Attach deterministic `set` payload under this instruction.
    """

    # --- AWARE: LOGIC START attach_set
    if function_impl_instruction.type != FunctionImplInstructionType.set:
        raise RuntimeError(
            "FunctionImplInstruction.attach_set requires instruction type 'set': "
            f"instruction_id={function_impl_instruction.id} type={function_impl_instruction.type.value}"
        )

    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.attach_set requires FunctionImplInstruction.id")

    created = await FunctionImplInstructionSet.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        target_class_config_attribute_config_id=target_class_config_attribute_config_id,
        value_source_id=value_source_id,
    )
    function_impl_instruction.instruction_set = created
    return created
    # --- AWARE: LOGIC END attach_set


async def attach_require(
    function_impl_instruction: FunctionImplInstruction,
    kind: FunctionImplRequireKind,
    compare_operator: FunctionImplRequireCompareOperator | None = None,
    expected_count: int | None = None,
    message: str | None = None,
) -> FunctionImplInstructionRequire:
    """
    Attach deterministic `require` payload under this instruction.
    """

    # --- AWARE: LOGIC START attach_require
    if function_impl_instruction.type != FunctionImplInstructionType.require:
        raise RuntimeError(
            "FunctionImplInstruction.attach_require requires instruction type 'require': "
            f"instruction_id={function_impl_instruction.id} type={function_impl_instruction.type.value}"
        )

    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.attach_require requires FunctionImplInstruction.id")

    created = await FunctionImplInstructionRequire.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        kind=kind,
        compare_operator=compare_operator,
        expected_count=expected_count,
        message=message,
    )
    function_impl_instruction.instruction_require = created
    return created
    # --- AWARE: LOGIC END attach_require


async def create_value_source(
    function_impl_instruction: FunctionImplInstruction,
    key: str,
    kind: FunctionImplValueSourceKind,
    source_function_config_attribute_config_id: UUID | None = None,
    source_instruction_let_id: UUID | None = None,
) -> FunctionImplValueSource:
    """
    Create one deterministic value source local to this instruction.
    """

    # --- AWARE: LOGIC START create_value_source
    function_impl_instruction_id = function_impl_instruction.id
    if function_impl_instruction_id is None:
        raise RuntimeError("FunctionImplInstruction.create_value_source requires FunctionImplInstruction.id")

    created = await FunctionImplValueSource.build_via_function_impl_instruction(
        function_impl_instruction_id=function_impl_instruction_id,
        key=key,
        kind=kind,
        source_function_config_attribute_config_id=source_function_config_attribute_config_id,
        source_instruction_let_id=source_instruction_let_id,
    )
    if all(existing.id != created.id for existing in function_impl_instruction.value_sources):
        function_impl_instruction.value_sources.append(created)
    return created
    # --- AWARE: LOGIC END create_value_source


async def build_via_function_impl(
    function_impl_id: UUID, type: FunctionImplInstructionType, sequence: int
) -> FunctionImplInstruction:
    """
    Create deterministic FunctionImplInstruction under one FunctionImpl parent path.

    Contract:
    - Parent context (`function_impl_id`) is injected by parent-edge lowering.
    - Constructor identity keys are `(type, sequence)` plus propagated parent scope.
    """

    # --- AWARE: LOGIC START build_via_function_impl
    if sequence < 0:
        raise RuntimeError("FunctionImplInstruction.build_via_function requires sequence >= 0")

    session = current_handler_session()
    function_impl = session.imap_get(FunctionImpl, function_impl_id)
    if function_impl is None:
        raise RuntimeError(
            "FunctionImplInstruction.build_via_function requires existing FunctionImpl: "
            f"function_impl_id={function_impl_id}"
        )

    type_value = str(getattr(type, "value", type))
    function_impl_instruction_id = stable_function_impl_instruction_id(
        function_impl_id=function_impl_id,
        type=type_value,
        sequence=sequence,
    )
    existing = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if existing is not None:
        if existing.function_impl_id != function_impl_id or existing.type != type or existing.sequence != sequence:
            raise RuntimeError(
                "FunctionImplInstruction.build_via_function payload mismatch for existing instruction: "
                f"function_impl_instruction_id={function_impl_instruction_id}"
            )
        return existing

    return FunctionImplInstruction(
        id=function_impl_instruction_id,
        function_impl_id=function_impl_id,
        type=type,
        sequence=sequence,
    )
    # --- AWARE: LOGIC END build_via_function_impl
