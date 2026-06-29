from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology_dto.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
    from aware_meta_ontology_dto.class_.class_config import ClassConfig
    from aware_meta_ontology_dto.enum.enum_config import EnumConfig
    from aware_meta_ontology_dto.primitive.primitive_config import PrimitiveConfig


class AttributeTypeDescriptor(BaseModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None)
    enum_config: EnumConfig | None = Field(default=None)
    primitive_config: PrimitiveConfig | None = Field(default=None)
    child_links: list[AttributeTypeDescriptorLink] = Field(default_factory=list)

    # Attributes
    collection_kind: AttributeCollectionType = Field(default=AttributeCollectionType.single)
    kind: AttributeTypeDescriptorKind
