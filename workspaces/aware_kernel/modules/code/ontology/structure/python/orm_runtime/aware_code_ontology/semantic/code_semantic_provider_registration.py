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
    from aware_code_ontology.module.code_module import CodeModule
    from aware_code_ontology.semantic.code_semantic_package_binding import CodeSemanticPackageBinding


class CodeSemanticProviderRegistration(ORMModel):
    # Relationships
    code_module: CodeModule | None = Field(default=None)
    semantic_package_bindings: list[CodeSemanticPackageBinding] = Field(default_factory=list)

    # Attributes
    provider_key: str
    semantic_contract_module: str | None = Field(default=None)
    status: str = Field(default="registered")

    # Foreign Keys
    code_module_id: UUID = Field(description="Foreign key for CodeSemanticProviderRegistration.code_module")

    @classmethod
    async def build(
        cls,
        code_module_id: UUID,
        provider_key: str,
        semantic_contract_module: str | None = None,
        status: str = "registered",
    ) -> CodeSemanticProviderRegistration:
        """
        Register Code-owned semantic contract provider participation.

        Contract:
        - Provider registration is anchored to CodeModule truth, not
          WorkspaceCodeModulePin.
        - Package-slot participation is recorded by CodeSemanticPackageBinding.
        - Workspace consumes resolved provider records through revision
          receipts only.
        """

        payload = {
            "code_module_id": code_module_id,
            "provider_key": provider_key,
            "semantic_contract_module": semantic_contract_module,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeSemanticProviderRegistration):
            return value
        return CodeSemanticProviderRegistration.validate_invocation_value(value)

    async def bind_semantic_package(
        self,
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
        """Attach one Code-owned semantic package binding under this provider."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="bind_semantic_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.semantic.code_semantic_package_binding import CodeSemanticPackageBinding

        if isinstance(value, CodeSemanticPackageBinding):
            return value
        return CodeSemanticPackageBinding.validate_invocation_value(value)


class CodeSemanticProviderRegistrationBuildInput(BaseModel):
    code_module_id: UUID
    provider_key: str
    semantic_contract_module: str | None = Field(default=None)
    status: str = Field(default="registered")


class CodeSemanticProviderRegistrationBuildOutput(BaseModel):
    value: CodeSemanticProviderRegistration


class CodeSemanticProviderRegistrationBindSemanticPackageInput(BaseModel):
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


class CodeSemanticProviderRegistrationBindSemanticPackageOutput(BaseModel):
    value: CodeSemanticPackageBinding


FUNCTIONS = {
    "CodeSemanticProviderRegistration": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Register Code-owned semantic contract provider participation.\n\nContract:\n- Provider registration is anchored to CodeModule truth, not\n  WorkspaceCodeModulePin.\n- Package-slot participation is recorded by CodeSemanticPackageBinding.\n- Workspace consumes resolved provider records through revision\n  receipts only.",
                "is_constructor": True,
            },
            "input": CodeSemanticProviderRegistrationBuildInput,
            "output": CodeSemanticProviderRegistrationBuildOutput,
        },
        "bind_semantic_package": {
            "canonical": {
                "name": "bind_semantic_package",
                "description": "Attach one Code-owned semantic package binding under this provider.",
                "is_constructor": False,
            },
            "input": CodeSemanticProviderRegistrationBindSemanticPackageInput,
            "output": CodeSemanticProviderRegistrationBindSemanticPackageOutput,
        },
    },
}

__all__ = [
    "CodeSemanticProviderRegistration",
    "CodeSemanticProviderRegistrationBuildInput",
    "CodeSemanticProviderRegistrationBuildOutput",
    "CodeSemanticProviderRegistrationBindSemanticPackageInput",
    "CodeSemanticProviderRegistrationBindSemanticPackageOutput",
    "FUNCTIONS",
]
