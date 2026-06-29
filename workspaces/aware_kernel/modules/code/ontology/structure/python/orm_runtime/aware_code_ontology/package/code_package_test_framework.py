from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.code.code_test_framework import CodeTestFramework


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

    @classmethod
    async def build_via_code_package(
        cls,
        code_package_id: UUID,
        code_test_framework_id: UUID,
        declaration_kind: str = "unknown",
        declaration_ref: str | None = None,
    ) -> CodePackageTestFramework:
        """Attach an existing CodeTestFramework under this CodePackage."""

        payload = {
            "code_package_id": code_package_id,
            "code_test_framework_id": code_test_framework_id,
            "declaration_kind": declaration_kind,
            "declaration_ref": declaration_ref,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageTestFramework):
            return value
        return CodePackageTestFramework.validate_invocation_value(value)


class CodePackageTestFrameworkBuildViaCodePackageInput(BaseModel):
    code_package_id: UUID = Field(description="Join FK to CodePackage")
    code_test_framework_id: UUID
    declaration_kind: str = Field(default="unknown")
    declaration_ref: str | None = Field(default=None)


class CodePackageTestFrameworkBuildViaCodePackageOutput(BaseModel):
    value: CodePackageTestFramework


FUNCTIONS = {
    "CodePackageTestFramework": {
        "build_via_code_package": {
            "canonical": {
                "name": "build_via_code_package",
                "description": "Attach an existing CodeTestFramework under this CodePackage.",
                "is_constructor": True,
            },
            "input": CodePackageTestFrameworkBuildViaCodePackageInput,
            "output": CodePackageTestFrameworkBuildViaCodePackageOutput,
        },
    },
}

__all__ = [
    "CodePackageTestFramework",
    "CodePackageTestFrameworkBuildViaCodePackageInput",
    "CodePackageTestFrameworkBuildViaCodePackageOutput",
    "FUNCTIONS",
]
