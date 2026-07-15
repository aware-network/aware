from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class InterfaceMountStatusViewStateV1(BaseModel):
    """
    API-owned view-state contract for Interface package mount readiness.
    Public API view key: interface.package_mount_status
    """

    # Attributes
    mounted: bool = Field(default=False)
    ready: bool = Field(default=False)
    status: str = Field(default="unknown")
    summary: str | None = Field(default=None)
    error: str | None = Field(default=None)
    active_layout_key: str | None = Field(default=None)
    active_section_key: str | None = Field(default=None)
