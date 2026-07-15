from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class PricingPolicy(ORMModel):
    # Attributes
    description: str | None = Field(default=None)
    fail_closed: bool = Field(default=True)
    name: str
    policy_json: JsonObject = Field(default_factory=JsonObject)
    version: int = Field(default=1)
