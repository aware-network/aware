from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import Json

if TYPE_CHECKING:
    from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


class FunctionImplValueSourceLiteralPrimitive(ORMModel):
    """
    Deterministic typed primitive literal payload for function value sources.
    Contract:
    - Literal identity is anchored by `primitive_config`.
    - `value` must be compatible with the selected primitive type.
    """

    # Relationships
    primitive_config: PrimitiveConfig

    # Attributes
    value: Json

    # Foreign Keys
    function_impl_value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_literal_primitive"
    )
    primitive_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceLiteralPrimitive.primitive_config"
    )

    @classmethod
    async def build_via_function_impl_value_source(
        cls, function_impl_value_source_id: UUID, primitive_config_id: UUID, value: Json
    ) -> FunctionImplValueSourceLiteralPrimitive:
        """Create deterministic primitive literal payload under one FunctionImplValueSource."""

        payload = {
            "function_impl_value_source_id": function_impl_value_source_id,
            "primitive_config_id": primitive_config_id,
            "value": value,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_value_source", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSourceLiteralPrimitive):
            return value
        return FunctionImplValueSourceLiteralPrimitive.validate_invocation_value(value)


class FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceInput(BaseModel):
    function_impl_value_source_id: UUID = Field(
        description="Foreign key for FunctionImplValueSource.source_literal_primitive"
    )
    primitive_config_id: UUID
    value: Json


class FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceOutput(BaseModel):
    value: FunctionImplValueSourceLiteralPrimitive


FUNCTIONS = {
    "FunctionImplValueSourceLiteralPrimitive": {
        "build_via_function_impl_value_source": {
            "canonical": {
                "name": "build_via_function_impl_value_source",
                "description": "Create deterministic primitive literal payload under one FunctionImplValueSource.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceInput,
            "output": FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSourceLiteralPrimitive",
    "FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceInput",
    "FunctionImplValueSourceLiteralPrimitiveBuildViaFunctionImplValueSourceOutput",
    "FUNCTIONS",
]
