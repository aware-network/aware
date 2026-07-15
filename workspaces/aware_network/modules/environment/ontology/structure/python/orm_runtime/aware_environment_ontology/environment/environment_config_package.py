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
    from aware_environment_ontology.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology.environment.environment_config_package_dependency import (
        EnvironmentConfigPackageDependency,
    )
    from aware_environment_ontology.environment.environment_config_package_ontology_package import (
        EnvironmentConfigPackageOntologyPackage,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentConfigPackage(ORMModel):
    # Relationships
    environment_config: EnvironmentConfig | None = Field(default=None)
    environment_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontology_packages: list[EnvironmentConfigPackageOntologyPackage] = Field(default_factory=list)
    dependencies: list[EnvironmentConfigPackageDependency] = Field(default_factory=list)

    # Attributes
    handle: str

    # Foreign Keys
    environment_config_id: UUID = Field(description="Foreign key for EnvironmentConfigPackage.environment_config")
    environment_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentConfigPackage.environment_config_object_instance_graph_commit",
    )

    @classmethod
    async def build(
        cls,
        handle: str,
        environment_config_id: UUID,
        environment_config_object_instance_graph_commit_id: UUID | None = None,
    ) -> EnvironmentConfigPackage:
        """
        Create the canonical environment-owned semantic aggregate package.

        Contract:
        - Identity is keyed by the environment `handle`.
        - `EnvironmentConfigPackage` is the package/public root over an existing
          canonical `EnvironmentConfig` portal target.
        - `environment_config_id` must point at the canonical EnvironmentConfig
          stable id for the same handle.
        - `environment_config_object_instance_graph_commit_id` pins the historical
          ObjectInstanceGraphCommit for the semantic EnvironmentConfig root so
          WorkspaceRevision consumers can replay exact environment truth without
          resolving branch head.
        - Repository/layout ownership remains outside this aggregate package.
        - ObjectConfigGraph resolution is only reachable through
          EnvironmentConfig -> OntologyConfig and OntologyPackage ->
          OntologyConfig.
        """

        payload = {
            "handle": handle,
            "environment_config_id": environment_config_id,
            "environment_config_object_instance_graph_commit_id": environment_config_object_instance_graph_commit_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentConfigPackage):
            return value
        return EnvironmentConfigPackage.validate_invocation_value(value)

    async def attach_ontology_package(
        self, name: str, fqn_prefix: str, ontology_package_object_instance_graph_commit_id: UUID | None = None
    ) -> EnvironmentConfigPackageOntologyPackage:
        """
        Attach one Ontology-owned package under this environment aggregate.

        Contract:
        - Parent `EnvironmentConfigPackage` scope is injected by propagation.
        - Target ontology package identity is resolved deterministically from
          `(name, fqn_prefix)`.
        - The optional OIG commit pin is exact ontology package replay truth.
        - This is the semantic ownership rail. Raw `ObjectConfigGraphPackage`
          membership is not owned by EnvironmentConfigPackage.
        """

        payload = {
            "name": name,
            "fqn_prefix": fqn_prefix,
            "ontology_package_object_instance_graph_commit_id": ontology_package_object_instance_graph_commit_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_ontology_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_config_package_ontology_package import (
            EnvironmentConfigPackageOntologyPackage,
        )

        if isinstance(value, EnvironmentConfigPackageOntologyPackage):
            return value
        return EnvironmentConfigPackageOntologyPackage.validate_invocation_value(value)

    async def attach_dependency(
        self,
        dependency_role: str,
        dependency_index: int,
        target_handle: str,
        target_environment_config_package_id: UUID,
        target_environment_config_package_object_instance_graph_commit_id: UUID,
    ) -> EnvironmentConfigPackageDependency:
        """
        Attach one direct EnvironmentConfigPackage dependency.

        Contract:
        - Parent `EnvironmentConfigPackage` scope is injected by propagation.
        - `dependency_role` is usually `base`; the class remains generic so
          kernel is not hard-coded into the ontology.
        - `dependency_index` preserves authored composition order.
        - Target package identity and OIG commit are pinned so WorkspaceRevision
          consumers can replay composition without reopening source manifests.
        """

        payload = {
            "dependency_role": dependency_role,
            "dependency_index": dependency_index,
            "target_handle": target_handle,
            "target_environment_config_package_id": target_environment_config_package_id,
            "target_environment_config_package_object_instance_graph_commit_id": target_environment_config_package_object_instance_graph_commit_id,
        }
        result = await invoke_instance(orm_model=self, function_name="attach_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_environment_ontology.environment.environment_config_package_dependency import (
            EnvironmentConfigPackageDependency,
        )

        if isinstance(value, EnvironmentConfigPackageDependency):
            return value
        return EnvironmentConfigPackageDependency.validate_invocation_value(value)


class EnvironmentConfigPackageBuildInput(BaseModel):
    handle: str
    environment_config_id: UUID
    environment_config_object_instance_graph_commit_id: UUID | None = Field(default=None)


class EnvironmentConfigPackageBuildOutput(BaseModel):
    value: EnvironmentConfigPackage


class EnvironmentConfigPackageAttachOntologyPackageInput(BaseModel):
    name: str
    fqn_prefix: str
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)


