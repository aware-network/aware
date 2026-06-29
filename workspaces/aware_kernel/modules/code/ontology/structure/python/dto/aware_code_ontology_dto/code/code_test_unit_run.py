from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeTestRunStatus

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_test_unit import CodeTestUnit


class CodeTestUnitRun(BaseModel):
    """
    Canonical execution receipt for one CodeTestUnit.
    Contract:
    - The identity points to a concrete CodeTestUnit, not a file path.
    - Parent CodePackageTestRun provides the execution/run envelope.
    - Failure payload stays descriptive; test identity remains relational.
    """

    # Relationships
    code_test_unit: CodeTestUnit

    # Attributes
    status: CodeTestRunStatus
    selector: str
    duration_s: float | None = Field(default=None)
    failures: JsonArray = Field(default_factory=JsonArray)
    error: str | None = Field(default=None)
