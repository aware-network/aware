from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeTestRunStatus

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code_test_unit_run import CodeTestUnitRun


class CodePackageTestRun(BaseModel):
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
