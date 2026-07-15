from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_config import AttributeConfig
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class ProgramImplInstructionIntentActivationFieldBinding(BaseModel):
    """One activation-input field projected into a continuation action request."""

    # Relationships
    source_class_config: ClassConfig | None = Field(default=None)
    source_attribute_config: AttributeConfig | None = Field(default=None)
    target_request_attribute_config: AttributeConfig | None = Field(default=None)

    # Attributes
    source_input_key: str
    required: bool = Field(default=True)
    position: int | None = Field(default=None)
