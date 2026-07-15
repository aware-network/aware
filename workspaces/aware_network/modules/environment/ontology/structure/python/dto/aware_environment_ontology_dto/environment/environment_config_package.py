from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_config import EnvironmentConfig
    from aware_environment_ontology_dto.environment.environment_config_package_dependency import (
        EnvironmentConfigPackageDependency,
    )
    from aware_environment_ontology_dto.environment.environment_config_package_ontology_package import (
        EnvironmentConfigPackageOntologyPackage,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentConfigPackage(BaseModel):
    # Relationships
    environment_config: EnvironmentConfig | None = Field(default=None)
    environment_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    ontology_packages: list[EnvironmentConfigPackageOntologyPackage] = Field(default_factory=list)
    dependencies: list[EnvironmentConfigPackageDependency] = Field(default_factory=list)

    # Attributes
    handle: str
