from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class NetworkNodeSessionStatusViewStateV1(BaseModel):
    """
    API-owned view-state contract for NetworkNode session readiness.
    Public API view key: network.session_status
    """

    # Attributes
    managed: bool = Field(default=False)
    available: bool = Field(default=False)
    ready: bool = Field(default=False)
    phase: str = Field(default="idle")
    active_target_id: str | None = Field(default=None)
    target_key: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    backend_kind: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    recent_log_lines: list[str] = Field(default_factory=list)
    target_statuses: list[JsonObject] = Field(default_factory=list)
