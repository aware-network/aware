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
    from aware_code_ontology.module.code_module import CodeModule


class CodeModuleDependence(ORMModel):
    # Relationships
    dependence: CodeModule | None = Field(default=None)

    # Attributes
    name: str

    # Foreign Keys
    code_module_id: UUID = Field(description="Foreign key for CodeModule.dependences")
    dependence_id: UUID = Field(description="Foreign key for CodeModuleDependence.dependence")

    @classmethod
    async def build_via_code_module(cls, code_module_id: UUID, name: str) -> CodeModuleDependence:
        """
        Create a deterministic dependency association under one CodeModule.

        Contract:
        - Parent CodeModule scope is injected by propagation.
        - Target CodeModule identity is resolved by `CodeModule.build(name)`.
        """

        payload = {"code_module_id": code_module_id, "name": name}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_module", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeModuleDependence):
            return value
        return CodeModuleDependence.validate_invocation_value(value)


class CodeModuleDependenceBuildViaCodeModuleInput(BaseModel):
    code_module_id: UUID = Field(description="Foreign key for CodeModule.dependences")
    name: str


class CodeModuleDependenceBuildViaCodeModuleOutput(BaseModel):
    value: CodeModuleDependence


FUNCTIONS = {
    "CodeModuleDependence": {
        "build_via_code_module": {
            "canonical": {
                "name": "build_via_code_module",
                "description": "Create a deterministic dependency association under one CodeModule.\n\nContract:\n- Parent CodeModule scope is injected by propagation.\n- Target CodeModule identity is resolved by `CodeModule.build(name)`.",
                "is_constructor": True,
            },
            "input": CodeModuleDependenceBuildViaCodeModuleInput,
            "output": CodeModuleDependenceBuildViaCodeModuleOutput,
        },
    },
}

__all__ = [
    "CodeModuleDependence",
    "CodeModuleDependenceBuildViaCodeModuleInput",
    "CodeModuleDependenceBuildViaCodeModuleOutput",
    "FUNCTIONS",
]
