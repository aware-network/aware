from __future__ import annotations

# Standard
from enum import Enum


class CodeSectionAnnotationOneOfMode(Enum):
    # Oneof is a payload validation rail (renderer/runtime validation semantics).
    validation = "validation"
    # Oneof is an identity rail (stable-id polymorphic key resolution semantics).
    identity = "identity"
