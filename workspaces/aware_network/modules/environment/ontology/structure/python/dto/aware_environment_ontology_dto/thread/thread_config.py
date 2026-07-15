from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.thread.thread_config_layout_config import ThreadConfigLayoutConfig
    from aware_environment_ontology_dto.thread.thread_config_object_projection_graph import (
        ThreadConfigObjectProjectionGraph,
    )
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ThreadConfig(BaseModel):
    """
    Environment-owned contextual Thread topology config.
    Contract:
    - Owned by Environment under ProcessConfig.
    - Reusable key/config for runtime Thread instances.
    - Hosts projection graph authority refs and Attention layout configs.
    - Does not reference Experience ProjectionExperience or ProgramConfigGraph.
    """

    # Relationships
    object_projection_graphs: list[ThreadConfigObjectProjectionGraph] = Field(default_factory=list)
    layout_configs: list[ThreadConfigLayoutConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        description="Optional profile-level image used as the default for Thread instances.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(
        default=None, description="Narrative text for this thread context and workspace flow."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for thread-level decision/routing.")
    state_prompt_template: str | None = Field(
        default=None, description="Declarative prompt template anchor for state-aware thread composition."
    )
    key: str = Field(description="Stable key for thread narrative role (e.g. `main.workspace`, `ops.monitor`).")
    title: str | None = Field(default=None, description="Display label override for thread desktop surfaces.")
    workspace_view_key: str | None = Field(default=None, description="Canonical thread workspace view selector.")
    position: int | None = Field(default=None, description="Ordering hint for thread navigation surfaces.")
    is_default: bool = Field(
        default=False, description="Process-level default thread option for Environment session entrypoints."
    )
