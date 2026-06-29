from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_package import ApiPackage


class SdkPackageApiPackage(BaseModel):
    # Relationships
    api_package: ApiPackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
