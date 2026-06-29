from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.package.code_package_enums import CodePackageConfigOutputKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class CodePackageConfigOutput(ORMModel):
    # Attributes
    output_key: str
    kind: CodePackageConfigOutputKind
    producer_key: str | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_output_key: str | None = Field(default=None)
    target_provider_key: str | None = Field(default=None)
    target_input_key: str | None = Field(default=None)
    target_semantic_owner: str | None = Field(default=None)
    target_package_family: str | None = Field(default=None)
    target_semantic_kind: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)

    # Foreign Keys
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.outputs")

    @classmethod
    async def build_via_code_package_config(
        cls,
        code_package_config_id: UUID,
        output_key: str,
        kind: CodePackageConfigOutputKind,
        producer_key: str | None = None,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        package_output_key: str | None = None,
        target_provider_key: str | None = None,
        target_input_key: str | None = None,
        target_semantic_owner: str | None = None,
        target_package_family: str | None = None,
        target_semantic_kind: str | None = None,
        media_type: str | None = None,
        runtime_contract_version: str | None = None,
        required_for: list[str] = [],
        required: bool = True,
    ) -> CodePackageConfigOutput:
        """
        Create one CodePackageConfig-scoped materialization output contract row.

        Contract:
        - Parent CodePackageConfig context is propagated by constructor lowering.
        - This describes declared outputs only.
        - CodePackageArtifact owns package output evidence emitted for a concrete CodePackage.
        - Workspace owns revision pins, materialization envelopes, and publication envelopes.
        """

        payload = {
            "code_package_config_id": code_package_config_id,
            "output_key": output_key,
            "kind": kind,
            "producer_key": producer_key,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "package_output_key": package_output_key,
            "target_provider_key": target_provider_key,
            "target_input_key": target_input_key,
            "target_semantic_owner": target_semantic_owner,
            "target_package_family": target_package_family,
            "target_semantic_kind": target_semantic_kind,
            "media_type": media_type,
            "runtime_contract_version": runtime_contract_version,
            "required_for": required_for,
            "required": required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageConfigOutput):
            return value
        return CodePackageConfigOutput.validate_invocation_value(value)


class CodePackageConfigOutputBuildViaCodePackageConfigInput(BaseModel):
    code_package_config_id: UUID = Field(description="Foreign key for CodePackageConfig.outputs")
    output_key: str
    kind: CodePackageConfigOutputKind
    producer_key: str | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_output_key: str | None = Field(default=None)
    target_provider_key: str | None = Field(default=None)
    target_input_key: str | None = Field(default=None)
    target_semantic_owner: str | None = Field(default=None)
    target_package_family: str | None = Field(default=None)
    target_semantic_kind: str | None = Field(default=None)
    media_type: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required_for: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)


class CodePackageConfigOutputBuildViaCodePackageConfigOutput(BaseModel):
    value: CodePackageConfigOutput


FUNCTIONS = {
    "CodePackageConfigOutput": {
        "build_via_code_package_config": {
            "canonical": {
                "name": "build_via_code_package_config",
                "description": "Create one CodePackageConfig-scoped materialization output contract row.\n\nContract:\n- Parent CodePackageConfig context is propagated by constructor lowering.\n- This describes declared outputs only.\n- CodePackageArtifact owns package output evidence emitted for a concrete CodePackage.\n- Workspace owns revision pins, materialization envelopes, and publication envelopes.",
                "is_constructor": True,
            },
            "input": CodePackageConfigOutputBuildViaCodePackageConfigInput,
            "output": CodePackageConfigOutputBuildViaCodePackageConfigOutput,
        },
    },
}

__all__ = [
    "CodePackageConfigOutput",
    "CodePackageConfigOutputBuildViaCodePackageConfigInput",
    "CodePackageConfigOutputBuildViaCodePackageConfigOutput",
    "FUNCTIONS",
]
