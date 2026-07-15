from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class RenderComponentInputPort(BaseModel):
    # Attributes
    port_key: str
    value_kind: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)
