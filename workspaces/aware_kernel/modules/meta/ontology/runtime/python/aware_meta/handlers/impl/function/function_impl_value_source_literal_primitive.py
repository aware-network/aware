from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import Json

# Meta Ontology
from aware_meta_ontology.function.function_impl_value_source_literal_primitive import (
    FunctionImplValueSourceLiteralPrimitive,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplValueSourceKind
from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_meta_ontology.stable_ids import stable_function_impl_value_source_literal_primitive_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_function_impl_value_source(
    function_impl_value_source_id: UUID, primitive_config_id: UUID, value: Json
) -> FunctionImplValueSourceLiteralPrimitive:
    """
    Create deterministic primitive literal payload under one FunctionImplValueSource.
    """

    # --- AWARE: LOGIC START build_via_function_impl_value_source
    session = current_handler_session()
    value_source = session.imap_get(FunctionImplValueSource, function_impl_value_source_id)
    if value_source is None:
        raise RuntimeError(
            "FunctionImplValueSourceLiteralPrimitive.build_via_function requires existing FunctionImplValueSource: "
            f"function_impl_value_source_id={function_impl_value_source_id}"
        )
    if value_source.kind != FunctionImplValueSourceKind.literal:
        raise RuntimeError(
            "FunctionImplValueSourceLiteralPrimitive.build_via_function requires source kind 'literal': "
            f"function_impl_value_source_id={function_impl_value_source_id} kind={value_source.kind.value}"
        )

    primitive_config = session.imap_get(PrimitiveConfig, primitive_config_id)
    if primitive_config is None:
        raise RuntimeError(
            "FunctionImplValueSourceLiteralPrimitive.build_via_function requires existing PrimitiveConfig: "
            f"primitive_config_id={primitive_config_id}"
        )

    function_impl_value_source_literal_primitive_id = stable_function_impl_value_source_literal_primitive_id(
        function_impl_value_source_id=function_impl_value_source_id
    )
    existing = session.imap_get(
        FunctionImplValueSourceLiteralPrimitive,
        function_impl_value_source_literal_primitive_id,
    )
    if existing is not None:
        if existing.primitive_config_id != primitive_config_id or existing.value != value:
            raise RuntimeError(
                "FunctionImplValueSourceLiteralPrimitive.build_via_function payload mismatch for existing literal "
                "payload: "
                f"function_impl_value_source_literal_primitive_id={function_impl_value_source_literal_primitive_id}"
            )
        return existing

    return FunctionImplValueSourceLiteralPrimitive(
        id=function_impl_value_source_literal_primitive_id,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
        value=value,
    )
    # --- AWARE: LOGIC END build_via_function_impl_value_source
