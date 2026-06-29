from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.primitive.code_primitive_type import CodePrimitiveType


class CodePrimitiveTypeUnionType(ORMModel):
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

    # Foreign Keys
    union_type_id: UUID | None = Field(default=None, description="Join FK to CodePrimitiveType")
    code_primitive_type_id: UUID = Field(description="Join FK to CodePrimitiveType")
