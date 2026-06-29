from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import Json

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplValueSourceKind,
    FunctionImplValueTransformKind,
)
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource
from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
    FunctionImplValueSourceLiteralPrimitive,
)
from aware_meta_ontology.function.function_impl_value_source_transform import FunctionImplValueSourceTransform

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.function.function_impl_instruction_let import FunctionImplInstructionLet
from aware_meta_ontology.function.function_impl_instruction import FunctionImplInstruction
from aware_meta_ontology.stable_ids import stable_function_impl_value_source_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def attach_literal_primitive(
    function_impl_value_source: FunctionImplValueSource, primitive_config_id: UUID, value: Json
) -> FunctionImplValueSourceLiteralPrimitive:
    """
    Attach deterministic primitive literal payload when `kind == literal`.
    """

    # --- AWARE: LOGIC START attach_literal_primitive
    if not isinstance(primitive_config_id, UUID):
        try:
            primitive_config_id = UUID(str(primitive_config_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplValueSource.attach_literal_primitive requires "
                "UUID-compatible primitive_config_id: "
                f"primitive_config_id={primitive_config_id!r}"
            ) from exc
    if function_impl_value_source.kind != FunctionImplValueSourceKind.literal:
        raise RuntimeError(
            "FunctionImplValueSource.attach_literal_primitive requires kind 'literal': "
            f"value_source_id={function_impl_value_source.id} kind={function_impl_value_source.kind.value}"
        )

    function_impl_value_source_id = function_impl_value_source.id
    if function_impl_value_source_id is None:
        raise RuntimeError("FunctionImplValueSource.attach_literal_primitive requires FunctionImplValueSource.id")

    created = await FunctionImplValueSourceLiteralPrimitive.build_via_function_impl_value_source(
        function_impl_value_source_id=function_impl_value_source_id,
        primitive_config_id=primitive_config_id,
        value=value,
    )

    existing = function_impl_value_source.source_literal_primitive
    if existing is not None and existing.id != created.id:
        raise RuntimeError(
            "FunctionImplValueSource.attach_literal_primitive encountered conflicting literal payload: "
            f"value_source_id={function_impl_value_source_id} "
            f"existing_literal_id={existing.id} created_literal_id={created.id}"
        )

    function_impl_value_source.source_literal_primitive = created
    return created
    # --- AWARE: LOGIC END attach_literal_primitive


async def attach_transform(
    function_impl_value_source: FunctionImplValueSource,
    operation: FunctionImplValueTransformKind,
    output_primitive_config_id: UUID | None = None,
) -> FunctionImplValueSourceTransform:
    """
    Attach deterministic pure-transform payload when `kind == transform`.
    """

    # --- AWARE: LOGIC START attach_transform
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_transform


async def update_function_input_ref(
    function_impl_value_source: FunctionImplValueSource, source_function_config_attribute_config_id: UUID
) -> None:
    """
    Update an existing function-input value source to point at another input edge.

    Contract:
    - The value source identity and key remain stable.
    - Only `function_input_ref` sources are mutable on this rail.
    - Literal and let-ref replacement require their own explicit ontology functions.
    """

    # --- AWARE: LOGIC START update_function_input_ref
    if not isinstance(source_function_config_attribute_config_id, UUID):
        try:
            source_function_config_attribute_config_id = UUID(str(source_function_config_attribute_config_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplValueSource.update_function_input_ref requires "
                "UUID-compatible source_function_config_attribute_config_id: "
                "source_function_config_attribute_config_id="
                f"{source_function_config_attribute_config_id!r}"
            ) from exc
    current_kind = function_impl_value_source.kind
    if not isinstance(current_kind, FunctionImplValueSourceKind):
        raw_kind = str(getattr(current_kind, "value", current_kind)).strip()
        try:
            current_kind = FunctionImplValueSourceKind(raw_kind)
        except ValueError:
            current_kind = FunctionImplValueSourceKind[raw_kind]
    if current_kind != FunctionImplValueSourceKind.function_input_ref:
        raise RuntimeError(
            "FunctionImplValueSource.update_function_input_ref requires kind "
            f"'function_input_ref': value_source_id={function_impl_value_source.id} "
            f"kind={current_kind.value}"
        )
    function_impl_value_source.kind = current_kind

    session = current_handler_session()
    source_function_config_attribute_config = session.imap_get(
        FunctionConfigAttributeConfig,
        source_function_config_attribute_config_id,
    )
    if source_function_config_attribute_config is None:
        raise RuntimeError(
            "FunctionImplValueSource.update_function_input_ref requires existing "
            "FunctionConfigAttributeConfig: "
            "source_function_config_attribute_config_id="
            f"{source_function_config_attribute_config_id}"
        )

    function_impl_value_source.kind = FunctionImplValueSourceKind.function_input_ref
    function_impl_value_source.source_function_config_attribute_config = source_function_config_attribute_config
    function_impl_value_source.source_function_config_attribute_config_id = source_function_config_attribute_config.id
    function_impl_value_source.source_instruction_let = None
    function_impl_value_source.source_instruction_let_id = None
    function_impl_value_source.source_literal_primitive = None
    return None
    # --- AWARE: LOGIC END update_function_input_ref


async def build_via_function_impl_instruction(
    function_impl_instruction_id: UUID,
    key: str,
    kind: FunctionImplValueSourceKind,
    source_function_config_attribute_config_id: UUID | None = None,
    source_instruction_let_id: UUID | None = None,
) -> FunctionImplValueSource:
    """
    Create deterministic value-source payload under one FunctionImplInstruction.

    Contract:
    - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
    - Identity is parent-scoped via stable `key`.
    """

    # --- AWARE: LOGIC START build_via_function_impl_instruction
    if not isinstance(function_impl_instruction_id, UUID):
        try:
            function_impl_instruction_id = UUID(str(function_impl_instruction_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function requires "
                "UUID-compatible function_impl_instruction_id: "
                f"function_impl_instruction_id={function_impl_instruction_id!r}"
            ) from exc
    if source_function_config_attribute_config_id is not None and not isinstance(
        source_function_config_attribute_config_id, UUID
    ):
        try:
            source_function_config_attribute_config_id = UUID(str(source_function_config_attribute_config_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function requires "
                "UUID-compatible source_function_config_attribute_config_id: "
                "source_function_config_attribute_config_id="
                f"{source_function_config_attribute_config_id!r}"
            ) from exc
    if source_instruction_let_id is not None and not isinstance(
        source_instruction_let_id,
        UUID,
    ):
        try:
            source_instruction_let_id = UUID(str(source_instruction_let_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function requires "
                "UUID-compatible source_instruction_let_id: "
                f"source_instruction_let_id={source_instruction_let_id!r}"
            ) from exc
    key_norm = (key or "").strip()
    if not key_norm:
        raise RuntimeError("FunctionImplValueSource.build_via_function requires non-empty key")
    if not isinstance(kind, FunctionImplValueSourceKind):
        raw_kind = str(getattr(kind, "value", kind)).strip()
        try:
            kind = FunctionImplValueSourceKind(raw_kind)
        except ValueError:
            kind = FunctionImplValueSourceKind[raw_kind]

    session = current_handler_session()
    instruction = session.imap_get(FunctionImplInstruction, function_impl_instruction_id)
    if instruction is None:
        raise RuntimeError(
            "FunctionImplValueSource.build_via_function requires existing FunctionImplInstruction: "
            f"function_impl_instruction_id={function_impl_instruction_id}"
        )

    source_function_config_attribute_config = None
    source_instruction_let = None

    if kind == FunctionImplValueSourceKind.literal:
        if source_function_config_attribute_config_id is not None or source_instruction_let_id is not None:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function kind 'literal' forbids source refs "
                "(use attach_literal_primitive)"
            )
    elif kind == FunctionImplValueSourceKind.function_input_ref:
        if source_function_config_attribute_config_id is None or source_instruction_let_id is not None:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function kind 'function_input_ref' requires only "
                "source_function_config_attribute_config_id"
            )
        source_function_config_attribute_config = session.imap_get(
            FunctionConfigAttributeConfig,
            source_function_config_attribute_config_id,
        )
        if source_function_config_attribute_config is None:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function requires existing FunctionConfigAttributeConfig: "
                f"source_function_config_attribute_config_id={source_function_config_attribute_config_id}"
            )
    elif kind == FunctionImplValueSourceKind.let_ref:
        if source_instruction_let_id is None or source_function_config_attribute_config_id is not None:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function kind 'let_ref' requires only " "source_instruction_let_id"
            )
        source_instruction_let = session.imap_get(FunctionImplInstructionLet, source_instruction_let_id)
        if source_instruction_let is None:
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function requires existing FunctionImplInstructionLet: "
                f"source_instruction_let_id={source_instruction_let_id}"
            )
    else:
        raise RuntimeError(f"Unsupported FunctionImplValueSource kind: {kind!r}")

    function_impl_value_source_id = stable_function_impl_value_source_id(
        function_impl_instruction_id=function_impl_instruction_id,
        key=key_norm,
    )
    existing = session.imap_get(FunctionImplValueSource, function_impl_value_source_id)
    if existing is not None:
        if (
            existing.function_impl_instruction_id != function_impl_instruction_id
            or existing.key != key_norm
            or existing.kind != kind
            or existing.source_function_config_attribute_config_id != source_function_config_attribute_config_id
            or existing.source_instruction_let_id != source_instruction_let_id
        ):
            raise RuntimeError(
                "FunctionImplValueSource.build_via_function payload mismatch for existing value source: "
                f"function_impl_value_source_id={function_impl_value_source_id}"
            )
        return existing

    return FunctionImplValueSource(
        id=function_impl_value_source_id,
        function_impl_instruction_id=function_impl_instruction_id,
        key=key_norm,
        kind=kind,
        source_function_config_attribute_config=source_function_config_attribute_config,
        source_function_config_attribute_config_id=source_function_config_attribute_config_id,
        source_instruction_let=source_instruction_let,
        source_instruction_let_id=source_instruction_let_id,
    )
    # --- AWARE: LOGIC END build_via_function_impl_instruction
