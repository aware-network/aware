from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.environment.environment import Environment


class InterfaceEnvironment(ORMModel):
    """
    Interface-owned Environment access contract.
    Contract:
    - This is the canonical commit-backed fact that an Interface can resolve against an Environment.
    - Window/thread targeting must route through this association instead of letting windows grant
    Environment access directly.
    """

    # Relationships
    environment: Environment | None = Field(default=None, exclude=True)

    # Foreign Keys
    interface_id: UUID = Field(description="Foreign key for Interface.environments")
    environment_id: UUID = Field(description="Foreign key for InterfaceEnvironment.environment")
