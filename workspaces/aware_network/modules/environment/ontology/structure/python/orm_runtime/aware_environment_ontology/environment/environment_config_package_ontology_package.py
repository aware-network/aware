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
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology.ontology.ontology_package import OntologyPackage


class EnvironmentConfigPackageOntologyPackage(ORMModel):
    # Relationships
    ontology_package: OntologyPackage | None = Field(default=None)
    ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    fqn_prefix: str
    name: str

    # Foreign Keys
    environment_config_package_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackage.ontology_packages"
    )
    ontology_package_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentConfigPackageOntologyPackage.ontology_package"
    )
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentConfigPackageOntologyPackage.ontology_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_environment_config_package(
        cls,
        environment_config_package_id: UUID,
        name: str,
        fqn_prefix: str,
        ontology_package_object_instance_graph_commit_id: UUID | None = None,
    ) -> EnvironmentConfigPackageOntologyPackage:
        """
        Create a deterministic environment-owned membership edge to one
        Ontology-owned `OntologyPackage`.

        Contract:
        - Parent `EnvironmentConfigPackage` scope is injected by propagation.
        - Target package identity is resolved from `(name, fqn_prefix)`.
        - `ontology_package_object_instance_graph_commit_id` pins the exact
          OntologyPackage semantic package commit when available.
        - Raw OCG package refs are reached through
          `OntologyPackage.object_config_graph_package`, not duplicated here.
        """

        payload = {
            "environment_config_package_id": environment_config_package_id,
            "name": name,
            "fqn_prefix": fqn_prefix,
            "ontology_package_object_instance_graph_commit_id": ontology_package_object_instance_graph_commit_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_config_package", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentConfigPackageOntologyPackage):
            return value
        return EnvironmentConfigPackageOntologyPackage.validate_invocation_value(value)


class EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageInput(BaseModel):
    environment_config_package_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackage.ontology_packages"
    )
    name: str
    fqn_prefix: str
    ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)


class EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageOutput(BaseModel):
    value: EnvironmentConfigPackageOntologyPackage


FUNCTIONS = {
    "EnvironmentConfigPackageOntologyPackage": {
        "build_via_environment_config_package": {
            "canonical": {
                "name": "build_via_environment_config_package",
                "description": "Create a deterministic environment-owned membership edge to one\nOntology-owned `OntologyPackage`.\n\nContract:\n- Parent `EnvironmentConfigPackage` scope is injected by propagation.\n- Target package identity is resolved from `(name, fqn_prefix)`.\n- `ontology_package_object_instance_graph_commit_id` pins the exact\n  OntologyPackage semantic package commit when available.\n- Raw OCG package refs are reached through\n  `OntologyPackage.object_config_graph_package`, not duplicated here.",
                "is_constructor": True,
            },
            "input": EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageInput,
            "output": EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageOutput,
        },
    },
}

__all__ = [
    "EnvironmentConfigPackageOntologyPackage",
    "EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageInput",
    "EnvironmentConfigPackageOntologyPackageBuildViaEnvironmentConfigPackageOutput",
    "FUNCTIONS",
]
