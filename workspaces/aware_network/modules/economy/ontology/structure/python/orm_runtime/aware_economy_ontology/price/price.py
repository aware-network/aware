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
from pydantic import (
    BaseModel,
    Field,
)

# Economy Ontology
from aware_economy_ontology.price.price_enums import PriceType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)

if TYPE_CHECKING:
    from aware_economy_ontology.coin.coin import Coin
    from aware_economy_ontology.price.price_schedule import PriceSchedule


class Price(ORMModel):
    # Relationships
    coin: Coin | None = Field(default=None, exclude=True)
    price_schedules: list[PriceSchedule] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    name: str
    type: PriceType

    # Foreign Keys
    coin_id: UUID = Field(description="Foreign key for Price.coin")

    @classmethod
    async def build(
        cls, coin_id: UUID, name: str, type: PriceType, additional_metadata: JsonObject | None = {}
    ) -> Price:
        """
        Creates one Economy-owned price primitive.

        Receipt: Price linked to Coin as a stable pricing family root.
        """

        payload = {"coin_id": coin_id, "name": name, "type": type, "additional_metadata": additional_metadata}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Price):
            return value
        return Price.validate_invocation_value(value)

    async def create_price_schedule(
        self,
        pricing_policy_id: UUID,
        name: str,
        effective_from: datetime,
        version: int = 1,
        effective_until: datetime | None = None,
        fixed_amount: Annotated[Decimal, DecimalWire()] | None = None,
        markup_percentage: Annotated[Decimal, DecimalWire()] | None = None,
        additional_metadata: JsonObject | None = {},
    ) -> PriceSchedule:
        """
        Creates one schedule under this Price.

        Receipt: PriceSchedule linked to this Price and the referenced PricingPolicy.
        """

        payload = {
            "pricing_policy_id": pricing_policy_id,
            "name": name,
            "effective_from": effective_from,
            "version": version,
            "effective_until": effective_until,
            "fixed_amount": fixed_amount,
            "markup_percentage": markup_percentage,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="create_price_schedule", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.price.price_schedule import PriceSchedule

        if isinstance(value, PriceSchedule):
            return value
        return PriceSchedule.validate_invocation_value(value)


class PriceBuildInput(BaseModel):
    coin_id: UUID
    name: str
    type: PriceType
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class PriceBuildOutput(BaseModel):
    value: Price


class PriceCreatePriceScheduleInput(BaseModel):
    pricing_policy_id: UUID
    name: str
    effective_from: datetime
    version: int = Field(default=1)
    effective_until: datetime | None = Field(default=None)
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class PriceCreatePriceScheduleOutput(BaseModel):
    value: PriceSchedule


FUNCTIONS = {
    "Price": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Creates one Economy-owned price primitive.\n\nReceipt: Price linked to Coin as a stable pricing family root.",
                "is_constructor": True,
            },
            "input": PriceBuildInput,
            "output": PriceBuildOutput,
        },
        "create_price_schedule": {
            "canonical": {
                "name": "create_price_schedule",
                "description": "Creates one schedule under this Price.\n\nReceipt: PriceSchedule linked to this Price and the referenced PricingPolicy.",
                "is_constructor": False,
            },
            "input": PriceCreatePriceScheduleInput,
            "output": PriceCreatePriceScheduleOutput,
        },
    },
}

__all__ = [
    "Price",
    "PriceBuildInput",
    "PriceBuildOutput",
    "PriceCreatePriceScheduleInput",
    "PriceCreatePriceScheduleOutput",
    "FUNCTIONS",
]
