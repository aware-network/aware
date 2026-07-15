from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_config_package import EnvironmentConfigPackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentConfigPackageDependency(ORMModel):
    """
    A direct dependency from one EnvironmentConfigPackage to another.
    This models environment config composition as semantic package truth. The
    current kernel base is just one dependency role/value, not a special module
    dependency copied into product environments.
    """

    # Relationships
    target_environment_config_package: EnvironmentConfigPackage | None = Field(default=None)
    target_environment_config_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None
    )
    environment_config_package: EnvironmentConfigPackage | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentConfigPackage.dependencies"
    )

    # Attributes
    dependency_role: str
    dependency_index: int
    target_handle: str

    # Foreign Keys
    environment_config_package_id: UUID = Field(description="Foreign key for EnvironmentConfigPackage.dependencies")
    target_environment_config_package_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackageDependency.target_environment_config_package"
    )
    target_environment_config_package_object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for EnvironmentConfigPackageDependency.target_environment_config_package_object_instance_graph_commit"
    )
