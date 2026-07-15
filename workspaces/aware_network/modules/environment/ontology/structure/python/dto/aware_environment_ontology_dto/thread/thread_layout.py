from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout import Layout


class ThreadLayout(BaseModel):
    """
    Deterministic Thread -> Attention Layout association edge.
    Contract:
    - Canonical portal from environment thread context to attention layout topology.
    - Thread remains narrative/layout-management context; attention owns section/focus truth.
    """

    # Relationships
    layout: Layout | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None, description="Stable association key under a Thread for layout attachments.")
