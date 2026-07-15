from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.code.code_test import CodeTest
    from aware_content_ontology_orm_models.part.content_part_text import ContentPartText


class Code(ORMModel):
    # Relationships
    code_sections: list[CodeSection] = Field(default_factory=list, exclude=True)
    content_part_text: ContentPartText
    tests: list[CodeTest] = Field(default_factory=list)

    # Attributes
    relative_path: str
    language: CodeLanguage | None = Field(default=None)

    # Foreign Keys
    content_part_text_id: UUID | None = Field(default=None, description="Foreign key for Code.content_part_text")
    code_package_code_id: UUID = Field(description="Propagation FK to CodePackageCode")
