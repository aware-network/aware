from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.process.process_config import ProcessConfig
    from aware_experience_ontology_dto.environment.environment_topology_thread_seed import EnvironmentTopologyThreadSeed


class EnvironmentTopologyProcessSeed(BaseModel):
    """Runtime Process seed inside an EnvironmentTopologySeed."""

    # Relationships
    process_config: ProcessConfig | None = Field(default=None)
    thread_seeds: list[EnvironmentTopologyThreadSeed] = Field(default_factory=list)

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
