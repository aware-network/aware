from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_package import ApiPackage


class SkillPackageApiPackage(ORMModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_package_id: UUID = Field(description="Foreign key for SkillPackage.api_packages")
    api_package_id: UUID = Field(description="Foreign key for SkillPackageApiPackage.api_package")
