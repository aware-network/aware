from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeTestRunStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun


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

    async def create_unit_run(
        self,
        code_test_unit_id: UUID,
        status: CodeTestRunStatus,
        selector: str,
        failures: JsonArray,
        duration_s: float | None = None,
        error: str | None = None,
    ) -> CodeTestUnitRun:
        """Attach one canonical unit run receipt to this package test run."""

        payload = {
            "code_test_unit_id": code_test_unit_id,
            "status": status,
            "selector": selector,
            "failures": failures,
            "duration_s": duration_s,
            "error": error,
        }
        result = await invoke_instance(orm_model=self, function_name="create_unit_run", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun

        if isinstance(value, CodeTestUnitRun):
            return value
        return CodeTestUnitRun.validate_invocation_value(value)

    @classmethod
    async def build_via_code_package_test(
        cls,
        code_package_test_id: UUID,
        run_key: str,
        backend_kind: str,
        status: CodeTestRunStatus,
        started_at_utc: datetime | None = None,
        finished_at_utc: datetime | None = None,
        duration_s: float | None = None,
        selected_unit_count: int = 0,
        total_tests: int = 0,
        passed_tests: int = 0,
        failed_tests: int = 0,
        skipped_tests: int = 0,
        unsupported_tests: int = 0,
        error: str | None = None,
    ) -> CodePackageTestRun:
        """Build one canonical run envelope for a package-owned CodeTest."""

        payload = {
            "code_package_test_id": code_package_test_id,
            "run_key": run_key,
            "backend_kind": backend_kind,
            "status": status,
            "started_at_utc": started_at_utc,
            "finished_at_utc": finished_at_utc,
            "duration_s": duration_s,
            "selected_unit_count": selected_unit_count,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "unsupported_tests": unsupported_tests,
            "error": error,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package_test", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageTestRun):
            return value
        return CodePackageTestRun.validate_invocation_value(value)


class CodePackageTestRunCreateUnitRunInput(BaseModel):
    code_test_unit_id: UUID
    status: CodeTestRunStatus
    selector: str
    failures: JsonArray
    duration_s: float | None = Field(default=None)
    error: str | None = Field(default=None)


class CodePackageTestRunCreateUnitRunOutput(BaseModel):
    value: CodeTestUnitRun


class CodePackageTestRunBuildViaCodePackageTestInput(BaseModel):
    code_package_test_id: UUID = Field(description="Foreign key for CodePackageTest.runs")
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


class CodePackageTestRunBuildViaCodePackageTestOutput(BaseModel):
    value: CodePackageTestRun


FUNCTIONS = {
    "CodePackageTestRun": {
        "create_unit_run": {
            "canonical": {
                "name": "create_unit_run",
                "description": "Attach one canonical unit run receipt to this package test run.",
                "is_constructor": False,
            },
            "input": CodePackageTestRunCreateUnitRunInput,
            "output": CodePackageTestRunCreateUnitRunOutput,
        },
        "build_via_code_package_test": {
            "canonical": {
                "name": "build_via_code_package_test",
                "description": "Build one canonical run envelope for a package-owned CodeTest.",
                "is_constructor": True,
            },
            "input": CodePackageTestRunBuildViaCodePackageTestInput,
            "output": CodePackageTestRunBuildViaCodePackageTestOutput,
        },
    },
}

__all__ = [
    "CodePackageTestRun",
    "CodePackageTestRunCreateUnitRunInput",
    "CodePackageTestRunCreateUnitRunOutput",
    "CodePackageTestRunBuildViaCodePackageTestInput",
    "CodePackageTestRunBuildViaCodePackageTestOutput",
    "FUNCTIONS",
]
