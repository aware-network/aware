from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkDirectory(BaseModel):
    # Attributes
    name: str = Field(default="default")
