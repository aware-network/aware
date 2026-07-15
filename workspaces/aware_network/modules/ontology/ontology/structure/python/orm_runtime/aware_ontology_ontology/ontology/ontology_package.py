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

# Types
from aware_types import JsonArray

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package import CodePackage
    from aware_meta_ontology.graph.config.object_config_graph_package import ObjectConfigGraphPackage
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology.ontology.ontology_config import OntologyConfig
    from aware_ontology_ontology.ontology.ontology_package_dependency import OntologyPackageDependency
    from aware_ontology_ontology.ontology.ontology_package_runtime_code_package import OntologyPackageRuntimeCodePackage


class OntologyPackage(ORMModel):
    """
    Semantic owner for one ontology package.
    `ObjectConfigGraphPackage` remains the raw Meta representation package.
    `CodePackage` remains the raw source/runtime package owner. `OntologyPackage`
    is the semantic package root that binds those lower-level package truths into
    the ontology domain so environments can compose ontology meaning instead of
    raw graph leaves.
    """

    # Relationships
    ontology_config: OntologyConfig | None = Field(default=None)
    ontology_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    source_code_package: CodePackage | None = Field(default=None)
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    object_config_graph_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    runtime_code_packages: list[OntologyPackageRuntimeCodePackage] = Field(default_factory=list)
    dependencies: list[OntologyPackageDependency] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    fqn_prefix: str
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    sources_root: str = Field(default="modules")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    ontology_config_id: UUID | None = Field(default=None, description="Foreign key for OntologyPackage.ontology_config")
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.ontology_config_object_instance_graph_commit"
    )
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.source_code_package"
    )
    object_config_graph_package_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.object_config_graph_package"
    )
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for OntologyPackage.object_config_graph_package_object_instance_graph_commit",
    )
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Foreign key for OntologyPackage.object_config_graph_object_instance_graph_commit"
    )

    @classmethod
    async def build(
        cls,
        name: str,
        fqn_prefix: str,
        ontology_config_id: UUID | None = None,
        ontology_config_object_instance_graph_commit_id: UUID | None = None,
        source_code_package_id: UUID | None = None,
        object_config_graph_package_id: UUID | None = None,
        object_config_graph_package_object_instance_graph_commit_id: UUID | None = None,
        object_config_graph_object_instance_graph_commit_id: UUID | None = None,
        version_number: int = 1,
        title: str | None = None,
        description: str | None = None,
        manifest_relative_path: str | None = None,
        package_root: str = ".",
        sources_root: str = "modules",
    ) -> OntologyPackage:
        """
        Create the canonical ontology-owned semantic package root.

        Contract:
        - Identity is keyed by ontology package `name` and `fqn_prefix`.
        - `ontology_config_id` points to Ontology-owned config/schema truth.
        - `source_code_package_id` points to Code-owned source package truth.
        - `object_config_graph_package_id` points to Meta-owned raw OCG package
          representation truth.
        - OIG commit pins let WorkspaceRevision/Environment consumers replay
          exact ontology package and graph truth without reopening source TOMLs.
        - Environment composition should select `OntologyPackage`; raw
          `ObjectConfigGraphPackage` membership is representation detail and
          compatibility fallback only.
        """

        payload = {
            "name": name,
            "fqn_prefix": fqn_prefix,
            "ontology_config_id": ontology_config_id,
            "ontology_config_object_instance_graph_commit_id": ontology_config_object_instance_graph_commit_id,
            "source_code_package_id": source_code_package_id,
            "object_config_graph_package_id": object_config_graph_package_id,
            "object_config_graph_package_object_instance_graph_commit_id": object_config_graph_package_object_instance_graph_commit_id,
            "object_config_graph_object_instance_graph_commit_id": object_config_graph_object_instance_graph_commit_id,
            "version_number": version_number,
            "title": title,
            "description": description,
            "manifest_relative_path": manifest_relative_path,
            "package_root": package_root,
            "sources_root": sources_root,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, OntologyPackage):
            return value
        return OntologyPackage.validate_invocation_value(value)

    async def attach_runtime_code_package(
        self,
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
        Attach one runtime/implementation CodePackage to this OntologyPackage.

        Contract:
        - Parent `OntologyPackage` scope is injected by propagation.
        - The attached `CodePackage` is implementation/runtime truth, not the
          ontology package source package unless it also appears in
          `source_code_package`.
        - Consumers must use this explicit package contract instead of inferring
          runtime import roots from repository layout.
        """

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="attach_runtime_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_ontology_ontology.ontology.ontology_package_runtime_code_package import (
            OntologyPackageRuntimeCodePackage,
        )

        if isinstance(value, OntologyPackageRuntimeCodePackage):
            return value
        return OntologyPackageRuntimeCodePackage.validate_invocation_value(value)

    async def attach_dependency(
        self,
        target_ontology_package_id: UUID,
        target_package_name: str,
        target_ontology_package_object_instance_graph_commit_id: UUID | None = None,
        target_version_number: int | None = None,
        expected_hash_sha256: str | None = None,
        description: str | None = None,
    ) -> OntologyPackageDependency:
        """
        Attach one ontology package dependency.

        Contract:
        - Parent `OntologyPackage` scope is injected by propagation.
        - Dependencies are ontology package dependencies, not raw OCG dependency
          shortcuts. Raw graph dependency closure is resolved through the target
          `OntologyPackage -> ObjectConfigGraphPackage` bridge.
        """

        payload = {
            "target_ontology_package_id": target_ontology_package_id,
            "target_package_name": target_package_name,
            "target_ontology_package_object_instance_graph_commit_id": target_ontology_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_ontology_ontology.ontology.ontology_package_dependency import OntologyPackageDependency

        if isinstance(value, OntologyPackageDependency):
            return value
        return OntologyPackageDependency.validate_invocation_value(value)


class OntologyPackageBuildInput(BaseModel):
    name: str
    fqn_prefix: str
    ontology_config_id: UUID | None = Field(default=None)
    ontology_config_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)
    object_config_graph_package_id: UUID | None = Field(default=None)
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(default=None)
    version_number: int = Field(default=1)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    package_root: str = Field(default=".")
    sources_root: str = Field(default="modules")


class OntologyPackageBuildOutput(BaseModel):
    value: OntologyPackage


class OntologyPackageAttachRuntimeCodePackageInput(BaseModel):
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


class OntologyPackageAttachRuntimeCodePackageOutput(BaseModel):
    value: OntologyPackageRuntimeCodePackage


class OntologyPackageAttachDependencyInput(BaseModel):
    target_ontology_package_id: UUID
    target_package_name: str
    target_ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class OntologyPackageAttachDependencyOutput(BaseModel):
    value: OntologyPackageDependency


FUNCTIONS = {
    "OntologyPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical ontology-owned semantic package root.\n\nContract:\n- Identity is keyed by ontology package `name` and `fqn_prefix`.\n- `ontology_config_id` points to Ontology-owned config/schema truth.\n- `source_code_package_id` points to Code-owned source package truth.\n- `object_config_graph_package_id` points to Meta-owned raw OCG package\n  representation truth.\n- OIG commit pins let WorkspaceRevision/Environment consumers replay\n  exact ontology package and graph truth without reopening source TOMLs.\n- Environment composition should select `OntologyPackage`; raw\n  `ObjectConfigGraphPackage` membership is representation detail and\n  compatibility fallback only.",
                "is_constructor": True,
            },
            "input": OntologyPackageBuildInput,
            "output": OntologyPackageBuildOutput,
        },
        "attach_runtime_code_package": {
            "canonical": {
                "name": "attach_runtime_code_package",
                "description": "Attach one runtime/implementation CodePackage to this OntologyPackage.\n\nContract:\n- Parent `OntologyPackage` scope is injected by propagation.\n- The attached `CodePackage` is implementation/runtime truth, not the\n  ontology package source package unless it also appears in\n  `source_code_package`.\n- Consumers must use this explicit package contract instead of inferring\n  runtime import roots from repository layout.",
                "is_constructor": False,
            },
            "input": OntologyPackageAttachRuntimeCodePackageInput,
            "output": OntologyPackageAttachRuntimeCodePackageOutput,
        },
        "attach_dependency": {
            "canonical": {
                "name": "attach_dependency",
                "description": "Attach one ontology package dependency.\n\nContract:\n- Parent `OntologyPackage` scope is injected by propagation.\n- Dependencies are ontology package dependencies, not raw OCG dependency\n  shortcuts. Raw graph dependency closure is resolved through the target\n  `OntologyPackage -> ObjectConfigGraphPackage` bridge.",
                "is_constructor": False,
            },
            "input": OntologyPackageAttachDependencyInput,
            "output": OntologyPackageAttachDependencyOutput,
        },
    },
}

__all__ = [
    "OntologyPackage",
    "OntologyPackageBuildInput",
    "OntologyPackageBuildOutput",
    "OntologyPackageAttachRuntimeCodePackageInput",
    "OntologyPackageAttachRuntimeCodePackageOutput",
    "OntologyPackageAttachDependencyInput",
    "OntologyPackageAttachDependencyOutput",
    "FUNCTIONS",
]
