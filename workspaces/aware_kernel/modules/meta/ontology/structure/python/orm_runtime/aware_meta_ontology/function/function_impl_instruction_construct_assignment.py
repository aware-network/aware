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

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionConstructAssignment(ORMModel):
    """Deterministic target/value assignment for explicit object-construction payloads."""

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig
    value_source: FunctionImplValueSource

    # Attributes
    position: int | None = Field(default=None)

    # Foreign Keys
    function_impl_instruction_construct_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionConstruct.assignments"
    )
    target_class_config_attribute_config_id: UUID | None = Field(
        default=None,
        description="Foreign key for FunctionImplInstructionConstructAssignment.target_class_config_attribute_config",
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionConstructAssignment.value_source"
    )

    @classmethod
    async def build_via_function_impl_instruction_construct(
        cls,
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

        payload = {
            "function_impl_instruction_construct_id": function_impl_instruction_construct_id,
            "target_class_config_attribute_config_id": target_class_config_attribute_config_id,
            "value_source_id": value_source_id,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction_construct", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionConstructAssignment):
            return value
        return FunctionImplInstructionConstructAssignment.validate_invocation_value(value)


class FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructInput(BaseModel):
    function_impl_instruction_construct_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionConstruct.assignments"
    )
    target_class_config_attribute_config_id: UUID
    value_source_id: UUID
    position: int | None = Field(default=None)


class FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructOutput(BaseModel):
    value: FunctionImplInstructionConstructAssignment


FUNCTIONS = {
    "FunctionImplInstructionConstructAssignment": {
        "build_via_function_impl_instruction_construct": {
            "canonical": {
                "name": "build_via_function_impl_instruction_construct",
                "description": "Create deterministic construct assignment under one FunctionImplInstructionConstruct.\n\nContract:\n- Parent context (`function_impl_instruction_construct_id`) is injected by parent-edge lowering.\n- Constructor identity keys are `(target_class_config_attribute_config_id, value_source_id)` plus parent scope.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructInput,
            "output": FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionConstructAssignment",
    "FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructInput",
    "FunctionImplInstructionConstructAssignmentBuildViaFunctionImplInstructionConstructOutput",
    "FUNCTIONS",
]
