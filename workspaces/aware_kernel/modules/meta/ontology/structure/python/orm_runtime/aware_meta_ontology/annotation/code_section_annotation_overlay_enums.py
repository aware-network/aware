from __future__ import annotations

# Standard
from enum import Enum


class CodeSectionAnnotationOverlayEntity(Enum):
    class_ = "class"
    enum = "enum"
    enum_option = "enum_option"
    attribute = "attribute"
    function = "function"
