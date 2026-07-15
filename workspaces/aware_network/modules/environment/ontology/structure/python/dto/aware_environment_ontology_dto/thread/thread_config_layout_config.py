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
    from aware_environment_ontology_dto.thread.thread_config_layout_config_section import (
        ThreadConfigLayoutConfigSection,
    )


class ThreadConfigLayoutConfig(BaseModel):
    """
    Deterministic ThreadConfig -> Attention LayoutConfig association edge.
    Contract:
    - ThreadConfig is the Environment-owned availability source.
    - LayoutConfig is Attention-owned topology config.
    - Runtime provisioning lowers this edge into Thread -> ThreadLayout -> Layout.
    """

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)
    sections: list[ThreadConfigLayoutConfigSection] = Field(default_factory=list)

    # Attributes
    key: str | None = Field(default=None, description="Optional stable association key under the parent ThreadConfig.")
    position: int | None = Field(default=None, description="Ordering hint for thread layout selectors.")
    narrative: str | None = Field(default=None, description="Narrative text for why this layout belongs to the thread.")
    intent: str | None = Field(default=None, description="Short canonical intent for the layout option.")
