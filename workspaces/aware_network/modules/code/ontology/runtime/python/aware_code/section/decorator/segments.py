from enum import Enum


# Segment names enum for type safety
class CodeSectionDecoratorSegment(Enum):
    """Segment names for decorator sections."""

    NAME = "name"
    ARGUMENTS = "arguments"
