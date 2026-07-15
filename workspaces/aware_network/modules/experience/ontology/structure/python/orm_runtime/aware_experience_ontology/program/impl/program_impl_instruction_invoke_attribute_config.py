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


class ProgramImplInstructionInvokeAttributeConfig(ORMModel):
    """
    Signature/value binding slot for ProgramImplInstructionInvoke.
    Contract:
    - Keeps invoke argument lowering explicit and deterministic.
    - Association identity is deterministic from `(invoke_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    value_expr: JsonObject
    position: int | None = Field(default=None)

    # Foreign Keys
    program_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvokeAttributeConfig.attribute_config"
    )

    @classmethod
    async def build_via_program_impl_instruction_invoke(
        cls,
        program_impl_instruction_invoke_id: UUID,
        attribute_config_id: UUID,
        value_expr: JsonObject,
        position: int | None = None,
    ) -> ProgramImplInstructionInvokeAttributeConfig:
        """Create deterministic invoke argument association for one ProgramImplInstructionInvoke."""

        payload = {
            "program_impl_instruction_invoke_id": program_impl_instruction_invoke_id,
            "attribute_config_id": attribute_config_id,
            "value_expr": value_expr,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction_invoke", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionInvokeAttributeConfig):
            return value
        return ProgramImplInstructionInvokeAttributeConfig.validate_invocation_value(value)


class ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeInput(BaseModel):
    program_impl_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInvoke.attribute_configs"
    )
    attribute_config_id: UUID
    value_expr: JsonObject
    position: int | None = Field(default=None)


class ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeOutput(BaseModel):
    value: ProgramImplInstructionInvokeAttributeConfig


FUNCTIONS = {
    "ProgramImplInstructionInvokeAttributeConfig": {
        "build_via_program_impl_instruction_invoke": {
            "canonical": {
                "name": "build_via_program_impl_instruction_invoke",
                "description": "Create deterministic invoke argument association for one ProgramImplInstructionInvoke.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeInput,
            "output": ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionInvokeAttributeConfig",
    "ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeInput",
    "ProgramImplInstructionInvokeAttributeConfigBuildViaProgramImplInstructionInvokeOutput",
    "FUNCTIONS",
]
