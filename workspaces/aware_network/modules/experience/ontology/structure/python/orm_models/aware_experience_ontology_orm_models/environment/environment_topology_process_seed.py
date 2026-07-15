from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_environment_ontology_orm_models.process.process_config import ProcessConfig
    from aware_experience_ontology_orm_models.environment.environment_topology_thread_seed import (
        EnvironmentTopologyThreadSeed,
    )


class EnvironmentTopologyProcessSeed(ORMModel):
    """Runtime Process seed inside an EnvironmentTopologySeed."""

    # Relationships
    process_config: ProcessConfig | None = Field(default=None, exclude=True)
    thread_seeds: list[EnvironmentTopologyThreadSeed] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)
    key: str | None = Field(
        default=None, description="Optional seed-local key; defaults to `process_key` in runtime handlers."
    )
    process_key: str = Field(description="Runtime Process.key to create or resolve under Environment.")
    position: int | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    title: str | None = Field(default=None)

    # Foreign Keys
    environment_topology_seed_id: UUID = Field(description="Foreign key for EnvironmentTopologySeed.process_seeds")
    process_config_id: UUID = Field(description="Foreign key for EnvironmentTopologyProcessSeed.process_config")
