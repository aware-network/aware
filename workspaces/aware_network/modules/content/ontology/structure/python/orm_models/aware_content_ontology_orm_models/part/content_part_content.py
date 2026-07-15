from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_content_ontology_orm_models.part.content_part import ContentPart


class ContentPartContent(ORMModel):
    # Relationships
    content_part: ContentPart

    # Attributes
    position: int

    # Foreign Keys
    content_id: UUID = Field(description="Foreign key for Content.content_part_contents")
