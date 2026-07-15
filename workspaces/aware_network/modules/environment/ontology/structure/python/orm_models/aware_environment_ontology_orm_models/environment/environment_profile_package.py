from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_environment_ontology_orm_models.environment.environment_config_package import EnvironmentConfigPackage
    from aware_environment_ontology_orm_models.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_orm_models.environment.environment_profile_package_dependency import (
        EnvironmentProfilePackageDependency,
    )
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackage(ORMModel):
    """
    Semantic package root for one reusable EnvironmentProfileConfig.
    Contract:
    - EnvironmentProfilePackage is Environment-owned OS profile package truth.
    - The package root points at reusable EnvironmentProfileConfig, not applied
    EnvironmentProfile runtime state.
    - EnvironmentProfileConfig owns ProcessConfig, ThreadConfig, provider, and
    actor eligibility topology.
    - EnvironmentSessionConfig belongs to EnvironmentConfig and may reference
    profile/process/thread config defaults through portals.
    - EnvironmentProfile stays the concrete Environment-applied bridge to
    running EnvironmentSessions.
    """

    # Relationships
    source_code_package: CodePackage | None = Field(default=None)
    environment_config_package: EnvironmentConfigPackage | None = Field(default=None)
    environment_config_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    environment_profile_config: EnvironmentProfileConfig | None = Field(default=None)
    environment_profile_config_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    dependencies: list[EnvironmentProfilePackageDependency] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    name: str
    package_root: str = Field(default=".")
    profile_key: str | None = Field(default=None)
    sources_root: str = Field(default="profiles")
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)

    # Foreign Keys
    source_code_package_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProfilePackage.source_code_package"
    )
    environment_config_package_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentProfilePackage.environment_config_package"
    )
    environment_config_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackage.environment_config_package_object_instance_graph_commit",
    )
    environment_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentProfilePackage.environment_profile_config"
    )
    environment_profile_config_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackage.environment_profile_config_object_instance_graph_commit",
    )
