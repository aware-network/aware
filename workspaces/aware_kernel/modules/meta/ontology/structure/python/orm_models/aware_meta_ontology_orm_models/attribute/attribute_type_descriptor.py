from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology_orm_models.attribute.attribute_type_descriptor_enums import AttributeTypeDescriptorKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.attribute.attribute_type_descriptor_link import AttributeTypeDescriptorLink
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig
    from aware_meta_ontology_orm_models.enum.enum_config import EnumConfig
    from aware_meta_ontology_orm_models.primitive.primitive_config import PrimitiveConfig


class AttributeTypeDescriptor(ORMModel):
    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    enum_config: EnumConfig | None = Field(default=None)
    primitive_config: PrimitiveConfig | None = Field(default=None)
    child_links: list[AttributeTypeDescriptorLink] = Field(default_factory=list)

    # Attributes
    collection_kind: AttributeCollectionType = Field(default=AttributeCollectionType.single)
    kind: AttributeTypeDescriptorKind

    # Foreign Keys
    class_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeTypeDescriptor.class_config"
    )
    enum_config_id: UUID | None = Field(default=None, description="Foreign key for AttributeTypeDescriptor.enum_config")
    primitive_config_id: UUID | None = Field(
        default=None, description="Foreign key for AttributeTypeDescriptor.primitive_config"
    )
