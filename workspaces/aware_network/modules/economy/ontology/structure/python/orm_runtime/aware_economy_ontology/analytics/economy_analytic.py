from __future__ import annotations

# Standard
from decimal import Decimal
from typing import (
    Annotated,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import DecimalWire

if TYPE_CHECKING:
    from aware_economy_ontology.analytics.economy_analytic_execution import EconomyAnalyticExecution
    from aware_economy_ontology.analytics.economy_analytic_metric import EconomyAnalyticMetric


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

    @classmethod
    async def build(cls, key: str = "default", analytic_id: UUID | None = None) -> EconomyAnalytic:
        """
        Creates an Economy-owned analytic container.

        If `analytic_id` is provided, it is used as the object id to support idempotent callers
        that derive stable ids from Economy service roots.
        """

        payload = {"key": key, "analytic_id": analytic_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EconomyAnalytic):
            return value
        return EconomyAnalytic.validate_invocation_value(value)


class EconomyAnalyticBuildInput(BaseModel):
    key: str = Field(default="default")
    analytic_id: UUID | None = Field(default=None)


class EconomyAnalyticBuildOutput(BaseModel):
    value: EconomyAnalytic


FUNCTIONS = {
    "EconomyAnalytic": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates an Economy-owned analytic container.\n\nIf `analytic_id` is provided, it is used as the object id to support idempotent callers\nthat derive stable ids from Economy service roots.",
                "is_constructor": True,
            },
            "input": EconomyAnalyticBuildInput,
            "output": EconomyAnalyticBuildOutput,
        },
    },
}

__all__ = [
    "EconomyAnalytic",
    "EconomyAnalyticBuildInput",
    "EconomyAnalyticBuildOutput",
    "FUNCTIONS",
]
