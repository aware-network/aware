from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.experience_package import ExperiencePackage
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class AppPackageExperiencePackage(BaseModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)
    experience_package_object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    role: str = Field(default="experience")
