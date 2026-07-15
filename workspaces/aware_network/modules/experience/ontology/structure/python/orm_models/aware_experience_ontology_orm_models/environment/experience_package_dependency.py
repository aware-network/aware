from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.experience_package import ExperiencePackage
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperiencePackageDependency(ORMModel):
    """
    Experience package to Experience package dependency bridge.
    The authored `aware.experience.toml` dependency row is selector truth. The
    resolved OIG commit pin, when present, is exact reproducibility authority for
    WorkspaceRevision/Hub consumers and cross-Experience transition linking.
    """

    # Relationships
    target_experience_package: ExperiencePackage | None = Field(default=None)
    target_experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    target_package_name: str
    target_version_number: int | None = Field(default=None)
    expected_hash_sha256: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.experience_package_dependencies")
    target_experience_package_id: UUID = Field(
        description="Foreign key for ExperiencePackageDependency.target_experience_package"
    )
    target_experience_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for ExperiencePackageDependency.target_experience_package_object_instance_graph_commit",
    )
