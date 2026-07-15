from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class HostedInterfaceNamespace(BaseModel):
    """
    Snapshot of one namespace hosted behind the local Interface daemon.
    Transport-only contract:
    - graph/ORM agnostic
    - local-machine scoped
    - safe for renderer and CLI clients
    """

    # Attributes
    namespace: str
    host_label: str
    started: bool
    actor_id: UUID | None = Field(default=None)
    interface_id: UUID | None = Field(default=None)
    interface_session_id: UUID | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_config_id: UUID | None = Field(default=None)
    warnings: list[str] = Field(default_factory=list)
