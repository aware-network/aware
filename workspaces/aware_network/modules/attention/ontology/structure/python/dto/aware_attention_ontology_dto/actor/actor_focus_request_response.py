from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ActorFocusRequestResponse(BaseModel):
    """Separate from ActorFocusRequest to ensure provenance on result standalone."""

    # Attributes
    key: str = Field(default="default")
    success: bool
    message: str | None = Field(default=None)
