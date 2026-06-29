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


class CodePrimitiveTypeElementType(BaseModel):
    """
    Edge linking a tuple-like CodePrimitiveType to its element types.
    Modeled as an explicit edge to support:
    - self-referential element lists without ambiguous FK names
    - sharing element nodes across multiple parents (M2M semantics)
    - stable ordering via `position`
    """

    # Relationships
    element_type: CodePrimitiveType = Field(description="Association target reference to CodePrimitiveType")

    # Attributes
    position: int
