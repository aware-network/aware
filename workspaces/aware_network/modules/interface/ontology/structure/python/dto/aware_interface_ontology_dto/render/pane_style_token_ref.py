from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class PaneStyleTokenRef(BaseModel):
    # Attributes
    token_key: str
    token_value: str | None = Field(default=None)
