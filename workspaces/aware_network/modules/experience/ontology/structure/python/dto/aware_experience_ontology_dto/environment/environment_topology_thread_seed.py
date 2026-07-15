from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.thread.thread_config import ThreadConfig
    from aware_experience_ontology_dto.environment.environment_topology_thread_layout_seed import (
        EnvironmentTopologyThreadLayoutSeed,
    )


class EnvironmentTopologyThreadSeed(BaseModel):
    """Runtime Thread seed inside an EnvironmentTopologyProcessSeed."""

    # Relationships
    thread_config: ThreadConfig | None = Field(default=None)
    layout_seeds: list[EnvironmentTopologyThreadLayoutSeed] = Field(default_factory=list)

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
