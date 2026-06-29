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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.code.code_test_framework import CodeTestFramework
    from aware_code_ontology.code.code_test_unit import CodeTestUnit


class CodeTest(ORMModel):
    """
    Canonical test surface for one Code object.
    Contract:
    - Code owns test surfaces.
    - Framework identity is relational, not enum-backed.
    - Runnable test units live below this surface and point at concrete
    CodeSection truth.
    """

    # Relationships
    framework: CodeTestFramework | None = Field(default=None)
    units: list[CodeTestUnit] = Field(default_factory=list)

    # Attributes
    discovery_kind: str
    selector_prefix: str | None = Field(default=None)

    # Foreign Keys
    code_id: UUID = Field(description="Foreign key for Code.tests")
    framework_id: UUID = Field(description="Foreign key for CodeTest.framework")

    async def create_unit(
        self, code_section_id: UUID, unit_key: str, selector: str, kind: str = "function", name: str | None = None
    ) -> CodeTestUnit:
        """Attach one runnable test unit to a concrete CodeSection."""

        payload = {
            "code_section_id": code_section_id,
            "unit_key": unit_key,
            "selector": selector,
            "kind": kind,
            "name": name,
        }
        result = await invoke_instance(orm_model=self, function_name="create_unit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_test_unit import CodeTestUnit

        if isinstance(value, CodeTestUnit):
            return value
        return CodeTestUnit.validate_invocation_value(value)

    @classmethod
    async def build_via_code(
        cls,
        code_id: UUID,
        framework_id: UUID,
        discovery_kind: str = "language_plugin",
        selector_prefix: str | None = None,
    ) -> CodeTest:
        """Build one framework-specific test surface under a Code object."""

        payload = {
            "code_id": code_id,
            "framework_id": framework_id,
            "discovery_kind": discovery_kind,
            "selector_prefix": selector_prefix,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeTest):
            return value
        return CodeTest.validate_invocation_value(value)


class CodeTestCreateUnitInput(BaseModel):
    code_section_id: UUID
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)


class CodeTestCreateUnitOutput(BaseModel):
    value: CodeTestUnit


class CodeTestBuildViaCodeInput(BaseModel):
    code_id: UUID = Field(description="Foreign key for Code.tests")
    framework_id: UUID
    discovery_kind: str = Field(default="language_plugin")
    selector_prefix: str | None = Field(default=None)


class CodeTestBuildViaCodeOutput(BaseModel):
    value: CodeTest


FUNCTIONS = {
    "CodeTest": {
        "create_unit": {
            "canonical": {
                "name": "create_unit",
                "description": "Attach one runnable test unit to a concrete CodeSection.",
                "is_constructor": False,
            },
            "input": CodeTestCreateUnitInput,
            "output": CodeTestCreateUnitOutput,
        },
        "build_via_code": {
            "canonical": {
                "name": "build_via_code",
                "description": "Build one framework-specific test surface under a Code object.",
                "is_constructor": True,
            },
            "input": CodeTestBuildViaCodeInput,
            "output": CodeTestBuildViaCodeOutput,
        },
    },
}

__all__ = [
    "CodeTest",
    "CodeTestCreateUnitInput",
    "CodeTestCreateUnitOutput",
    "CodeTestBuildViaCodeInput",
    "CodeTestBuildViaCodeOutput",
    "FUNCTIONS",
]
