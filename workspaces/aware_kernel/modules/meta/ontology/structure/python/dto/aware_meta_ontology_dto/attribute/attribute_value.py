from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_meta_ontology_dto.attribute.attribute_type_descriptor import AttributeTypeDescriptor
    from aware_meta_ontology_dto.attribute.attribute_value_change import AttributeValueChange
    from aware_meta_ontology_dto.attribute.attribute_value_link import AttributeValueLink
    from aware_meta_ontology_dto.class_.class_instance import ClassInstance
    from aware_meta_ontology_dto.class_.inline_value_instance import InlineValueInstance
    from aware_meta_ontology_dto.enum.enum_option import EnumOption


class AttributeValue(BaseModel):
    """
    Descriptor-driven value representation for Attributes.
    AttributeValue is a node in a value tree whose shape MUST match the
    AttributeTypeDescriptor tree referenced by `type_descriptor`.
    - Container nodes (COLLECTION/MAPPING/TUPLE/UNION) store no leaf payload and
    express structure via `child_links`.
    - Leaf nodes store exactly one payload kind (primitive_value / enum_option /
    class_instance / inline_value_instance) consistent with `type_descriptor.kind`.
    Canonical identity for children is expressed on the *link*:
    - LIST/TUPLE/UNION: `position` is the stable slot key.
    - SET/MAPPING: `identity_key` is the stable slot key (e.g., key fingerprint).
    """

    # Relationships
    attribute_value_changes: list[AttributeValueChange] = Field(default_factory=list)
    type_descriptor: AttributeTypeDescriptor | None = Field(default=None)
    child_links: list[AttributeValueLink] = Field(default_factory=list)
    enum_option: EnumOption | None = Field(default=None)
    class_instance: ClassInstance | None = Field(default=None)
    inline_value_instance: InlineValueInstance | None = Field(default=None)

    # Attributes
    primitive_value: JsonObject | None = Field(default=None)
