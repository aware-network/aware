from enum import Enum


class CodeSectionAnnotationSegment(Enum):
    """Segment names for annotation sections."""

    PATH = "path"
    VERB = "verb"
    ARGS = "args"
    RAW = "raw"
