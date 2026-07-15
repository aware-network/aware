from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.section.section_focus_scope import SectionFocusScope


class Section(ORMModel):
    """Declarative "representation unit" as section for Attention contract via FocusScope."""

    # Relationships
    focus_scopes: list[SectionFocusScope] = Field(default_factory=list, exclude=True)
    active_focus_scope: SectionFocusScope | None = Field(default=None, exclude=True)

    # Attributes
    key: str
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    active_focus_scope_id: UUID | None = Field(default=None, description="Foreign key for Section.active_focus_scope")
