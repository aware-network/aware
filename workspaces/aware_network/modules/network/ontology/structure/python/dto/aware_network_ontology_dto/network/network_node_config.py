from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkNodeConfig(BaseModel):
    # Attributes
    name: str
    description: str | None = Field(default=None)
