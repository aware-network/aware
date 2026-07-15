from __future__ import annotations

# Standard
from decimal import Decimal
from typing import Annotated

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import DecimalWire


class EconomyAnalyticMetric(BaseModel):
    # Attributes
    cost_per_unit: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    unit: str
