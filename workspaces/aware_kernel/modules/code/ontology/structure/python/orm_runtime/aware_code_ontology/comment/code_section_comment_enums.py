from __future__ import annotations

# Standard
from enum import Enum


class CodeSectionCommentType(Enum):
    block = "block"
    doc = "doc"
    line = "line"
    metadata = "metadata"
