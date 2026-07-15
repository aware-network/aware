from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage


class EconomyPackage(BaseModel):
    # Relationships
    source_code_package: CodePackage | None = Field(default=None)

    # Attributes
    name: str
