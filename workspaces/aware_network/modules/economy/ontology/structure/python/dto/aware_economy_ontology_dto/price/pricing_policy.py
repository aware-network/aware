from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class PricingPolicy(BaseModel):
    # Attributes
    description: str | None = Field(default=None)
    fail_closed: bool = Field(default=True)
    name: str
    policy_json: JsonObject = Field(default_factory=JsonObject)
    version: int = Field(default=1)
