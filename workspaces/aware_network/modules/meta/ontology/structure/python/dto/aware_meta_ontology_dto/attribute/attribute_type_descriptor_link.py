from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_type_descriptor import AttributeTypeDescriptor


class AttributeTypeDescriptorLink(BaseModel):
    # Relationships
    child: AttributeTypeDescriptor

    # Attributes
    role: AttributeTypeDescriptorRole
    position: int = Field(default=0)
