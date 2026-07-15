from __future__ import annotations

# Standard
from enum import Enum


class AttributeTypeDescriptorKind(Enum):
    class_ = "class"
    collection = "collection"
    enum = "enum"
    mapping = "mapping"
    primitive = "primitive"
    tuple = "tuple"
    union = "union"


class AttributeTypeDescriptorRole(Enum):
    element = "element"
    key = "key"
    member = "member"
    value_ = "value"
