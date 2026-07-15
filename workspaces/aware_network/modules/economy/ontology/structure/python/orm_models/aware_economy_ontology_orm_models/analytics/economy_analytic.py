from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_orm_models.analytics.economy_analytic_execution import EconomyAnalyticExecution
    from aware_economy_ontology_orm_models.analytics.economy_analytic_metric import EconomyAnalyticMetric


class EconomyAnalytic(ORMModel):
    # Relationships
    analytic_executions: list[EconomyAnalyticExecution] = Field(default_factory=list, exclude=True)
    analytic_metrics: list[EconomyAnalyticMetric] = Field(default_factory=list, exclude=True)

    # Attributes
    average_cost_base_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=Decimal("0"))
    average_cost_final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=Decimal("0"))
    average_duration: float | None = Field(default=0.0)
    failure_count: int | None = Field(default=0)
    key: str = Field(default="default")
    success_count: int | None = Field(default=0)
    success_rate: float | None = Field(default=0.0)
