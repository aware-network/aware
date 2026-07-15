from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ProgramImplInstructionIntentReceiptFieldBinding(BaseModel):
    """One prior action terminal receipt field projected into a continuation request."""

    # Relationships
    source_program_impl_instruction_intent: ProgramImplInstructionIntent | None = Field(default=None)
    source_receipt_class_config: ClassConfig | None = Field(default=None)
    source_receipt_attribute_config: AttributeConfig | None = Field(default=None)
    target_request_attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    required: bool = Field(default=True)
    position: int | None = Field(default=None)
