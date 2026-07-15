from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_profile_package import EnvironmentProfilePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class EnvironmentProfilePackageDependency(BaseModel):
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
        default=None, description="Reverse view for EnvironmentProfilePackage.dependencies"
    )

    # Attributes
    description: str | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    target_package_name: str
    target_version_number: int | None = Field(default=None)
