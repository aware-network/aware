from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology.function.code_section_function import CodeSectionFunction


class CodeSectionClassFunction(ORMModel):
    # Relationships
    code_section_function: CodeSectionFunction = Field(
        description="Association target reference to CodeSectionFunction"
    )

    # Attributes
    position: int = Field(default=0)

    # Foreign Keys
    code_section_function_id: UUID | None = Field(default=None, description="Join FK to CodeSectionFunction")
    code_section_class_id: UUID = Field(description="Join FK to CodeSectionClass")


FUNCTIONS = {
    "CodeSectionClassFunction": {},
}

__all__ = [
    "CodeSectionClassFunction",
    "FUNCTIONS",
]
