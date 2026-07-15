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
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config import ClassConfig


class ProgramImplInstructionIntentActivationFieldBinding(ORMModel):
    """One activation-input field projected into a continuation action request."""

    # Relationships
    source_class_config: ClassConfig | None = Field(default=None, exclude=True)
    source_attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    target_request_attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    source_input_key: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)

    # Foreign Keys
    program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntent.activation_field_bindings"
    )
    source_class_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentActivationFieldBinding.source_class_config"
    )
    source_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentActivationFieldBinding.source_attribute_config"
    )
    target_request_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentActivationFieldBinding.target_request_attribute_config"
    )

    @classmethod
    async def build_via_program_impl_instruction_intent(
        cls,
        program_impl_instruction_intent_id: UUID,
        source_class_config_id: UUID,
        source_attribute_config_id: UUID,
        target_request_attribute_config_id: UUID,
        source_input_key: str,
        required: bool = True,
        position: int | None = None,
    ) -> ProgramImplInstructionIntentActivationFieldBinding:
        """Create one deterministic activation field edge under its target intent."""

        payload = {
            "program_impl_instruction_intent_id": program_impl_instruction_intent_id,
            "source_class_config_id": source_class_config_id,
            "source_attribute_config_id": source_attribute_config_id,
            "target_request_attribute_config_id": target_request_attribute_config_id,
            "source_input_key": source_input_key,
            "required": required,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction_intent", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionIntentActivationFieldBinding):
            return value
        return ProgramImplInstructionIntentActivationFieldBinding.validate_invocation_value(value)


class ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentInput(BaseModel):
    program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntent.activation_field_bindings"
    )
    source_class_config_id: UUID
    source_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    source_input_key: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentOutput(BaseModel):
    value: ProgramImplInstructionIntentActivationFieldBinding


FUNCTIONS = {
    "ProgramImplInstructionIntentActivationFieldBinding": {
        "build_via_program_impl_instruction_intent": {
            "canonical": {
                "name": "build_via_program_impl_instruction_intent",
                "description": "Create one deterministic activation field edge under its target intent.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentInput,
            "output": ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionIntentActivationFieldBinding",
    "ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentInput",
    "ProgramImplInstructionIntentActivationFieldBindingBuildViaProgramImplInstructionIntentOutput",
    "FUNCTIONS",
]
