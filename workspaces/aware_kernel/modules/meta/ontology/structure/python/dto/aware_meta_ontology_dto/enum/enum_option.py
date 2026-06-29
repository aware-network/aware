from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class EnumOption(BaseModel):
    # Attributes
    value: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)
