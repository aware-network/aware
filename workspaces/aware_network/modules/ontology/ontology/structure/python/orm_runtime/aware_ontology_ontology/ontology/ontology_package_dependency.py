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


class OntologyPackageDependency(ORMModel):
    """Direct ontology package dependency bridge."""

    # Relationships
    target_ontology_package: OntologyPackage | None = Field(default=None)
    target_ontology_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontology_package: OntologyPackage | None = Field(
        default=None, exclude=True, description="Reverse view for OntologyPackage.dependencies"
    )

    # Attributes
    description: str | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    target_package_name: str
    target_version_number: int | None = Field(default=None)

    # Foreign Keys
    ontology_package_id: UUID = Field(description="Foreign key for OntologyPackage.dependencies")
    target_ontology_package_id: UUID = Field(
        description="Foreign key for OntologyPackageDependency.target_ontology_package"
    )
    target_ontology_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for OntologyPackageDependency.target_ontology_package_object_instance_graph_commit",
    )

    @classmethod
    async def build_via_ontology_package(
        cls,
        ontology_package_id: UUID,
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
        - Identity is keyed by the target `OntologyPackage`.
        - The optional OIG commit pin is the exact reproducibility authority for
          WorkspaceRevision and Hub consumers.
        """

        payload = {
            "ontology_package_id": ontology_package_id,
            "target_ontology_package_id": target_ontology_package_id,
            "target_package_name": target_package_name,
            "target_ontology_package_object_instance_graph_commit_id": target_ontology_package_object_instance_graph_commit_id,
            "target_version_number": target_version_number,
            "expected_hash_sha256": expected_hash_sha256,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_ontology_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, OntologyPackageDependency):
            return value
        return OntologyPackageDependency.validate_invocation_value(value)


class OntologyPackageDependencyBuildViaOntologyPackageInput(BaseModel):
    ontology_package_id: UUID = Field(description="Foreign key for OntologyPackage.dependencies")
    target_ontology_package_id: UUID
    target_package_name: str
    target_ontology_package_object_instance_graph_commit_id: UUID | None = Field(default=None)
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)


class OntologyPackageDependencyBuildViaOntologyPackageOutput(BaseModel):
    value: OntologyPackageDependency


FUNCTIONS = {
    "OntologyPackageDependency": {
        "build_via_ontology_package": {
            "canonical": {
                "name": "build_via_ontology_package",
                "description": "Attach one ontology package dependency.\n\nContract:\n- Parent `OntologyPackage` scope is injected by propagation.\n- Identity is keyed by the target `OntologyPackage`.\n- The optional OIG commit pin is the exact reproducibility authority for\n  WorkspaceRevision and Hub consumers.",
                "is_constructor": True,
            },
            "input": OntologyPackageDependencyBuildViaOntologyPackageInput,
            "output": OntologyPackageDependencyBuildViaOntologyPackageOutput,
        },
    },
}

__all__ = [
    "OntologyPackageDependency",
    "OntologyPackageDependencyBuildViaOntologyPackageInput",
    "OntologyPackageDependencyBuildViaOntologyPackageOutput",
    "FUNCTIONS",
]
