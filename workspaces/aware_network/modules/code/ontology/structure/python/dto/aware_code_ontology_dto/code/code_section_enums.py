from __future__ import annotations

# Standard
from enum import Enum


class CodeSectionType(Enum):
    binding = "binding"
    attribute = "attribute"
    class_ = "class"
    comment = "comment"
    decorator = "decorator"
    enum = "enum"
    enum_value = "enum_value"
    expression = "expression"
    function = "function"
    import_ = "import"
    mirror = "mirror"
    annotation = "annotation"
    projection = "projection"
