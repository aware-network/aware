from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.analytics.economy_analytic_execution_metric import EconomyAnalyticExecutionMetric
    from aware_economy_ontology.analytics.economy_analytic_metric import EconomyAnalyticMetric


class EconomyAnalyticExecution(ORMModel):
    # Attributes
    cost_base_amount: Annotated[Decimal, DecimalWire()]
    cost_final_amount: Annotated[Decimal, DecimalWire()]
    end_time: datetime
    key: str = Field(default="default")
    start_time: datetime
    success: bool

    # Foreign Keys
    economy_analytic_id: UUID = Field(description="Foreign key for EconomyAnalytic.analytic_executions")

    # Edges
    economy_analytic_execution_metrics: list[EconomyAnalyticExecutionMetric] = Field(
        default_factory=list, exclude=True, description="Edge association helper for analytic_metrics"
    )

    @property
    def analytic_metrics(self) -> list[EconomyAnalyticMetric]:
        return [
            edge.economy_analytic_metric
            for edge in self.economy_analytic_execution_metrics
            if edge.economy_analytic_metric is not None
        ]


FUNCTIONS = {
    "EconomyAnalyticExecution": {},
}

__all__ = [
    "EconomyAnalyticExecution",
    "FUNCTIONS",
]
