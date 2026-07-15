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


class PanePackageExperiencePackage(BaseModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
