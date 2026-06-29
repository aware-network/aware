from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_plan import CodePackagePathRole

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code import Code


class CodePackageCode(ORMModel):
    # Relationships
    code: Code = Field(description="Association target reference to Code")

    # Attributes
    relative_path: str
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)

    # Foreign Keys
    code_package_id: UUID = Field(description="Join FK to CodePackage")
