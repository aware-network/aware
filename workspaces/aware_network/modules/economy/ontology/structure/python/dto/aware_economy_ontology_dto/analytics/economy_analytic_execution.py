from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology_dto.analytics.economy_analytic_execution_metric import EconomyAnalyticExecutionMetric
    from aware_economy_ontology_dto.analytics.economy_analytic_metric import EconomyAnalyticMetric


class EconomyAnalyticExecution(BaseModel):
    # Attributes
    cost_base_amount: Annotated[Decimal, DecimalWire()]
    cost_final_amount: Annotated[Decimal, DecimalWire()]
    end_time: datetime
    key: str = Field(default="default")
    start_time: datetime
    success: bool
