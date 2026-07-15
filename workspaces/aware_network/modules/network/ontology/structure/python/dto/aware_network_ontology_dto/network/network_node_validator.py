from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkNodeValidator(BaseModel):
    # Attributes
    public_key: str
    reliability: float = Field(default=1.0)
    stake: float = Field(default=0)
