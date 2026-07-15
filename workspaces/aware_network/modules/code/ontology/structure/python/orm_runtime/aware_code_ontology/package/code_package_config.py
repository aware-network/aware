from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package_enums import (
    CodePackageConfigInputKind,
    CodePackageConfigOutputKind,
    CodePackageConfigRuntimeContextKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_code_ontology.package.code_package_config_input import CodePackageConfigInput
    from aware_code_ontology.package.code_package_config_output import CodePackageConfigOutput
    from aware_code_ontology.package.code_package_config_runtime_context import CodePackageConfigRuntimeContext


class CodePackageConfig(ORMModel):
    # Relationships
    packages: list[CodePackage] = Field(default_factory=list)
    inputs: list[CodePackageConfigInput] = Field(default_factory=list)
    outputs: list[CodePackageConfigOutput] = Field(default_factory=list)
    runtime_contexts: list[CodePackageConfigRuntimeContext] = Field(default_factory=list)

    # Attributes
    config_key: str
    provider_key: str
    semantic_owner: str
    contract: str
    package_role: str | None = Field(default=None)
    manifest_kind: str
    manifest_filename: str
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    default_surface: str | None = Field(default=None)
    materialization_capability: str | None = Field(default=None)

    @classmethod
    async def build(
        cls,
        config_key: str,
        provider_key: str,
        semantic_owner: str,
        contract: str,
        manifest_kind: str,
        manifest_filename: str,
        package_role: str | None = None,
        semantic_package_family: str | None = None,
        semantic_package_kind: str | None = None,
        semantic_projection_name: str | None = None,
        semantic_root_kind: str | None = None,
        default_surface: str | None = None,
        materialization_capability: str | None = None,
    ) -> CodePackageConfig:
        """
        Create one Code-owned package configuration contract.

        Contract:
        - Identity is stable by `config_key`.
        - Config owns semantic package kind, manifest kind, and materialization contract vocabulary.
        - Workspace consumes this contract but owns deployment selection, planning, execution, and receipts.
        - Concrete CodePackage rows are constructed under `packages` so package identity is config-scoped.
        """

        payload = {
            "config_key": config_key,
            "provider_key": provider_key,
            "semantic_owner": semantic_owner,
            "contract": contract,
            "manifest_kind": manifest_kind,
            "manifest_filename": manifest_filename,
            "package_role": package_role,
            "semantic_package_family": semantic_package_family,
            "semantic_package_kind": semantic_package_kind,
            "semantic_projection_name": semantic_projection_name,
            "semantic_root_kind": semantic_root_kind,
            "default_surface": default_surface,
            "materialization_capability": materialization_capability,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageConfig):
            return value
        return CodePackageConfig.validate_invocation_value(value)

    async def create_package(
        self,
        package_name: str,
        language: CodeLanguage,
        manifest_relative_path: str,
        package_root: str,
        sources_root: str | None = None,
        fqn_prefix: str | None = None,
        surface: str | None = None,
    ) -> CodePackage:
        """
        Create one concrete CodePackage under this CodePackageConfig.

        Contract:
        - Parent CodePackageConfig context is propagated by constructor lowering.
        - Runtime package layout remains instance payload.
        - `surface` is an optional package override; consumers fall back to `default_surface`.
        """

        payload = {
            "package_name": package_name,
            "language": language,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
            "fqn_prefix": fqn_prefix,
            "surface": surface,
        }
        result = await invoke_instance(orm_model=self, function_name="create_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package import CodePackage

        if isinstance(value, CodePackage):
            return value
        return CodePackage.validate_invocation_value(value)

    async def add_input(
        self,
        input_key: str,
        kind: CodePackageConfigInputKind,
        artifact_family: str | None = None,
        artifact_role: str | None = None,
        package_family: str | None = None,
        semantic_kind: str | None = None,
        runtime_contract_version: str | None = None,
        required: bool = True,
    ) -> CodePackageConfigInput:
        """Declare one typed materialization input accepted by this package config."""

        payload = {
            "input_key": input_key,
            "kind": kind,
            "artifact_family": artifact_family,
            "artifact_role": artifact_role,
            "package_family": package_family,
            "semantic_kind": semantic_kind,
            "runtime_contract_version": runtime_contract_version,
            "required": required,
        }
        result = await invoke_instance(orm_model=self, function_name="add_input", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_config_input import CodePackageConfigInput

        if isinstance(value, CodePackageConfigInput):
            return value
        return CodePackageConfigInput.validate_invocation_value(value)

    async def add_output(
        self,
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
        """Declare one typed materialization output emitted by this package config."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="add_output", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_config_output import CodePackageConfigOutput

        if isinstance(value, CodePackageConfigOutput):
            return value
        return CodePackageConfigOutput.validate_invocation_value(value)

    async def add_runtime_context(
        self,
        context_key: str,
        kind: CodePackageConfigRuntimeContextKind,
        package_name: str | None = None,
        projection_name: str | None = None,
        runtime_contract_version: str | None = None,
        required: bool = True,
    ) -> CodePackageConfigRuntimeContext:
        """Declare one typed runtime context required by this package config."""

        payload = {
            "context_key": context_key,
            "kind": kind,
            "package_name": package_name,
            "projection_name": projection_name,
            "runtime_contract_version": runtime_contract_version,
            "required": required,
        }
        result = await invoke_instance(orm_model=self, function_name="add_runtime_context", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_config_runtime_context import CodePackageConfigRuntimeContext

        if isinstance(value, CodePackageConfigRuntimeContext):
            return value
        return CodePackageConfigRuntimeContext.validate_invocation_value(value)


class CodePackageConfigBuildInput(BaseModel):
    config_key: str
    provider_key: str
    semantic_owner: str
    contract: str
    manifest_kind: str
    manifest_filename: str
    package_role: str | None = Field(default=None)
    semantic_package_family: str | None = Field(default=None)
    semantic_package_kind: str | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    default_surface: str | None = Field(default=None)
    materialization_capability: str | None = Field(default=None)


class CodePackageConfigBuildOutput(BaseModel):
    value: CodePackageConfig


class CodePackageConfigCreatePackageInput(BaseModel):
    package_name: str
    language: CodeLanguage
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    surface: str | None = Field(default=None)


class CodePackageConfigCreatePackageOutput(BaseModel):
    value: CodePackage


class CodePackageConfigAddInputInput(BaseModel):
    input_key: str
    kind: CodePackageConfigInputKind
    artifact_family: str | None = Field(default=None)
    artifact_role: str | None = Field(default=None)
    package_family: str | None = Field(default=None)
    semantic_kind: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)


class CodePackageConfigAddInputOutput(BaseModel):
    value: CodePackageConfigInput


class CodePackageConfigAddOutputInput(BaseModel):
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


class CodePackageConfigAddOutputOutput(BaseModel):
    value: CodePackageConfigOutput


class CodePackageConfigAddRuntimeContextInput(BaseModel):
    context_key: str
    kind: CodePackageConfigRuntimeContextKind
    package_name: str | None = Field(default=None)
    projection_name: str | None = Field(default=None)
    runtime_contract_version: str | None = Field(default=None)
    required: bool = Field(default=True)


class CodePackageConfigAddRuntimeContextOutput(BaseModel):
    value: CodePackageConfigRuntimeContext


FUNCTIONS = {
    "CodePackageConfig": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create one Code-owned package configuration contract.\n\nContract:\n- Identity is stable by `config_key`.\n- Config owns semantic package kind, manifest kind, and materialization contract vocabulary.\n- Workspace consumes this contract but owns deployment selection, planning, execution, and receipts.\n- Concrete CodePackage rows are constructed under `packages` so package identity is config-scoped.",
                "is_constructor": True,
            },
            "input": CodePackageConfigBuildInput,
            "output": CodePackageConfigBuildOutput,
        },
        "create_package": {
            "canonical": {
                "name": "create_package",
                "description": "Create one concrete CodePackage under this CodePackageConfig.\n\nContract:\n- Parent CodePackageConfig context is propagated by constructor lowering.\n- Runtime package layout remains instance payload.\n- `surface` is an optional package override; consumers fall back to `default_surface`.",
                "is_constructor": False,
            },
            "input": CodePackageConfigCreatePackageInput,
            "output": CodePackageConfigCreatePackageOutput,
        },
        "add_input": {
            "canonical": {
                "name": "add_input",
                "description": "Declare one typed materialization input accepted by this package config.",
                "is_constructor": False,
            },
            "input": CodePackageConfigAddInputInput,
            "output": CodePackageConfigAddInputOutput,
        },
        "add_output": {
            "canonical": {
                "name": "add_output",
                "description": "Declare one typed materialization output emitted by this package config.",
                "is_constructor": False,
            },
            "input": CodePackageConfigAddOutputInput,
            "output": CodePackageConfigAddOutputOutput,
        },
        "add_runtime_context": {
            "canonical": {
                "name": "add_runtime_context",
                "description": "Declare one typed runtime context required by this package config.",
                "is_constructor": False,
            },
            "input": CodePackageConfigAddRuntimeContextInput,
            "output": CodePackageConfigAddRuntimeContextOutput,
        },
    },
}

__all__ = [
    "CodePackageConfig",
    "CodePackageConfigBuildInput",
    "CodePackageConfigBuildOutput",
    "CodePackageConfigCreatePackageInput",
    "CodePackageConfigCreatePackageOutput",
    "CodePackageConfigAddInputInput",
    "CodePackageConfigAddInputOutput",
    "CodePackageConfigAddOutputInput",
    "CodePackageConfigAddOutputOutput",
    "CodePackageConfigAddRuntimeContextInput",
    "CodePackageConfigAddRuntimeContextOutput",
    "FUNCTIONS",
]
