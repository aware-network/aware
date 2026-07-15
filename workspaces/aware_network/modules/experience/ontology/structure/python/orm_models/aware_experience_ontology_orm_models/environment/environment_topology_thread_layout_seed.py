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


class EnvironmentTopologyThreadLayoutSeed(ORMModel):
    """Runtime ThreadLayout seed inside an EnvironmentTopologyThreadSeed."""

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None, exclude=True)

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

    # Foreign Keys
    environment_topology_thread_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyThreadSeed.layout_seeds"
    )
    layout_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyThreadLayoutSeed.layout_config")
