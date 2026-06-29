from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import Vector


class ContentIndex(BaseModel):
    # Attributes
    key: str = Field(default="default")
    content_embedding: Vector | None = Field(default=None)
