from enum import Enum


# Segment names enum for type safety
class CodeSectionFunctionSegment(Enum):
    """Segment names for function sections."""

    NAME = "name"
    SIGNATURE = "signature"
    RETURN_TYPE = "return_type"
    BODY = "body"
    IS_ASYNC = "is_async"
    DESCRIPTION_COMMENT = "description_comment"
