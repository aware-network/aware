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
