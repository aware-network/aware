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
    from aware_code_ontology.code.code_section import CodeSection


class CodeTestUnit(ORMModel):
    """
    Runnable test unit resolved from CodeSection truth.
    Contract:
    - Identity is the target CodeSection under the parent CodeTest.
    - `selector` is execution/discovery payload, not file-path identity.
    """

    # Relationships
    code_section: CodeSection

    # Attributes
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)

    # Foreign Keys
    code_test_id: UUID = Field(description="Foreign key for CodeTest.units")
    code_section_id: UUID | None = Field(default=None, description="Foreign key for CodeTestUnit.code_section")

    @classmethod
    async def build_via_code_test(
        cls,
        code_test_id: UUID,
        code_section_id: UUID,
        unit_key: str,
        selector: str,
        kind: str = "function",
        name: str | None = None,
    ) -> CodeTestUnit:
        """Build one runnable test unit for a concrete CodeSection."""

        payload = {
            "code_test_id": code_test_id,
            "code_section_id": code_section_id,
            "unit_key": unit_key,
            "selector": selector,
            "kind": kind,
            "name": name,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_test", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeTestUnit):
            return value
        return CodeTestUnit.validate_invocation_value(value)


class CodeTestUnitBuildViaCodeTestInput(BaseModel):
    code_test_id: UUID = Field(description="Foreign key for CodeTest.units")
    code_section_id: UUID
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)


class CodeTestUnitBuildViaCodeTestOutput(BaseModel):
    value: CodeTestUnit


FUNCTIONS = {
    "CodeTestUnit": {
        "build_via_code_test": {
            "canonical": {
                "name": "build_via_code_test",
                "description": "Build one runnable test unit for a concrete CodeSection.",
                "is_constructor": True,
            },
            "input": CodeTestUnitBuildViaCodeTestInput,
            "output": CodeTestUnitBuildViaCodeTestOutput,
        },
    },
}

__all__ = [
    "CodeTestUnit",
    "CodeTestUnitBuildViaCodeTestInput",
    "CodeTestUnitBuildViaCodeTestOutput",
    "FUNCTIONS",
]
