from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.lane.lane import Lane
    from aware_history_ontology_orm_models.version.version import Version


class Branch(ORMModel):
    """Branch is a bundle of lanes."""

    # Relationships
    lanes: list[Lane] = Field(default_factory=list, exclude=True)
    versions: list[Version] = Field(default_factory=list, exclude=True)

    # Attributes
    is_main: bool = Field(default=False)
    key: str = Field(default="default")
    name: str | None = Field(default=None)
