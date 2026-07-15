from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.thread.thread_config import ThreadConfig
    from aware_experience_ontology_orm_models.environment.environment_topology_thread_layout_seed import (
        EnvironmentTopologyThreadLayoutSeed,
    )


class EnvironmentTopologyThreadSeed(ORMModel):
    """Runtime Thread seed inside an EnvironmentTopologyProcessSeed."""

    # Relationships
    thread_config: ThreadConfig | None = Field(default=None, exclude=True)
    layout_seeds: list[EnvironmentTopologyThreadLayoutSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    is_main: bool = Field(default=False)
    key: str | None = Field(
        default=None, description="Optional seed-local key; defaults to `thread_key` in runtime handlers."
    )
    thread_key: str = Field(description="Runtime Thread.key to create or resolve under Environment.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_topology_process_seed_id: UUID = Field(
        description="Foreign key for EnvironmentTopologyProcessSeed.thread_seeds"
    )
    thread_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyThreadSeed.thread_config")
