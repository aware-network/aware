from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_environment_ontology_dto.environment.environment_config_package import EnvironmentConfigPackage
    from aware_environment_ontology_dto.environment.environment_profile_config import EnvironmentProfileConfig
    from aware_environment_ontology_dto.environment.environment_profile_package_dependency import (
        EnvironmentProfilePackageDependency,
    )
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackage(BaseModel):
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
