from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_config import LayoutConfig


class EnvironmentTopologyThreadLayoutSeed(BaseModel):
    """Runtime ThreadLayout seed inside an EnvironmentTopologyThreadSeed."""

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)

    # Attributes
    key: str | None = Field(
        default=None, description="Optional layout seed key; defaults to the LayoutConfig key when omitted."
    )
    position: int | None = Field(default=None)
    activate_on_seed: bool = Field(
        default=False, description="Whether provisioning should set this layout active for the runtime Thread."
    )
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
