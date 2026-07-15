from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import Vector


class ContentPartTextIndex(BaseModel):
    # Attributes
    key: str = Field(default="default")
    embedding: Vector | None = Field(default=None)
