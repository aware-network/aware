from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit
    from aware_ontology_ontology_orm_models.ontology.ontology_package import OntologyPackage


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
