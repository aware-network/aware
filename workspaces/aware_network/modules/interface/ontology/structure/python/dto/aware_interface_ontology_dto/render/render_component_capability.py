from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class RenderComponentCapability(BaseModel):
    # Attributes
    capability_kind: str
    capability_key: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)
