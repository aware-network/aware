from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.focus.focus_scope import FocusScope


class SectionFocusScope(ORMModel):
    """FocusScope binding at Section level."""

    # Relationships
    focus_scope: FocusScope | None = Field(default=None, exclude=True)

    # Attributes
    title: str
    description: str | None = Field(default=None)

    # Foreign Keys
    section_id: UUID = Field(description="Foreign key for Section.focus_scopes")
    focus_scope_id: UUID = Field(description="Foreign key for SectionFocusScope.focus_scope")
