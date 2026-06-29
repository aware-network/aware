from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplInstructionType
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Runtime
from aware_meta_ontology.stable_ids import stable_function_impl_id

# Meta Ontology
from aware_meta_ontology.function.function_config import FunctionConfig

# Aware Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_instruction(
    function_impl: FunctionImpl, type: FunctionImplInstructionType, sequence: int
) -> FunctionImplInstruction:
    """
    Create one deterministic instruction under this FunctionImpl.
    """

    # --- AWARE: LOGIC START create_instruction
    function_impl_id = function_impl.id
    if function_impl_id is None:
        raise RuntimeError("FunctionImpl.create_instruction requires FunctionImpl.id")

    created = await FunctionImplInstruction.build_via_function_impl(
        function_impl_id=function_impl_id,
        type=type,
        sequence=sequence,
    )
    if all(existing.id != created.id for existing in function_impl.instructions):
        function_impl.instructions.append(created)
    return created
    # --- AWARE: LOGIC END create_instruction


async def remove_instruction(function_impl: FunctionImpl, type: FunctionImplInstructionType, sequence: int) -> None:
    """
    Remove one deterministic instruction from this FunctionImpl.
    """

    # --- AWARE: LOGIC START remove_instruction
    if not isinstance(type, FunctionImplInstructionType):
        raw_type = str(type)
        try:
            type = FunctionImplInstructionType(raw_type)
        except ValueError:
            type = FunctionImplInstructionType[raw_type]
    try:
        sequence_int = int(sequence)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "FunctionImpl.remove_instruction requires int-compatible sequence: " f"sequence={sequence!r}"
        ) from exc

    remaining: list[FunctionImplInstruction] = []
    removed = False
    for existing in function_impl.instructions:
        existing_type = existing.type
        if not isinstance(existing_type, FunctionImplInstructionType):
            raw_existing_type = str(existing_type)
            try:
                existing_type = FunctionImplInstructionType(raw_existing_type)
            except ValueError:
                existing_type = FunctionImplInstructionType[raw_existing_type]
        try:
            existing_sequence = int(existing.sequence)
        except (TypeError, ValueError):
            remaining.append(existing)
            continue
        if existing_type == type and existing_sequence == sequence_int:
            removed = True
            continue
        remaining.append(existing)
    if removed:
        function_impl.instructions = remaining
    return None
    # --- AWARE: LOGIC END remove_instruction


async def build_via_function_config(
    function_config_id: UUID, key: str = "default", kind: FunctionImplKind = FunctionImplKind.instruction_body
) -> FunctionImpl:
    """
    Create deterministic FunctionImpl under one FunctionConfig parent path.

    Contract:
    - `instruction_body` means the implementation owns executable instruction payloads.
    - `auto_constructor` means a bodyless construct declaration materializes through constructor
    identity rails.
    """

    # --- AWARE: LOGIC START build_via_function_config
    key_norm = (key or "").strip() or "default"

    session = current_handler_session()
    function_config = session.imap_get(FunctionConfig, function_config_id)
    if function_config is None:
        raise RuntimeError(
            "FunctionImpl.build_via_function requires existing FunctionConfig: "
            f"function_config_id={function_config_id}"
        )

    function_impl_id = stable_function_impl_id(function_config_id=function_config_id)
    existing = session.imap_get(FunctionImpl, function_impl_id)
    if existing is not None:
        if existing.key != key_norm or (
            existing.function_config_id is not None and existing.function_config_id != function_config_id
        ):
            raise RuntimeError(
                "FunctionImpl.build_via_function payload mismatch for existing impl: "
                f"function_impl_id={function_impl_id}"
            )
        return existing

    return FunctionImpl(
        id=function_impl_id,
        key=key_norm,
        function_config_id=function_config_id,
    )
    # --- AWARE: LOGIC END build_via_function_config
