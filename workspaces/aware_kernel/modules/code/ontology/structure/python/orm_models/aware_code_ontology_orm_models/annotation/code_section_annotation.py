from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection


class CodeSectionAnnotation(ORMModel):
    # Relationships
    code_section: CodeSection = Field(description="Reverse view for CodeSection.code_section_annotation")

    # Attributes
    path: str
    verb: str
    args: list[str] = Field(default_factory=list)

    # Foreign Keys
    code_section_id: UUID | None = Field(
        default=None, description="Foreign key for CodeSection.code_section_annotation"
    )
