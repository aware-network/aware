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
    from aware_code_ontology.package.code_package import CodePackage
    from aware_code_ontology.semantic.code_semantic_contract_profile import CodeSemanticContractProfile
    from aware_code_ontology.semantic.code_semantic_contract_runtime_import import CodeSemanticContractRuntimeImport


class CodeSemanticContractProfilePackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)
    semantic_contract_profile: CodeSemanticContractProfile | None = Field(default=None)
    runtime_imports: list[CodeSemanticContractRuntimeImport] = Field(default_factory=list)

    # Attributes
    manifest_relative_path: str | None = Field(default=None)
    profile_key: str
    profile_package_key: str
    runtime_import_mode: str = Field(default="dynamic_contract_module")
    runtime_import_required: bool = Field(default=True)
    source_workspace_handle: str | None = Field(default=None)
    status: str = Field(default="active")

    # Foreign Keys
    code_package_id: UUID = Field(description="Foreign key for CodeSemanticContractProfilePackage.code_package")
    semantic_contract_profile_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfilePackage.semantic_contract_profile"
    )

    @classmethod
    async def build(
        cls,
        code_package_id: UUID,
        semantic_contract_profile_id: UUID,
        profile_package_key: str,
        profile_key: str,
        source_workspace_handle: str | None = None,
        manifest_relative_path: str | None = None,
        runtime_import_mode: str = "dynamic_contract_module",
        runtime_import_required: bool = True,
        status: str = "active",
    ) -> CodeSemanticContractProfilePackage:
        """
        Bind one manifest-backed Code package/artifact to a semantic contract
        profile.

        Contract:
        - Each workspace publishes profile packages for its own provider
          surface.
        - Cross-workspace activation targets these package artifacts through
          Workspace dependency/profile resolution.
        - `runtime_import_required` records the current handler-backed bridge:
          semantic contract modules still need dynamic import availability even
          when no product package import is granted.
        """

        payload = {
            "code_package_id": code_package_id,
            "semantic_contract_profile_id": semantic_contract_profile_id,
            "profile_package_key": profile_package_key,
            "profile_key": profile_key,
            "source_workspace_handle": source_workspace_handle,
            "manifest_relative_path": manifest_relative_path,
            "runtime_import_mode": runtime_import_mode,
            "runtime_import_required": runtime_import_required,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticContractProfilePackage):
            return value
        return CodeSemanticContractProfilePackage.validate_invocation_value(value)

    async def attach_runtime_import(
        self,
        provider_key: str,
        semantic_contract_module: str,
        import_role: str = "semantic_contract",
        owned_manifest_kinds: list[str] = [],
        capabilities: list[str] = [],
        required: bool = True,
        status: str = "active",
    ) -> CodeSemanticContractRuntimeImport:
        """
        Attach one dynamic semantic contract module import under this profile
        package.
        """

        payload = {
            "provider_key": provider_key,
            "semantic_contract_module": semantic_contract_module,
            "import_role": import_role,
            "owned_manifest_kinds": owned_manifest_kinds,
            "capabilities": capabilities,
            "required": required,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_runtime_import", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.semantic.code_semantic_contract_runtime_import import CodeSemanticContractRuntimeImport

        if isinstance(value, CodeSemanticContractRuntimeImport):
            return value
        return CodeSemanticContractRuntimeImport.validate_invocation_value(value)


class CodeSemanticContractProfilePackageBuildInput(BaseModel):
    code_package_id: UUID
    semantic_contract_profile_id: UUID
    profile_package_key: str
    profile_key: str
    source_workspace_handle: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    runtime_import_mode: str = Field(default="dynamic_contract_module")
    runtime_import_required: bool = Field(default=True)
    status: str = Field(default="active")


class CodeSemanticContractProfilePackageBuildOutput(BaseModel):
    value: CodeSemanticContractProfilePackage


class CodeSemanticContractProfilePackageAttachRuntimeImportInput(BaseModel):
    provider_key: str
    semantic_contract_module: str
    import_role: str = Field(default="semantic_contract")
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    status: str = Field(default="active")


class CodeSemanticContractProfilePackageAttachRuntimeImportOutput(BaseModel):
    value: CodeSemanticContractRuntimeImport


FUNCTIONS = {
    "CodeSemanticContractProfilePackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Bind one manifest-backed Code package/artifact to a semantic contract\nprofile.\n\nContract:\n- Each workspace publishes profile packages for its own provider\n  surface.\n- Cross-workspace activation targets these package artifacts through\n  Workspace dependency/profile resolution.\n- `runtime_import_required` records the current handler-backed bridge:\n  semantic contract modules still need dynamic import availability even\n  when no product package import is granted.",
                "is_constructor": True,
            },
            "input": CodeSemanticContractProfilePackageBuildInput,
            "output": CodeSemanticContractProfilePackageBuildOutput,
        },
        "attach_runtime_import": {
            "canonical": {
                "name": "attach_runtime_import",
                "description": "Attach one dynamic semantic contract module import under this profile\npackage.",
                "is_constructor": False,
            },
            "input": CodeSemanticContractProfilePackageAttachRuntimeImportInput,
            "output": CodeSemanticContractProfilePackageAttachRuntimeImportOutput,
        },
    },
}

__all__ = [
    "CodeSemanticContractProfilePackage",
    "CodeSemanticContractProfilePackageBuildInput",
    "CodeSemanticContractProfilePackageBuildOutput",
    "CodeSemanticContractProfilePackageAttachRuntimeImportInput",
    "CodeSemanticContractProfilePackageAttachRuntimeImportOutput",
    "FUNCTIONS",
]
