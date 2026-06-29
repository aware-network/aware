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
    from aware_code_ontology.package.code_package import CodePackage


class CodeSemanticPackageBinding(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None)

    # Attributes
    code_package_config_key: str | None = Field(default=None)
    code_module_name: str | None = Field(default=None)
    capabilities: list[str] = Field(default_factory=list)
    manifest_relative_path: str | None = Field(default=None)
    module_package_id: str
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    semantic_contract_module: str | None = Field(default=None)
    semantic_contract_name: str
    semantic_contract_role: str
    status: str = Field(default="bound")

    # Foreign Keys
    code_semantic_provider_registration_id: UUID = Field(
        description="Foreign key for CodeSemanticProviderRegistration.semantic_package_bindings"
    )
    code_package_id: UUID = Field(description="Foreign key for CodeSemanticPackageBinding.code_package")

    @classmethod
    async def build_via_code_semantic_provider_registration(
        cls,
        code_semantic_provider_registration_id: UUID,
        code_package_id: UUID,
        module_package_id: str,
        semantic_contract_role: str,
        semantic_contract_name: str,
        code_package_config_key: str | None = None,
        code_module_name: str | None = None,
        module_package_kind: str | None = None,
        module_relative_package_root: str | None = None,
        manifest_relative_path: str | None = None,
        semantic_contract_module: str | None = None,
        owned_manifest_kinds: list[str] = [],
        capabilities: list[str] = [],
        status: str = "bound",
    ) -> CodeSemanticPackageBinding:
        """
        Record one Code-owned package-slot semantic contract binding.

        Contract:
        - The source CodePackage remains standalone package truth.
        - Semantic fields are derived from CodePackageConfig and
          CodeModuleCodePackage package-slot metadata.
        - Workspace may reference this binding in resolution receipts, but does
          not author or duplicate the binding.
        """

        payload = {
            "code_semantic_provider_registration_id": code_semantic_provider_registration_id,
            "code_package_id": code_package_id,
            "module_package_id": module_package_id,
            "semantic_contract_role": semantic_contract_role,
            "semantic_contract_name": semantic_contract_name,
            "code_package_config_key": code_package_config_key,
            "code_module_name": code_module_name,
            "module_package_kind": module_package_kind,
            "module_relative_package_root": module_relative_package_root,
            "manifest_relative_path": manifest_relative_path,
            "semantic_contract_module": semantic_contract_module,
            "owned_manifest_kinds": owned_manifest_kinds,
            "capabilities": capabilities,
            "status": status,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_semantic_provider_registration", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticPackageBinding):
            return value
        return CodeSemanticPackageBinding.validate_invocation_value(value)


class CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationInput(BaseModel):
    code_semantic_provider_registration_id: UUID = Field(
        description="Foreign key for CodeSemanticProviderRegistration.semantic_package_bindings"
    )
    code_package_id: UUID
    module_package_id: str
    semantic_contract_role: str
    semantic_contract_name: str
    code_package_config_key: str | None = Field(default=None)
    code_module_name: str | None = Field(default=None)
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    semantic_contract_module: str | None = Field(default=None)
    owned_manifest_kinds: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    status: str = Field(default="bound")


class CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationOutput(BaseModel):
    value: CodeSemanticPackageBinding


FUNCTIONS = {
    "CodeSemanticPackageBinding": {
        "build_via_code_semantic_provider_registration": {
            "canonical": {
                "name": "build_via_code_semantic_provider_registration",
                "description": "Record one Code-owned package-slot semantic contract binding.\n\nContract:\n- The source CodePackage remains standalone package truth.\n- Semantic fields are derived from CodePackageConfig and\n  CodeModuleCodePackage package-slot metadata.\n- Workspace may reference this binding in resolution receipts, but does\n  not author or duplicate the binding.",
                "is_constructor": True,
            },
            "input": CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationInput,
            "output": CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationOutput,
        },
    },
}

__all__ = [
    "CodeSemanticPackageBinding",
    "CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationInput",
    "CodeSemanticPackageBindingBuildViaCodeSemanticProviderRegistrationOutput",
    "FUNCTIONS",
]
