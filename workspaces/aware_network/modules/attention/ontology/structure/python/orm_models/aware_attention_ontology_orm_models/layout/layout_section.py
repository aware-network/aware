from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.section.section import Section


class LayoutSection(ORMModel):
    """Canonical section geometry/visibility entry inside a Layout."""

    # Relationships
    section: Section | None = Field(default=None, exclude=True)

    # Attributes
    order: int = Field(default=0)
    flex: float = Field(default=1.0)
    is_visible: bool = Field(default=True)

    # Foreign Keys
    layout_id: UUID = Field(description="Foreign key for Layout.sections")
    section_id: UUID = Field(description="Foreign key for LayoutSection.section")
