from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_economy_ontology.analytics.economy_analytic_metric import EconomyAnalyticMetric


class EconomyAnalyticExecutionMetric(ORMModel):
    # Relationships
    economy_analytic_metric: EconomyAnalyticMetric | None = Field(
        default=None, exclude=True, description="Association target reference to EconomyAnalyticMetric"
    )

    # Attributes
    key: str = Field(default="default")
    quantity: float

    # Foreign Keys
    economy_analytic_metric_id: UUID = Field(description="Join FK to EconomyAnalyticMetric")
    economy_analytic_execution_id: UUID = Field(description="Join FK to EconomyAnalyticExecution")


FUNCTIONS = {
    "EconomyAnalyticExecutionMetric": {},
}

__all__ = [
    "EconomyAnalyticExecutionMetric",
    "FUNCTIONS",
]
