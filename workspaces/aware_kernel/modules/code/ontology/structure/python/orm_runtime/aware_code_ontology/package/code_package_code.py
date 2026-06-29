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
from aware_code_ontology.code.code_plan import CodePackagePathRole

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.code.code import Code
    from aware_code_ontology.code.code_plan import CodeContentPlan
    from aware_code_ontology.code.code_plan import CodePackageDeltaProduction
    from aware_code_ontology.code.code_test_unit import CodeTestUnit


class CodePackageCode(ORMModel):
    # Relationships
    code: Code = Field(description="Association target reference to Code")

    # Attributes
    relative_path: str
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)

    # Foreign Keys
    code_package_id: UUID = Field(description="Join FK to CodePackage")

    async def sync_test_unit(
        self,
        framework_id: UUID,
        code_section_id: UUID,
        unit_key: str,
        selector: str,
        kind: str = "function",
        name: str | None = None,
        discovery_kind: str = "language_plugin",
        selector_prefix: str | None = None,
    ) -> CodeTestUnit:
        """Upsert one runnable Code test unit through the package-code bridge."""

        payload = {
            "framework_id": framework_id,
            "code_section_id": code_section_id,
            "unit_key": unit_key,
            "selector": selector,
            "kind": kind,
            "name": name,
            "discovery_kind": discovery_kind,
            "selector_prefix": selector_prefix,
        }
        result = await invoke_instance(orm_model=self, function_name="sync_test_unit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.code.code_test_unit import CodeTestUnit

        if isinstance(value, CodeTestUnit):
            return value
        return CodeTestUnit.validate_invocation_value(value)

    async def update_path_role(self, path_role: CodePackagePathRole) -> CodePackageCode:
        """Update this package-code edge path role through its own mutation boundary."""

        payload = {"path_role": path_role}
        result = await invoke_instance(orm_model=self, function_name="update_path_role", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)

    async def delete(self) -> None:
        """Delete this package-owned code attachment and its owned Code."""

        payload = {}
        await invoke_instance(orm_model=self, function_name="delete", payload=payload)
        return None

    @classmethod
    async def create_via_code_package(
        cls,
        code_package_id: UUID,
        relative_path: str,
        plan: CodeContentPlan,
        path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
        delta_production: CodePackageDeltaProduction | None = None,
    ) -> CodePackageCode:
        """Create a deterministic package-owned code attachment and owned Code from a canonical content plan."""

        payload = {
            "code_package_id": code_package_id,
            "relative_path": relative_path,
            "plan": plan,
            "path_role": path_role,
            "delta_production": delta_production,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageCode):
            return value
        return CodePackageCode.validate_invocation_value(value)


class CodePackageCodeSyncTestUnitInput(BaseModel):
    framework_id: UUID
    code_section_id: UUID
    unit_key: str
    selector: str
    kind: str = Field(default="function")
    name: str | None = Field(default=None)
    discovery_kind: str = Field(default="language_plugin")
    selector_prefix: str | None = Field(default=None)


class CodePackageCodeSyncTestUnitOutput(BaseModel):
    value: CodeTestUnit


class CodePackageCodeUpdatePathRoleInput(BaseModel):
    path_role: CodePackagePathRole


class CodePackageCodeUpdatePathRoleOutput(BaseModel):
    value: CodePackageCode


class CodePackageCodeDeleteInput(BaseModel):
    pass


class CodePackageCodeDeleteOutput(BaseModel):
    pass


class CodePackageCodeCreateViaCodePackageInput(BaseModel):
    code_package_id: UUID = Field(description="Join FK to CodePackage")
    relative_path: str
    plan: CodeContentPlan
    path_role: CodePackagePathRole = Field(default=CodePackagePathRole.authored_source)
    delta_production: CodePackageDeltaProduction | None = Field(default=None)


class CodePackageCodeCreateViaCodePackageOutput(BaseModel):
    value: CodePackageCode


FUNCTIONS = {
    "CodePackageCode": {
        "sync_test_unit": {
            "canonical": {
                "name": "sync_test_unit",
                "description": "Upsert one runnable Code test unit through the package-code bridge.",
                "is_constructor": False,
            },
            "input": CodePackageCodeSyncTestUnitInput,
            "output": CodePackageCodeSyncTestUnitOutput,
        },
        "update_path_role": {
            "canonical": {
                "name": "update_path_role",
                "description": "Update this package-code edge path role through its own mutation boundary.",
                "is_constructor": False,
            },
            "input": CodePackageCodeUpdatePathRoleInput,
            "output": CodePackageCodeUpdatePathRoleOutput,
        },
        "delete": {
            "canonical": {
                "name": "delete",
                "description": "Delete this package-owned code attachment and its owned Code.",
                "is_constructor": False,
            },
            "input": CodePackageCodeDeleteInput,
            "output": CodePackageCodeDeleteOutput,
        },
        "create_via_code_package": {
            "canonical": {
                "name": "create_via_code_package",
                "description": "Create a deterministic package-owned code attachment and owned Code from a canonical content plan.",
                "is_constructor": True,
            },
            "input": CodePackageCodeCreateViaCodePackageInput,
            "output": CodePackageCodeCreateViaCodePackageOutput,
        },
    },
}

__all__ = [
    "CodePackageCode",
    "CodePackageCodeSyncTestUnitInput",
    "CodePackageCodeSyncTestUnitOutput",
    "CodePackageCodeUpdatePathRoleInput",
    "CodePackageCodeUpdatePathRoleOutput",
    "CodePackageCodeDeleteInput",
    "CodePackageCodeDeleteOutput",
    "CodePackageCodeCreateViaCodePackageInput",
    "CodePackageCodeCreateViaCodePackageOutput",
    "FUNCTIONS",
]
