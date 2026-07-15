from enum import Enum


# Segment names enum for type safety
class CodeSectionClassSegment(Enum):
    """Segment names for class sections."""

    NAME = "name"
    BASES = "bases"
    BODY = "body"
    DESCRIPTION_COMMENT = "description_comment"
    KEYWORD = "keyword"
    MODIFIERS = "modifiers"
