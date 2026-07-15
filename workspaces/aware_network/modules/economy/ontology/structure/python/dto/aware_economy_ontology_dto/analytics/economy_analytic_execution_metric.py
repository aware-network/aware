from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_economy_ontology_dto.analytics.economy_analytic_metric import EconomyAnalyticMetric


class EconomyAnalyticExecutionMetric(BaseModel):
    # Relationships
    economy_analytic_metric: EconomyAnalyticMetric | None = Field(
        default=None, description="Association target reference to EconomyAnalyticMetric"
    )

    # Attributes
    key: str = Field(default="default")
    quantity: float
