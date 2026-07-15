from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigRuntimeContextKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class CodePackageConfigRuntimeContext(ORMModel):
    # Attributes
    context_key: str
    kind: CodePackageConfigRuntimeContextKind
    package_name: str | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.runtime_contexts")

    @classmethod
    async def build_via_code_package_config(
        cls,
        code_package_config_id: UUID,
        context_key: str,
        kind: CodePackageConfigRuntimeContextKind,
        package_name: str | None = None,
        projection_name: str | None = None,
        runtime_contract_version: str | None = None,
        required: bool = True,
    ) -> CodePackageConfigRuntimeContext:
        """
        Create one CodePackageConfig-scoped runtime context contract row.

        Contract:
        - Parent CodePackageConfig context is propagated by constructor lowering.
        - This records runtime context shape; provider routing and deployment lifecycle stay outside Code.
        """

        payload = {
            "code_package_config_id": code_package_config_id,
            "context_key": context_key,
            "kind": kind,
            "package_name": package_name,
            "projection_name": projection_name,
            "runtime_contract_version": runtime_contract_version,
            "required": required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageConfigRuntimeContext):
            return value
        return CodePackageConfigRuntimeContext.validate_invocation_value(value)


class CodePackageConfigRuntimeContextBuildViaCodePackageConfigInput(BaseModel):
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.runtime_contexts")
    context_key: str
    kind: CodePackageConfigRuntimeContextKind
    package_name: str | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)


class CodePackageConfigRuntimeContextBuildViaCodePackageConfigOutput(BaseModel):
    value: CodePackageConfigRuntimeContext


FUNCTIONS = {
    "CodePackageConfigRuntimeContext": {
        "build_via_code_package_config": {
            "canonical": {
                "name": "build_via_code_package_config",
                "description": "Create one CodePackageConfig-scoped runtime context contract row.\n\nContract:\n- Parent CodePackageConfig context is propagated by constructor lowering.\n- This records runtime context shape; provider routing and deployment lifecycle stay outside Code.",
                "is_constructor": True,
            },
            "input": CodePackageConfigRuntimeContextBuildViaCodePackageConfigInput,
            "output": CodePackageConfigRuntimeContextBuildViaCodePackageConfigOutput,
        },
    },
}

__all__ = [
    "CodePackageConfigRuntimeContext",
    "CodePackageConfigRuntimeContextBuildViaCodePackageConfigInput",
    "CodePackageConfigRuntimeContextBuildViaCodePackageConfigOutput",
    "FUNCTIONS",
]
