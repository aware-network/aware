from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.identity.identity import Identity


class MemorySemantic(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    key: str = Field(default="default")

    # Foreign Keys
    identity_id: UUID = Field(description="Foreign key for MemorySemantic.identity")
