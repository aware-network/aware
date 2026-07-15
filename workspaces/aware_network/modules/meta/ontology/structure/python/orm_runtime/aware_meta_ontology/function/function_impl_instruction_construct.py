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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig
    from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
        FunctionImplInstructionConstructAssignment,
    )


class FunctionImplInstructionConstruct(ORMModel):
    """
    Canonical explicit object-construction payload in function execution rail.
    Contract:
    - Represents direct object materialization intent (`construct ClassName(...)`).
    - Distinct from constructor invocation (`FunctionImplInstructionInvoke(kind=construct)`).
    """

    # Relationships
    target_class_config: ClassConfig | None = Field(default=None, exclude=True)
    assignments: list[FunctionImplInstructionConstructAssignment] = Field(default_factory=list)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_construct"
    )
    target_class_config_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionConstruct.target_class_config"
    )

    async def add_assignment(
        self, target_class_config_attribute_config_id: UUID, value_source_id: UUID, position: int | None = None
    ) -> FunctionImplInstructionConstructAssignment:
        """Attach one deterministic class-attribute assignment under this construct payload."""

        payload = {
            "target_class_config_attribute_config_id": target_class_config_attribute_config_id,
            "value_source_id": value_source_id,
            "position": position,
        }
        result = await invoke_instance(orm_model=self, function_name="add_assignment", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_construct_assignment import (
            FunctionImplInstructionConstructAssignment,
        )

        if isinstance(value, FunctionImplInstructionConstructAssignment):
            return value
        return FunctionImplInstructionConstructAssignment.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl_instruction(
        cls, function_impl_instruction_id: UUID, target_class_config_id: UUID
    ) -> FunctionImplInstructionConstruct:
        """
        Create deterministic explicit construct payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "function_impl_instruction_id": function_impl_instruction_id,
            "target_class_config_id": target_class_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionConstruct):
            return value
        return FunctionImplInstructionConstruct.validate_invocation_value(value)


class FunctionImplInstructionConstructAddAssignmentInput(BaseModel):
    target_class_config_attribute_config_id: UUID
    value_source_id: UUID
    position: int | None = Field(default=None)


class FunctionImplInstructionConstructAddAssignmentOutput(BaseModel):
    value: FunctionImplInstructionConstructAssignment


class FunctionImplInstructionConstructBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(
        description="Foreign key for FunctionImplInstruction.instruction_construct"
    )
    target_class_config_id: UUID


class FunctionImplInstructionConstructBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionConstruct


FUNCTIONS = {
    "FunctionImplInstructionConstruct": {
        "add_assignment": {
            "canonical": {
                "name": "add_assignment",
                "description": "Attach one deterministic class-attribute assignment under this construct payload.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionConstructAddAssignmentInput,
            "output": FunctionImplInstructionConstructAddAssignmentOutput,
        },
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic explicit construct payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionConstructBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionConstructBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionConstruct",
    "FunctionImplInstructionConstructAddAssignmentInput",
    "FunctionImplInstructionConstructAddAssignmentOutput",
    "FunctionImplInstructionConstructBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionConstructBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
