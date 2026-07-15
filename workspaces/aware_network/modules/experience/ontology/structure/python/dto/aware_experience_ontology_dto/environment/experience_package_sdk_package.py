from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_sdk_ontology_dto.sdk.sdk_package import SdkPackage


class ExperiencePackageSdkPackage(BaseModel):
    # Relationships
    sdk_package: SdkPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
