from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OcgDescriptorSpec(BaseModel):
    """OIG narration descriptor bundle derived from canonical OCG metadata.

    This is a read-side descriptor IR for change narration. It is not an
    Environment manifest producer; callers should populate it from Meta/Ontology
    runtime artifacts or service replica state.
    """

    classes: list[OcgClassDescriptorSpec] = Field(default_factory=list)


class OcgEnumDescriptorSpec(BaseModel):
    """Description of an enum referenced by an OIG attribute type."""

    enum_config_id: UUID
    name: str
    description: str | None = Field(default=None)
    options: list[OcgEnumOptionDescriptorSpec] = Field(default_factory=list)


class OcgEnumOptionDescriptorSpec(BaseModel):
    """Description of one enum option referenced by an OIG attribute value."""

    enum_option_id: UUID
    label: str | None = Field(default=None)
    value: str


class OcgClassDescriptorSpec(BaseModel):
    """Description of a class and its attributes/functions for OIG narration."""

    class_config_id: UUID
    name: str
    is_base: bool
    attributes: list[OcgAttributeDescriptorSpec] = Field(default_factory=list)
    functions: list[OcgFunctionDescriptorSpec] = Field(default_factory=list)


class OcgFunctionDescriptorSpec(BaseModel):
    """Description of a function attached to an OIG class descriptor."""

    function_config_id: UUID
    name: str
    description: str = ""
    is_constructor: bool
    inputs: list[OcgAttributeDescriptorSpec] = Field(default_factory=list)
    returns: list[OcgAttributeDescriptorSpec] = Field(default_factory=list)


class OcgAttributeDescriptorSpec(BaseModel):
    """Description of an attribute and its type for OIG narration."""

    attribute_config_id: UUID
    name: str
    required: bool
    type_descriptor: OcgAttributeTypeDescriptorSpec


class OcgAttributeTypeDescriptorKind(Enum):
    """Kind for an OIG narration type descriptor node."""

    PRIMITIVE = "primitive"
    ENUM = "enum"
    CLASS = "class"
    COLLECTION = "collection"
    MAPPING = "mapping"
    TUPLE = "tuple"
    UNION = "union"


class OcgAttributeTypeDescriptorRole(str, Enum):
    """Composition role for a nested OIG narration type descriptor."""

    ELEMENT = "element"
    KEY = "key"
    VALUE = "value"
    MEMBER = "member"


class OcgCollectionType(str, Enum):
    SINGLE = "single"
    LIST = "list"
    SET = "set"


class OcgAttributeTypeDescriptorSpec(BaseModel):
    """Hierarchical type descriptor node for OCG attribute descriptor types."""

    attribute_type_descriptor_id: UUID
    kind: OcgAttributeTypeDescriptorKind
    collection_kind: OcgCollectionType | None = Field(default=None)
    class_config_id: UUID | None = Field(default=None)
    class_name: str | None = Field(default=None)
    primitive_spec: OcgPrimitiveDescriptorSpec | None = Field(default=None)
    enum_spec: OcgEnumDescriptorSpec | None = Field(default=None)
    attribute_type_descriptor_link_child_list: list[OcgAttributeTypeDescriptorLinkSpec] = Field(
        default_factory=list
    )
    is_nullable: bool = Field(default=False)


class OcgAttributeTypeDescriptorLinkSpec(BaseModel):
    """Parent-child composition link between OIG narration type descriptors."""

    attribute_type_descriptor_link_id: UUID
    role: OcgAttributeTypeDescriptorRole
    position: int | None = Field(default=None)
    parent_id: UUID
    child_id: UUID | None = Field(default=None)
    child: OcgAttributeTypeDescriptorSpec


class OcgPrimitiveDescriptorSpec(BaseModel):
    """Description of a primitive type referenced by an attribute descriptor."""

    primitive_config_id: UUID
    primitive_type: OcgCodePrimitiveType


class OcgCodePrimitiveType(BaseModel):
    """Primitive/container type descriptor for OIG narration."""

    base_type: OcgBaseType
    item_type: OcgCodePrimitiveType | None = None
    key_type: OcgCodePrimitiveType | None = None
    value_type: OcgCodePrimitiveType | None = None
    element_types: list[OcgCodePrimitiveType] | None = None
    union_types: list[OcgCodePrimitiveType] | None = None
    constraints: dict[str, Any] | None = None


class OcgBaseType(str, Enum):
    """Base type categories used by OIG narration."""

    BOOLEAN = "boolean"
    BYTES = "bytes"
    DATETIME = "datetime"
    FLOAT = "float"
    INTEGER = "integer"
    STRING = "string"
    UUID = "uuid"
    VECTOR = "vector"
    ARRAY = "array"
    DICT = "dict"
    TUPLE = "tuple"
    SET = "set"
    JSON = "json"
    ANY = "any"
    NULL = "null"
    UNION = "union"


__all__ = [
    "OcgAttributeDescriptorSpec",
    "OcgAttributeTypeDescriptorKind",
    "OcgAttributeTypeDescriptorLinkSpec",
    "OcgAttributeTypeDescriptorRole",
    "OcgAttributeTypeDescriptorSpec",
    "OcgBaseType",
    "OcgClassDescriptorSpec",
    "OcgCodePrimitiveType",
    "OcgCollectionType",
    "OcgDescriptorSpec",
    "OcgEnumDescriptorSpec",
    "OcgEnumOptionDescriptorSpec",
    "OcgFunctionDescriptorSpec",
    "OcgPrimitiveDescriptorSpec",
]
