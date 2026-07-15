from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology_orm_models.environment.environment_config_package_dependency import (
        EnvironmentConfigPackageDependency,
    )
    from aware_environment_ontology_orm_models.environment.environment_config_package_ontology_package import (
        EnvironmentConfigPackageOntologyPackage,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


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
