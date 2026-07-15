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
    from aware_meta_ontology.class_.class_config_attribute_config import ClassConfigAttributeConfig
    from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionSet(ORMModel):
    """
    Deterministic mutation intent payload for function execution rail.
    Notes:
    - Grammar lowering for `set` is staged after this ontology contract.
    - Runtime must remain fail-closed until lowering/execution support is complete.
    """

    # Relationships
    target_class_config_attribute_config: ClassConfigAttributeConfig = Field(
        description="Canonical self-owned attribute declaration being mutated."
    )
    value_source: FunctionImplValueSource = Field(
        description="Deterministic assignment source (literal / function input ref / let ref)."
    )

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_set"
    )
    target_class_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionSet.target_class_config_attribute_config"
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionSet.value_source"
    )

    async def update_assignment(self, target_class_config_attribute_config_id: UUID, value_source_id: UUID) -> None:
        """
        Update the mutable assignment payload for an existing `set` instruction.

        Contract:
        - The FunctionImplInstructionSet identity is stable for the parent instruction.
        - The target attribute and value source must already exist as ontology truth.
        - The value source must belong to the same FunctionImplInstruction.
        """

        payload = {
            "target_class_config_attribute_config_id": target_class_config_attribute_config_id,
            "value_source_id": value_source_id,
        }
        await invoke_instance(orm_model=self, function_name="update_assignment", payload=payload)
        return None

    @classmethod
    async def build_via_function_impl_instruction(
        cls, function_impl_instruction_id: UUID, target_class_config_attribute_config_id: UUID, value_source_id: UUID
    ) -> FunctionImplInstructionSet:
        """
        Create deterministic `set` payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "function_impl_instruction_id": function_impl_instruction_id,
            "target_class_config_attribute_config_id": target_class_config_attribute_config_id,
            "value_source_id": value_source_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionSet):
            return value
        return FunctionImplInstructionSet.validate_invocation_value(value)


class FunctionImplInstructionSetUpdateAssignmentInput(BaseModel):
    target_class_config_attribute_config_id: UUID
    value_source_id: UUID


class FunctionImplInstructionSetUpdateAssignmentOutput(BaseModel):
    pass


class FunctionImplInstructionSetBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.instruction_set")
    target_class_config_attribute_config_id: UUID
    value_source_id: UUID


class FunctionImplInstructionSetBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionSet


FUNCTIONS = {
    "FunctionImplInstructionSet": {
        "update_assignment": {
            "canonical": {
                "name": "update_assignment",
                "description": "Update the mutable assignment payload for an existing `set` instruction.\n\nContract:\n- The FunctionImplInstructionSet identity is stable for the parent instruction.\n- The target attribute and value source must already exist as ontology truth.\n- The value source must belong to the same FunctionImplInstruction.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionSetUpdateAssignmentInput,
            "output": FunctionImplInstructionSetUpdateAssignmentOutput,
        },
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic `set` payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionSetBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionSetBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionSet",
    "FunctionImplInstructionSetUpdateAssignmentInput",
    "FunctionImplInstructionSetUpdateAssignmentOutput",
    "FunctionImplInstructionSetBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionSetBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
