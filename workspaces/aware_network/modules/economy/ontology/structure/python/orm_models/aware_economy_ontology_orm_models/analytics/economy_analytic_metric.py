from __future__ import annotations

# Standard
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire


class EconomyAnalyticMetric(ORMModel):
    # Attributes
    cost_per_unit: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    unit: str

    # Foreign Keys
    economy_analytic_id: UUID = Field(description="Foreign key for EconomyAnalytic.analytic_metrics")
