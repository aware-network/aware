from __future__ import annotations

# Standard
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
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.code.code_test_unit import CodeTestUnit


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

    @classmethod
    async def build_via_code_package_test_run(
        cls,
        code_package_test_run_id: UUID,
        code_test_unit_id: UUID,
        status: CodeTestRunStatus,
        selector: str,
        failures: JsonArray,
        duration_s: float | None = None,
        error: str | None = None,
    ) -> CodeTestUnitRun:
        """Build one canonical run receipt for a concrete CodeTestUnit."""

        payload = {
            "code_package_test_run_id": code_package_test_run_id,
            "code_test_unit_id": code_test_unit_id,
            "status": status,
            "selector": selector,
            "failures": failures,
            "duration_s": duration_s,
            "error": error,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_package_test_run", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeTestUnitRun):
            return value
        return CodeTestUnitRun.validate_invocation_value(value)


class CodeTestUnitRunBuildViaCodePackageTestRunInput(BaseModel):
    code_package_test_run_id: UUID = Field(description="Foreign key for CodePackageTestRun.unit_runs")
    code_test_unit_id: UUID
    status: CodeTestRunStatus
    selector: str
    failures: JsonArray
    duration_s: float | None = Field(default=None)
    error: str | None = Field(default=None)


class CodeTestUnitRunBuildViaCodePackageTestRunOutput(BaseModel):
    value: CodeTestUnitRun


FUNCTIONS = {
    "CodeTestUnitRun": {
        "build_via_code_package_test_run": {
            "canonical": {
                "name": "build_via_code_package_test_run",
                "description": "Build one canonical run receipt for a concrete CodeTestUnit.",
                "is_constructor": True,
            },
            "input": CodeTestUnitRunBuildViaCodePackageTestRunInput,
            "output": CodeTestUnitRunBuildViaCodePackageTestRunOutput,
        },
    },
}

__all__ = [
    "CodeTestUnitRun",
    "CodeTestUnitRunBuildViaCodePackageTestRunInput",
    "CodeTestUnitRunBuildViaCodePackageTestRunOutput",
    "FUNCTIONS",
]
