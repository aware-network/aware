from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class CodeSemanticContractRuntimeImport(ORMModel):
    # Attributes
    capabilities: list[str] = Field(default_factory=list)
    import_role: str = Field(default="semantic_contract")
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    provider_key: str
    required: bool = Field(default=True)
    semantic_contract_module: str
    status: str = Field(default="active")

    # Foreign Keys
    code_semantic_contract_profile_package_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfilePackage.runtime_imports"
    )

    @classmethod
    async def build_via_code_semantic_contract_profile_package(
        cls,
        code_semantic_contract_profile_package_id: UUID,
        provider_key: str,
        semantic_contract_module: str,
        import_role: str = "semantic_contract",
        owned_manifest_kinds: list[str] = [],
        capabilities: list[str] = [],
        required: bool = True,
        status: str = "active",
    ) -> CodeSemanticContractRuntimeImport:
        """
        Record one dynamic semantic contract runtime import required by a
        CodeSemanticContractProfilePackage.

        Contract:
        - This is runtime/provider activation truth, not product package import
          permission.
        - The current materializer still imports semantic contract handler
          modules, so profile packages must expose these dynamic runtime imports
          until the full contract surface becomes declarative.
        """

        payload = {
            "code_semantic_contract_profile_package_id": code_semantic_contract_profile_package_id,
            "provider_key": provider_key,
            "semantic_contract_module": semantic_contract_module,
            "import_role": import_role,
            "owned_manifest_kinds": owned_manifest_kinds,
            "capabilities": capabilities,
            "required": required,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_semantic_contract_profile_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticContractRuntimeImport):
            return value
        return CodeSemanticContractRuntimeImport.validate_invocation_value(value)


class CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageInput(BaseModel):
    code_semantic_contract_profile_package_id: UUID = Field(
        description="Foreign key for CodeSemanticContractProfilePackage.runtime_imports"
    )
    provider_key: str
    semantic_contract_module: str
    import_role: str = Field(default="semantic_contract")
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    status: str = Field(default="active")


class CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageOutput(BaseModel):
    value: CodeSemanticContractRuntimeImport


FUNCTIONS = {
    "CodeSemanticContractRuntimeImport": {
        "build_via_code_semantic_contract_profile_package": {
            "canonical": {
                "name": "build_via_code_semantic_contract_profile_package",
                "description": "Record one dynamic semantic contract runtime import required by a\nCodeSemanticContractProfilePackage.\n\nContract:\n- This is runtime/provider activation truth, not product package import\n  permission.\n- The current materializer still imports semantic contract handler\n  modules, so profile packages must expose these dynamic runtime imports\n  until the full contract surface becomes declarative.",
                "is_constructor": True,
            },
            "input": CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageInput,
            "output": CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageOutput,
        },
    },
}

__all__ = [
    "CodeSemanticContractRuntimeImport",
    "CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageInput",
    "CodeSemanticContractRuntimeImportBuildViaCodeSemanticContractProfilePackageOutput",
    "FUNCTIONS",
]
