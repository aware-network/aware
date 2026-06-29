from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import Vector


class ContentPartMultimodalIndex(ORMModel):
    # Attributes
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)

    # Foreign Keys
    content_part_id: UUID | None = Field(
        default=None, description="Foreign key for ContentPart.content_part_multimodal_index"
    )
