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
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class FunctionImplInstructionInvokeAttributeConfig(ORMModel):
    """Signature/value binding slot for `FunctionImplInstructionInvoke`."""

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)

    # Foreign Keys
    function_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvokeAttributeConfig.attribute_config"
    )

    @classmethod
    async def create_via_function_impl_instruction_invoke(
        cls,
        function_impl_instruction_invoke_id: UUID,
        attribute_config_id: UUID,
        value_expr: JsonObject,
        position: int | None = None,
    ) -> FunctionImplInstructionInvokeAttributeConfig:
        """Create deterministic invoke-argument binding under one invoke payload."""

        payload = {
            "function_impl_instruction_invoke_id": function_impl_instruction_invoke_id,
            "attribute_config_id": attribute_config_id,
            "value_expr": value_expr,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_function_impl_instruction_invoke", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionInvokeAttributeConfig):
            return value
        return FunctionImplInstructionInvokeAttributeConfig.validate_invocation_value(value)


class FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeInput(BaseModel):
    function_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID
    value_expr: JsonObject
    position: int | None = Field(default=None)


class FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeOutput(BaseModel):
    value: FunctionImplInstructionInvokeAttributeConfig


FUNCTIONS = {
    "FunctionImplInstructionInvokeAttributeConfig": {
        "create_via_function_impl_instruction_invoke": {
            "canonical": {
                "name": "create_via_function_impl_instruction_invoke",
                "description": "Create deterministic invoke-argument binding under one invoke payload.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeInput,
            "output": FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionInvokeAttributeConfig",
    "FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeInput",
    "FunctionImplInstructionInvokeAttributeConfigCreateViaFunctionImplInstructionInvokeOutput",
    "FUNCTIONS",
]
