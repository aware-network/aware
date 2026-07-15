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
    from aware_storage_ontology_dto.blob.storage_blob import StorageBlob


class ProcessConfig(BaseModel):
    """
    Environment-owned process topology config.
    Contract:
    - Owned by Environment under EnvironmentProfileConfig.
    - Reusable key/config for runtime Process instances.
    - Does not reference Experience-owned profile/config classes.
    """

    # Relationships
    thread_configs: list[ThreadConfig] = Field(default_factory=list)
    image: StorageBlob | None = Field(
        default=None,
        description="Optional profile-level image used as the default for Process instances.\nContract:\n- Image bytes are uploaded out-of-band (data-plane).\n- Commits reference StorageBlob metadata only.",
    )

    # Attributes
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None, description="Narrative text for this continuous process topology.")
    intent: str | None = Field(
        default=None, description="Short canonical intent for process routing and UX composition."
    )
    key: str = Field(description="Stable topology key for this process config.")
    shape: str | None = Field(default=None, description="Optional shape hint for process replication variants.")
    title: str | None = Field(default=None, description="Display label override for desktop surfaces.")
    type: str
    position: int | None = Field(default=None, description="Ordering hint for selectors/home cards.")
    is_default: bool = Field(
        default=False, description="Profile-level default process option for Environment session entrypoints."
    )
