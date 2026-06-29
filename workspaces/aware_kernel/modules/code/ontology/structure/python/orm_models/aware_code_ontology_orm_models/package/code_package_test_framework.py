from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_test_framework import CodeTestFramework


class CodePackageTestFramework(ORMModel):
    """
    Package-level declaration edge for a test framework.
    Contract:
    - The framework object remains Code-owned and relational.
    - This edge records package declaration/provenance, not installation state.
    """

    # Relationships
    code_test_framework: CodeTestFramework | None = Field(
        default=None, description="Association target reference to CodeTestFramework"
    )

    # Attributes
    declaration_kind: str = Field(default="unknown")
    declaration_ref: str | None = Field(default=None)

    # Foreign Keys
    code_test_framework_id: UUID = Field(description="Join FK to CodeTestFramework")
    code_package_id: UUID = Field(description="Join FK to CodePackage")
