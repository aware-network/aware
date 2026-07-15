from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout import Layout


class ThreadLayout(ORMModel):
    """
    Deterministic Thread -> Attention Layout association edge.
    Contract:
    - Canonical portal from environment thread context to attention layout topology.
    - Thread remains narrative/layout-management context; attention owns section/focus truth.
    """

    # Relationships
    layout: Layout | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None, description="Stable association key under a Thread for layout attachments.")

    # Foreign Keys
    thread_id: UUID = Field(description="Foreign key for Thread.thread_layouts")
    layout_id: UUID = Field(description="Foreign key for ThreadLayout.layout")
