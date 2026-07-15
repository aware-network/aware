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


class CodeModuleCodePackage(ORMModel):
    # Relationships
    code_package: CodePackage | None = Field(default=None, description="Association target reference to CodePackage")

    # Attributes
    manifest_relative_path: str | None = Field(default=None)
    mirrors_ontology: bool = Field(default=False)
    module_package_id: str | None = Field(default=None)
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    semantic_contract_capabilities: list[str] = Field(default_factory=list)
    semantic_contract_module: str | None = Field(default=None)
    semantic_contract_name: str | None = Field(default=None)
    semantic_contract_owns_manifest_kinds: list[str] = Field(default_factory=list)
    semantic_contract_provider_key: str | None = Field(default=None)
    semantic_contract_role: str | None = Field(default=None)
    visibility: str = Field(default="module")

    # Foreign Keys
    code_package_id: UUID = Field(description="Join FK to CodePackage")
    code_module_id: UUID = Field(description="Join FK to CodeModule")

    @classmethod
    async def build_via_code_module(
        cls,
        code_module_id: UUID,
        code_package_id: UUID,
        module_package_id: str | None = None,
        module_package_kind: str | None = None,
        module_relative_package_root: str | None = None,
        manifest_relative_path: str | None = None,
        visibility: str = "module",
        semantic_contract_role: str | None = None,
        semantic_contract_name: str | None = None,
        semantic_contract_provider_key: str | None = None,
        semantic_contract_module: str | None = None,
        semantic_contract_owns_manifest_kinds: list[str] = [],
        semantic_contract_capabilities: list[str] = [],
        mirrors_ontology: bool = False,
    ) -> CodeModuleCodePackage:
        """
        Attach an existing standalone CodePackage under this CodeModule.

        Contract:
        - `CodePackage` remains standalone raw/source package identity.
        - `CodeModuleCodePackage` is the module-local package slot emitted from
          `aware.module.toml` package inventory.
        - Semantic contract fields are declarative package-role metadata only;
          executable bindings remain package-local contract/runtime truth.
        """

        payload = {
            "code_module_id": code_module_id,
            "code_package_id": code_package_id,
            "module_package_id": module_package_id,
            "module_package_kind": module_package_kind,
            "module_relative_package_root": module_relative_package_root,
            "manifest_relative_path": manifest_relative_path,
            "visibility": visibility,
            "semantic_contract_role": semantic_contract_role,
            "semantic_contract_name": semantic_contract_name,
            "semantic_contract_provider_key": semantic_contract_provider_key,
            "semantic_contract_module": semantic_contract_module,
            "semantic_contract_owns_manifest_kinds": semantic_contract_owns_manifest_kinds,
            "semantic_contract_capabilities": semantic_contract_capabilities,
            "mirrors_ontology": mirrors_ontology,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_module", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeModuleCodePackage):
            return value
        return CodeModuleCodePackage.validate_invocation_value(value)


class CodeModuleCodePackageBuildViaCodeModuleInput(BaseModel):
    code_module_id: UUID = Field(description="Join FK to CodeModule")
    code_package_id: UUID
    module_package_id: str | None = Field(default=None)
    module_package_kind: str | None = Field(default=None)
    module_relative_package_root: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    visibility: str = Field(default="module")
    semantic_contract_role: str | None = Field(default=None)
    semantic_contract_name: str | None = Field(default=None)
    semantic_contract_provider_key: str | None = Field(default=None)
    semantic_contract_module: str | None = Field(default=None)
    semantic_contract_owns_manifest_kinds: list[str] = Field(default_factory=list)
    semantic_contract_capabilities: list[str] = Field(default_factory=list)
    mirrors_ontology: bool = Field(default=False)


class CodeModuleCodePackageBuildViaCodeModuleOutput(BaseModel):
    value: CodeModuleCodePackage


FUNCTIONS = {
    "CodeModuleCodePackage": {
        "build_via_code_module": {
            "canonical": {
                "name": "build_via_code_module",
                "description": "Attach an existing standalone CodePackage under this CodeModule.\n\nContract:\n- `CodePackage` remains standalone raw/source package identity.\n- `CodeModuleCodePackage` is the module-local package slot emitted from\n  `aware.module.toml` package inventory.\n- Semantic contract fields are declarative package-role metadata only;\n  executable bindings remain package-local contract/runtime truth.",
                "is_constructor": True,
            },
            "input": CodeModuleCodePackageBuildViaCodeModuleInput,
            "output": CodeModuleCodePackageBuildViaCodeModuleOutput,
        },
    },
}

__all__ = [
    "CodeModuleCodePackage",
    "CodeModuleCodePackageBuildViaCodeModuleInput",
    "CodeModuleCodePackageBuildViaCodeModuleOutput",
    "FUNCTIONS",
]
