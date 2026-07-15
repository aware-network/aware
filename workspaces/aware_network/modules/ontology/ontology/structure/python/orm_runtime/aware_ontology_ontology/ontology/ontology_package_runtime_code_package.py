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
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class OntologyPackageRuntimeCodePackage(ORMModel):
    """Runtime/implementation CodePackage attached to an OntologyPackage."""

    # Relationships
    code_package: CodePackage | None = Field(default=None)
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    exclude_paths: JsonArray = Field(default_factory=JsonArray)
    import_root: str
    include_paths: JsonArray = Field(default_factory=JsonArray)
    language: CodeLanguage
    manifest_relative_path: str
    package_name: str
    package_root: str = Field(default=".")
    role: str = Field(default="runtime")

    # Foreign Keys
    ontology_package_id: UUID = Field(description="Foreign key for OntologyPackage.runtime_code_packages")
    code_package_id: UUID = Field(description="Foreign key for OntologyPackageRuntimeCodePackage.code_package")
    object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackageRuntimeCodePackage.object_instance_graph_commit"
    )

    @classmethod
    async def build_via_ontology_package(
        cls,
        ontology_package_id: UUID,
        code_package_id: UUID,
        package_name: str,
        language: CodeLanguage,
        import_root: str,
        manifest_relative_path: str,
        package_root: str = ".",
        role: str = "runtime",
        object_instance_graph_commit_id: UUID | None = None,
        include_paths: JsonArray = [],
        exclude_paths: JsonArray = [],
    ) -> OntologyPackageRuntimeCodePackage:
        """
        Attach one Code-owned implementation/runtime package.

        Contract:
        - Parent `OntologyPackage` scope is injected by propagation.
        - Identity is keyed by the attached `CodePackage`.
        - `object_instance_graph_commit_id`, when present, is the exact
          WorkspaceRevision/Hub replay pin for that CodePackage.
        """

        payload = {
            "ontology_package_id": ontology_package_id,
            "code_package_id": code_package_id,
            "package_name": package_name,
            "language": language,
            "import_root": import_root,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "role": role,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "include_paths": include_paths,
            "exclude_paths": exclude_paths,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_ontology_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, OntologyPackageRuntimeCodePackage):
            return value
        return OntologyPackageRuntimeCodePackage.validate_invocation_value(value)


class OntologyPackageRuntimeCodePackageBuildViaOntologyPackageInput(BaseModel):
    ontology_package_id: UUID = Field(description="Foreign key for OntologyPackage.runtime_code_packages")
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = Field(default=".")
    role: str = Field(default="runtime")
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    include_paths: JsonArray = Field(default_factory=JsonArray)
    exclude_paths: JsonArray = Field(default_factory=JsonArray)


class OntologyPackageRuntimeCodePackageBuildViaOntologyPackageOutput(BaseModel):
    value: OntologyPackageRuntimeCodePackage


FUNCTIONS = {
    "OntologyPackageRuntimeCodePackage": {
        "build_via_ontology_package": {
            "canonical": {
                "name": "build_via_ontology_package",
                "description": "Attach one Code-owned implementation/runtime package.\n\nContract:\n- Parent `OntologyPackage` scope is injected by propagation.\n- Identity is keyed by the attached `CodePackage`.\n- `object_instance_graph_commit_id`, when present, is the exact\n  WorkspaceRevision/Hub replay pin for that CodePackage.",
                "is_constructor": True,
            },
            "input": OntologyPackageRuntimeCodePackageBuildViaOntologyPackageInput,
            "output": OntologyPackageRuntimeCodePackageBuildViaOntologyPackageOutput,
        },
    },
}

__all__ = [
    "OntologyPackageRuntimeCodePackage",
    "OntologyPackageRuntimeCodePackageBuildViaOntologyPackageInput",
    "OntologyPackageRuntimeCodePackageBuildViaOntologyPackageOutput",
    "FUNCTIONS",
]
