from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config import LayoutConfig
    from aware_environment_ontology_orm_models.thread.thread_config_layout_config_section import (
        ThreadConfigLayoutConfigSection,
    )


class ThreadConfigLayoutConfig(ORMModel):
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

    # Foreign Keys
    thread_config_id: UUID = Field(description="Foreign key for ThreadConfig.layout_configs")
    layout_config_id: UUID = Field(description="Foreign key for ThreadConfigLayoutConfig.layout_config")
