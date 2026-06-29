from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_plan import CodePackagePathRole

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code import Code


class CodePackageCode(BaseModel):
    # Relationships
    code: Code = Field(description="Association target reference to Code")

    # Attributes
    relative_path: str
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
