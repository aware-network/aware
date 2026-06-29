from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_test_framework import CodeTestFramework


class CodePackageTestFramework(BaseModel):
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
