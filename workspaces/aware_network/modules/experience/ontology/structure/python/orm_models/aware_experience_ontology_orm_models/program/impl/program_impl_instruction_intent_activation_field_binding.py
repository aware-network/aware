from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


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
