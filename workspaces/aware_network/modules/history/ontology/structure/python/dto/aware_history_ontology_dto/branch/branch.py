from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.lane.lane import Lane
    from aware_history_ontology_dto.version.version import Version


class Branch(BaseModel):
    """Branch is a bundle of lanes."""

    # Relationships
    lanes: list[Lane] = Field(default_factory=list)
    versions: list[Version] = Field(default_factory=list)

    # Attributes
    is_main: bool = Field(default=False)
    key: str = Field(default="default")
    name: str | None = Field(default=None)
