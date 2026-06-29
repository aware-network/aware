from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.primitive.code_primitive_type import CodePrimitiveType


class CodePrimitiveTypeUnionType(BaseModel):
    """
    Edge linking a union-like CodePrimitiveType to its member types.
    Modeled as an explicit edge to support:
    - self-referential unions without ambiguous FK names
    - sharing member nodes across multiple parents (M2M semantics)
    - stable ordering for deterministic renders via `position` (optional)
    """

    # Relationships
    union_type: CodePrimitiveType = Field(description="Association target reference to CodePrimitiveType")

    # Attributes
    position: int
