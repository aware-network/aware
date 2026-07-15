from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_code_ontology.module.code_module_code_package import CodeModuleCodePackage
    from aware_code_ontology.module.code_module_dependence import CodeModuleDependence
    from aware_code_ontology.package.code_package import CodePackage


class CodeModule(ORMModel):
    # Relationships
    dependences: list[CodeModuleDependence] = Field(default_factory=list, exclude=True)

    # Attributes
    aware_module_version: int = Field(default=1)
    languages: list[CodeLanguage] = Field(default_factory=list)
    manifest_hash: str | None = Field(default=None)
    manifest_relative_path: str = Field(default="aware.module.toml")
    name: str

    # Edges
    code_module_code_packages: list[CodeModuleCodePackage] = Field(
        default_factory=list, description="Edge association helper for packages"
    )

    @property
    def packages(self) -> list[CodePackage]:
        return [edge.code_package for edge in self.code_module_code_packages if edge.code_package is not None]

    @classmethod
    async def build(
        cls,
        name: str,
        languages: list[CodeLanguage],
        aware_module_version: int = 1,
        manifest_relative_path: str = "aware.module.toml",
        manifest_hash: str | None = None,
    ) -> CodeModule:
        """Create deterministic CodeModule identity by name."""

        payload = {
            "name": name,
            "languages": languages,
            "aware_module_version": aware_module_version,
            "manifest_relative_path": manifest_relative_path,
            "manifest_hash": manifest_hash,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodeModule):
            return value
        return CodeModule.validate_invocation_value(value)

    async def create_dependency(self, name: str) -> CodeModuleDependence:
        """Create a deterministic dependency edge to another CodeModule."""

        payload = {"name": name}
        result = await invoke_instance(orm_model=self, function_name="create_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.module.code_module_dependence import CodeModuleDependence

        if isinstance(value, CodeModuleDependence):
            return value
        return CodeModuleDependence.validate_invocation_value(value)

    async def attach_package(
        self,
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
        Attach an existing CodePackage under this CodeModule.

        Contract:
        - `CodeModule` is a semantic package bundle only.
        - `CodePackage` remains standalone package truth.
        - `CodeModuleCodePackage` carries module-local package slot metadata so
          Workspace can mount resolved module packages without owning semantic
          package-family vocabulary.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="attach_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.module.code_module_code_package import CodeModuleCodePackage

        if isinstance(value, CodeModuleCodePackage):
            return value
        return CodeModuleCodePackage.validate_invocation_value(value)


class CodeModuleBuildInput(BaseModel):
    name: str
    languages: list[CodeLanguage] = Field(default_factory=list)
    aware_module_version: int = Field(default=1)
    manifest_relative_path: str = Field(default="aware.module.toml")
    manifest_hash: str | None = Field(default=None)


class CodeModuleBuildOutput(BaseModel):
    value: CodeModule


class CodeModuleCreateDependencyInput(BaseModel):
    name: str


class CodeModuleCreateDependencyOutput(BaseModel):
    value: CodeModuleDependence


class CodeModuleAttachPackageInput(BaseModel):
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


class CodeModuleAttachPackageOutput(BaseModel):
    value: CodeModuleCodePackage


FUNCTIONS = {
    "CodeModule": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic CodeModule identity by name.",
                "is_constructor": True,
            },
            "input": CodeModuleBuildInput,
            "output": CodeModuleBuildOutput,
        },
        "create_dependency": {
            "canonical": {
                "name": "create_dependency",
                "description": "Create a deterministic dependency edge to another CodeModule.",
                "is_constructor": False,
            },
            "input": CodeModuleCreateDependencyInput,
            "output": CodeModuleCreateDependencyOutput,
        },
        "attach_package": {
            "canonical": {
                "name": "attach_package",
                "description": "Attach an existing CodePackage under this CodeModule.\n\nContract:\n- `CodeModule` is a semantic package bundle only.\n- `CodePackage` remains standalone package truth.\n- `CodeModuleCodePackage` carries module-local package slot metadata so\n  Workspace can mount resolved module packages without owning semantic\n  package-family vocabulary.",
                "is_constructor": False,
            },
            "input": CodeModuleAttachPackageInput,
            "output": CodeModuleAttachPackageOutput,
        },
    },
}

__all__ = [
    "CodeModule",
    "CodeModuleBuildInput",
    "CodeModuleBuildOutput",
    "CodeModuleCreateDependencyInput",
    "CodeModuleCreateDependencyOutput",
    "CodeModuleAttachPackageInput",
    "CodeModuleAttachPackageOutput",
    "FUNCTIONS",
]
