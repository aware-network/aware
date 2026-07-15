from __future__ import annotations

# Standard
from enum import Enum


class CodeSectionExpressionType(Enum):
    call = "call"
    identifier = "identifier"
    literal = "literal"
