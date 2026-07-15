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


class AppPackageExperiencePackage(ORMModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)
    experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    role: str = Field(default="experience")

    # Foreign Keys
    app_package_id: UUID = Field(description="Foreign key for AppPackage.experience_packages")
    experience_package_id: UUID = Field(description="Foreign key for AppPackageExperiencePackage.experience_package")
    experience_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None,
        description="Foreign key for AppPackageExperiencePackage.experience_package_object_instance_graph_commit",
    )
