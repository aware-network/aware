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

if TYPE_CHECKING:
    from aware_code_ontology.code.code_test import CodeTest
    from aware_code_ontology.package.code_package_test_run import CodePackageTestRun


class CodePackageTest(ORMModel):
    """
    Package-level inventory object for one Code test surface.
    Contract:
    - CodePackageTest is a first-class object, not an association edge.
    - `code_test` is the direct target to Code-owned test identity.
    - Runs live only under this package-owned test surface.
    """

    # Relationships
    code_test: CodeTest
    runs: list[CodePackageTestRun] = Field(default_factory=list)

    # Attributes
    relative_path: str

    # Foreign Keys
    code_package_id: UUID = Field(description="Foreign key for CodePackage.tests")
    code_test_id: UUID | None = Field(default=None, description="Foreign key for CodePackageTest.code_test")

    async def create_run(
        self,
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
        """Create one canonical run envelope for this package-owned CodeTest."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="create_run", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_test_run import CodePackageTestRun

        if isinstance(value, CodePackageTestRun):
            return value
        return CodePackageTestRun.validate_invocation_value(value)

    @classmethod
    async def build_via_code_package(
        cls, code_package_id: UUID, code_test_id: UUID, relative_path: str
    ) -> CodePackageTest:
        """Attach an existing CodeTest under this CodePackage inventory."""

        payload = {"code_package_id": code_package_id, "code_test_id": code_test_id, "relative_path": relative_path}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageTest):
            return value
        return CodePackageTest.validate_invocation_value(value)


class CodePackageTestCreateRunInput(BaseModel):
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


class CodePackageTestCreateRunOutput(BaseModel):
    value: CodePackageTestRun


class CodePackageTestBuildViaCodePackageInput(BaseModel):
    code_package_id: UUID = Field(description="Foreign key for CodePackage.tests")
    code_test_id: UUID
    relative_path: str


class CodePackageTestBuildViaCodePackageOutput(BaseModel):
    value: CodePackageTest


FUNCTIONS = {
    "CodePackageTest": {
        "create_run": {
            "canonical": {
                "name": "create_run",
                "description": "Create one canonical run envelope for this package-owned CodeTest.",
                "is_constructor": False,
            },
            "input": CodePackageTestCreateRunInput,
            "output": CodePackageTestCreateRunOutput,
        },
        "build_via_code_package": {
            "canonical": {
                "name": "build_via_code_package",
                "description": "Attach an existing CodeTest under this CodePackage inventory.",
                "is_constructor": True,
            },
            "input": CodePackageTestBuildViaCodePackageInput,
            "output": CodePackageTestBuildViaCodePackageOutput,
        },
    },
}

__all__ = [
    "CodePackageTest",
    "CodePackageTestCreateRunInput",
    "CodePackageTestCreateRunOutput",
    "CodePackageTestBuildViaCodePackageInput",
    "CodePackageTestBuildViaCodePackageOutput",
    "FUNCTIONS",
]
