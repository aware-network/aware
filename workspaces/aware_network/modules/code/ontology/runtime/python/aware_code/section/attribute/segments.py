from enum import Enum


# Segment names enum for type safety
class CodeSectionAttributeSegment(Enum):
    """Segment names for attribute sections."""

    NAME = "name"
    TYPE = "type"
    DEFAULT_VALUE = "default_value"
