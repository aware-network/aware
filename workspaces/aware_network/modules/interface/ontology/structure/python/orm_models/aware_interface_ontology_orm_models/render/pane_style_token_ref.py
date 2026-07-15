from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class PaneStyleTokenRef(ORMModel):
    # Attributes
    token_key: str
    token_value: str | None = Field(default=None)

    # Foreign Keys
    pane_render_node_id: UUID = Field(description="Foreign key for PaneRenderNode.style_tokens")
