from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology.content.content import Content


class MemoryProcedureConfig(ORMModel):
    # Relationships
    content: Content | None = Field(default=None, exclude=True)

    # Attributes
    title: str
    description: str

    # Foreign Keys
    content_id: UUID = Field(description="Foreign key for MemoryProcedureConfig.content")


FUNCTIONS = {
    "MemoryProcedureConfig": {},
}

__all__ = [
    "MemoryProcedureConfig",
    "FUNCTIONS",
]
