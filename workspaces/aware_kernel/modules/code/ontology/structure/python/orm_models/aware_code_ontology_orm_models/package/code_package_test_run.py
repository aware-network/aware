from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeTestRunStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code_test_unit_run import CodeTestUnitRun


class CodePackageTestRun(ORMModel):
    """
    Canonical run for one package-owned CodeTest surface.
    Contract:
    - CodePackageTest owns the run envelope.
    - Unit receipts compose through CodeTestUnitRun -> CodeTestUnit.
    - OIG commit ids are not attributes here; the commit envelope is emitted
    by the normal graph commit rail when this run graph is materialized.
    """

    # Relationships
    unit_runs: list[CodeTestUnitRun] = Field(default_factory=list)

    # Attributes
    run_key: str
    backend_kind: str
    status: CodeTestRunStatus
    started_at_utc: datetime | None = Field(default=None)
    finished_at_utc: datetime | None = Field(default=None)
    duration_s: float | None = Field(default=None)
    selected_unit_count: int = Field(default=0)
    total_tests: int = Field(default=0)
    passed_tests: int = Field(default=0)
    failed_tests: int = Field(default=0)
    skipped_tests: int = Field(default=0)
    unsupported_tests: int = Field(default=0)
    error: str | None = Field(default=None)

    # Foreign Keys
    code_package_test_id: UUID = Field(description="Foreign key for CodePackageTest.runs")
