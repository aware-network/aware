from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_sdk_ontology_orm_models.sdk.sdk_package import SdkPackage


class ExperiencePackageSdkPackage(ORMModel):
    # Relationships
    sdk_package: SdkPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_package_id: UUID = Field(description="Foreign key for ExperiencePackage.sdk_packages")
    sdk_package_id: UUID = Field(description="Foreign key for ExperiencePackageSdkPackage.sdk_package")
