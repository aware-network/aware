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


class InterfacePackageExperiencePackage(ORMModel):
    # Relationships
    experience_package: ExperiencePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    interface_package_id: UUID = Field(description="Foreign key for InterfacePackage.experience_packages")
    experience_package_id: UUID = Field(
        description="Foreign key for InterfacePackageExperiencePackage.experience_package"
    )
