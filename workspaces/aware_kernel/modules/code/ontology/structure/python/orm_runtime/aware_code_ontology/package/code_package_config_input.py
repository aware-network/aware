from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigInputKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class CodePackageConfigInput(ORMModel):
    # Attributes
    input_key: str
    kind: CodePackageConfigInputKind
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.inputs")

    @classmethod
    async def build_via_code_package_config(
        cls,
        code_package_config_id: UUID,
        input_key: str,
        kind: CodePackageConfigInputKind,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        package_family: str | None = None,
        semantic_kind: str | None = None,
        runtime_contract_version: str | None = None,
        required: bool = True,
    ) -> CodePackageConfigInput:
        """
        Create one CodePackageConfig-scoped materialization input contract row.

        Contract:
        - Parent CodePackageConfig context is propagated by constructor lowering.
        - This describes input shape only; Workspace owns selected revisions and execution receipts.
        """

        payload = {
            "code_package_config_id": code_package_config_id,
            "input_key": input_key,
            "kind": kind,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "package_family": package_family,
            "semantic_kind": semantic_kind,
            "runtime_contract_version": runtime_contract_version,
            "required": required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageConfigInput):
            return value
        return CodePackageConfigInput.validate_invocation_value(value)


class CodePackageConfigInputBuildViaCodePackageConfigInput(BaseModel):
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.inputs")
    input_key: str
    kind: CodePackageConfigInputKind
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)


class CodePackageConfigInputBuildViaCodePackageConfigOutput(BaseModel):
    value: CodePackageConfigInput


FUNCTIONS = {
    "CodePackageConfigInput": {
        "build_via_code_package_config": {
            "canonical": {
                "name": "build_via_code_package_config",
                "description": "Create one CodePackageConfig-scoped materialization input contract row.\n\nContract:\n- Parent CodePackageConfig context is propagated by constructor lowering.\n- This describes input shape only; Workspace owns selected revisions and execution receipts.",
                "is_constructor": True,
            },
            "input": CodePackageConfigInputBuildViaCodePackageConfigInput,
            "output": CodePackageConfigInputBuildViaCodePackageConfigOutput,
        },
    },
}

__all__ = [
    "CodePackageConfigInput",
    "CodePackageConfigInputBuildViaCodePackageConfigInput",
    "CodePackageConfigInputBuildViaCodePackageConfigOutput",
    "FUNCTIONS",
]
