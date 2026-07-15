from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent import (
        ProgramImplInstructionIntent,
    )
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


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
