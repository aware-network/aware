from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_config_package import EnvironmentConfigPackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentConfigPackageDependency(BaseModel):
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
        default=None, description="Reverse view for EnvironmentConfigPackage.dependencies"
    )

    # Attributes
    dependency_role: str
    dependency_index: int
    target_handle: str
