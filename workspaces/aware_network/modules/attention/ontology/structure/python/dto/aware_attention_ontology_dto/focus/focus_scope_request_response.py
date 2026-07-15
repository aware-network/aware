from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class FocusScopeRequestResponse(BaseModel):
    # Attributes
    success: bool
    message: str | None = Field(default=None)