class EnvironmentConfigPackageAttachOntologyPackageOutput(BaseModel):
    value: EnvironmentConfigPackageOntologyPackage


class EnvironmentConfigPackageAttachDependencyInput(BaseModel):
    dependency_role: str
    dependency_index: int
    target_handle: str
    target_environment_config_package_id: UUID
    target_environment_config_package_object_instance_graph_commit_id: UUID


class EnvironmentConfigPackageAttachDependencyOutput(BaseModel):
    value: EnvironmentConfigPackageDependency


FUNCTIONS = {
    "EnvironmentConfigPackage": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create the canonical environment-owned semantic aggregate package.\n\nContract:\n- Identity is keyed by the environment `handle`.\n- `EnvironmentConfigPackage` is the package/public root over an existing\n  canonical `EnvironmentConfig` portal target.\n- `environment_config_id` must point at the canonical EnvironmentConfig\n  stable id for the same handle.\n- `environment_config_object_instance_graph_commit_id` pins the historical\n  ObjectInstanceGraphCommit for the semantic EnvironmentConfig root so\n  WorkspaceRevision consumers can replay exact environment truth without\n  resolving branch head.\n- Repository/layout ownership remains outside this aggregate package.\n- ObjectConfigGraph resolution is only reachable through\n  EnvironmentConfig -> OntologyConfig and OntologyPackage ->\n  OntologyConfig.",
                "is_constructor": True,
            },
            "input": EnvironmentConfigPackageBuildInput,
            "output": EnvironmentConfigPackageBuildOutput,
        },
        "attach_ontology_package": {
            "canonical": {
                "name": "attach_ontology_package",
                "description": "Attach one Ontology-owned package under this environment aggregate.\n\nContract:\n- Parent `EnvironmentConfigPackage` scope is injected by propagation.\n- Target ontology package identity is resolved deterministically from\n  `(name, fqn_prefix)`.\n- The optional OIG commit pin is exact ontology package replay truth.\n- This is the semantic ownership rail. Raw `ObjectConfigGraphPackage`\n  membership is not owned by EnvironmentConfigPackage.",
                "is_constructor": False,
            },
            "input": EnvironmentConfigPackageAttachOntologyPackageInput,
            "output": EnvironmentConfigPackageAttachOntologyPackageOutput,
        },
        "attach_dependency": {
            "canonical": {
                "name": "attach_dependency",
                "description": "Attach one direct EnvironmentConfigPackage dependency.\n\nContract:\n- Parent `EnvironmentConfigPackage` scope is injected by propagation.\n- `dependency_role` is usually `base`; the class remains generic so\n  kernel is not hard-coded into the ontology.\n- `dependency_index` preserves authored composition order.\n- Target package identity and OIG commit are pinned so WorkspaceRevision\n  consumers can replay composition without reopening source manifests.",
                "is_constructor": False,
            },
            "input": EnvironmentConfigPackageAttachDependencyInput,
            "output": EnvironmentConfigPackageAttachDependencyOutput,
        },
    },
}

__all__ = [
    "EnvironmentConfigPackage",
    "EnvironmentConfigPackageBuildInput",
    "EnvironmentConfigPackageBuildOutput",
    "EnvironmentConfigPackageAttachOntologyPackageInput",
    "EnvironmentConfigPackageAttachOntologyPackageOutput",
    "EnvironmentConfigPackageAttachDependencyInput",
    "EnvironmentConfigPackageAttachDependencyOutput",
    "FUNCTIONS",
]
