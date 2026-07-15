from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_type_descriptor import AttributeTypeDescriptor


class AttributeTypeDescriptorLink(ORMModel):
    # Relationships
    child: AttributeTypeDescriptor

    # Attributes
    role: AttributeTypeDescriptorRole
    position: int = Field(default=0)

    # Foreign Keys
    attribute_type_descriptor_id: UUID = Field(description="Foreign key for AttributeTypeDescriptor.child_links")
    child_id: UUID | None = Field(default=None, description="Foreign key for AttributeTypeDescriptorLink.child")
