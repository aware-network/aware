from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment_profile_package import EnvironmentProfilePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackageDependency(ORMModel):
    """
    Direct dependency from one EnvironmentProfilePackage to another.
    This models reusable OS profile package composition as Environment semantic
    package truth. It is separate from concrete EnvironmentProfile session links.
    """

    # Relationships
    target_environment_profile_package: EnvironmentProfilePackage | None = Field(default=None)
    target_environment_profile_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(
        default=None
    )
    environment_profile_package: EnvironmentProfilePackage | None = Field(
        default=None, exclude=True, description="Reverse view for EnvironmentProfilePackage.dependencies"
    )

    # Attributes
    description: str | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    target_package_name: str
    target_version_number: int | None = Field(default=None)

    # Foreign Keys
    environment_profile_package_id: UUID = Field(description="Foreign key for EnvironmentProfilePackage.dependencies")
    target_environment_profile_package_id: UUID = Field(
        description="Foreign key for EnvironmentProfilePackageDependency.target_environment_profile_package"
    )
    target_environment_profile_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentProfilePackageDependency.target_environment_profile_package_object_instance_graph_commit",
    )
