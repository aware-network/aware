from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeTestRunStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_test_unit import CodeTestUnit


class CodeTestUnitRun(ORMModel):
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

    # Foreign Keys
    code_package_test_run_id: UUID = Field(description="Foreign key for CodePackageTestRun.unit_runs")
    code_test_unit_id: UUID | None = Field(default=None, description="Foreign key for CodeTestUnitRun.code_test_unit")
