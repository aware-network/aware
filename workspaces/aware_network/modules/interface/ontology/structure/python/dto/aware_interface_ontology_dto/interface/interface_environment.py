from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment import Environment


class InterfaceEnvironment(BaseModel):
    """
    Interface-owned Environment access contract.
    Contract:
    - This is the canonical commit-backed fact that an Interface can resolve against an Environment.
    - Window/thread targeting must route through this association instead of letting windows grant
    Environment access directly.
    """

    # Relationships
    environment: Environment | None = Field(default=None)
