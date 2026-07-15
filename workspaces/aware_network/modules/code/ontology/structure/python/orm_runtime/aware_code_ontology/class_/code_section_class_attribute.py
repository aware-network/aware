from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology.attribute.code_section_attribute import CodeSectionAttribute


class CodeSectionClassAttribute(ORMModel):
    # Relationships
    code_section_attribute: CodeSectionAttribute = Field(
        description="Association target reference to CodeSectionAttribute"
    )

    # Attributes
    position: int = Field(default=0)

    # Foreign Keys
    code_section_attribute_id: UUID | None = Field(default=None, description="Join FK to CodeSectionAttribute")
    code_section_class_id: UUID = Field(description="Join FK to CodeSectionClass")


FUNCTIONS = {
    "CodeSectionClassAttribute": {},
}

__all__ = [
    "CodeSectionClassAttribute",
    "FUNCTIONS",
]
