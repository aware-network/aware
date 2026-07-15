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
    from aware_experience_ontology.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology.class_.class_config import ClassConfig


class ProgramImplInstructionIntentReceiptFieldBinding(ORMModel):
    """One prior action terminal receipt field projected into a continuation request."""

    # Relationships
    source_program_impl_instruction_intent: ProgramImplInstructionIntent | None = Field(default=None, exclude=True)
    source_receipt_class_config: ClassConfig | None = Field(default=None, exclude=True)
    source_receipt_attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    target_request_attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    required: bool = Field(default=True)
    position: int | None = Field(default=None)

    # Foreign Keys
    program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntent.receipt_field_bindings"
    )
    source_program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentReceiptFieldBinding.source_program_impl_instruction_intent"
    )
    source_receipt_class_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentReceiptFieldBinding.source_receipt_class_config"
    )
    source_receipt_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentReceiptFieldBinding.source_receipt_attribute_config"
    )
    target_request_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntentReceiptFieldBinding.target_request_attribute_config"
    )

    @classmethod
    async def build_via_program_impl_instruction_intent(
        cls,
        program_impl_instruction_intent_id: UUID,
        source_program_impl_instruction_intent_id: UUID,
        source_receipt_class_config_id: UUID,
        source_receipt_attribute_config_id: UUID,
        target_request_attribute_config_id: UUID,
        required: bool = True,
        position: int | None = None,
    ) -> ProgramImplInstructionIntentReceiptFieldBinding:
        """Create one deterministic terminal-receipt field edge under its target intent."""

        payload = {
            "program_impl_instruction_intent_id": program_impl_instruction_intent_id,
            "source_program_impl_instruction_intent_id": source_program_impl_instruction_intent_id,
            "source_receipt_class_config_id": source_receipt_class_config_id,
            "source_receipt_attribute_config_id": source_receipt_attribute_config_id,
            "target_request_attribute_config_id": target_request_attribute_config_id,
            "required": required,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction_intent", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionIntentReceiptFieldBinding):
            return value
        return ProgramImplInstructionIntentReceiptFieldBinding.validate_invocation_value(value)


class ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentInput(BaseModel):
    program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionIntent.receipt_field_bindings"
    )
    source_program_impl_instruction_intent_id: UUID
    source_receipt_class_config_id: UUID
    source_receipt_attribute_config_id: UUID
    target_request_attribute_config_id: UUID
    required: bool = Field(default=True)
    position: int | None = Field(default=None)


class ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentOutput(BaseModel):
    value: ProgramImplInstructionIntentReceiptFieldBinding


FUNCTIONS = {
    "ProgramImplInstructionIntentReceiptFieldBinding": {
        "build_via_program_impl_instruction_intent": {
            "canonical": {
                "name": "build_via_program_impl_instruction_intent",
                "description": "Create one deterministic terminal-receipt field edge under its target intent.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentInput,
            "output": ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionIntentReceiptFieldBinding",
    "ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentInput",
    "ProgramImplInstructionIntentReceiptFieldBindingBuildViaProgramImplInstructionIntentOutput",
    "FUNCTIONS",
]
