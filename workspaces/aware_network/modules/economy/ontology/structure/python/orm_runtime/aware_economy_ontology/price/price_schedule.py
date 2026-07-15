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
    from aware_economy_ontology.price.pricing_policy import PricingPolicy
    from aware_economy_ontology.price.rate_snapshot import RateSnapshot


class PriceSchedule(ORMModel):
    # Relationships
    pricing_policy: PricingPolicy | None = Field(default=None, exclude=True)
    rate_snapshots: list[RateSnapshot] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    effective_from: datetime
    effective_until: datetime | None = Field(default=None)
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    name: str
    version: int = Field(default=1)

    # Foreign Keys
    price_id: UUID = Field(description="Foreign key for Price.price_schedules")
    pricing_policy_id: UUID = Field(description="Foreign key for PriceSchedule.pricing_policy")

    async def capture_rate_snapshot(
        self,
        snapshot_key: str,
        quoted_amount: Annotated[Decimal, DecimalWire()],
        captured_at: datetime,
        cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = None,
        markup_percentage: Annotated[Decimal, DecimalWire()] | None = None,
        markup_amount: Annotated[Decimal, DecimalWire()] | None = None,
        meter_evidence_ref: str | None = None,
        additional_metadata: JsonObject | None = {},
    ) -> RateSnapshot:
        """
        Captures one immutable pricing snapshot under this schedule.

        Receipt: RateSnapshot linked to this PriceSchedule.
        """

        payload = {
            "snapshot_key": snapshot_key,
            "quoted_amount": quoted_amount,
            "captured_at": captured_at,
            "cost_basis_amount": cost_basis_amount,
            "markup_percentage": markup_percentage,
            "markup_amount": markup_amount,
            "meter_evidence_ref": meter_evidence_ref,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_instance(orm_model=self, function_name="capture_rate_snapshot", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.price.rate_snapshot import RateSnapshot

        if isinstance(value, RateSnapshot):
            return value
        return RateSnapshot.validate_invocation_value(value)

    @classmethod
    async def build_via_price(
        cls,
        price_id: UUID,
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
        Creates one schedule under a Price.

        Receipt: PriceSchedule linked to Price + PricingPolicy with a validity window.
        """

        payload = {
            "price_id": price_id,
            "pricing_policy_id": pricing_policy_id,
            "name": name,
            "effective_from": effective_from,
            "version": version,
            "effective_until": effective_until,
            "fixed_amount": fixed_amount,
            "markup_percentage": markup_percentage,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_price", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PriceSchedule):
            return value
        return PriceSchedule.validate_invocation_value(value)


class PriceScheduleCaptureRateSnapshotInput(BaseModel):
    snapshot_key: str
    quoted_amount: Annotated[Decimal, DecimalWire()]
    captured_at: datetime
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class PriceScheduleCaptureRateSnapshotOutput(BaseModel):
    value: RateSnapshot


class PriceScheduleBuildViaPriceInput(BaseModel):
    price_id: UUID = Field(description="Foreign key for Price.price_schedules")
    pricing_policy_id: UUID
    name: str
    effective_from: datetime
    version: int = Field(default=1)
    effective_until: datetime | None = Field(default=None)
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class PriceScheduleBuildViaPriceOutput(BaseModel):
    value: PriceSchedule


FUNCTIONS = {
    "PriceSchedule": {
        "capture_rate_snapshot": {
            "canonical": {
                "name": "capture_rate_snapshot",
                "description": "Captures one immutable pricing snapshot under this schedule.\n\nReceipt: RateSnapshot linked to this PriceSchedule.",
                "is_constructor": False,
            },
            "input": PriceScheduleCaptureRateSnapshotInput,
            "output": PriceScheduleCaptureRateSnapshotOutput,
        },
        "build_via_price": {
            "canonical": {
                "name": "build_via_price",
                "description": "Creates one schedule under a Price.\n\nReceipt: PriceSchedule linked to Price + PricingPolicy with a validity window.",
                "is_constructor": True,
            },
            "input": PriceScheduleBuildViaPriceInput,
            "output": PriceScheduleBuildViaPriceOutput,
        },
    },
}

__all__ = [
    "PriceSchedule",
    "PriceScheduleCaptureRateSnapshotInput",
    "PriceScheduleCaptureRateSnapshotOutput",
    "PriceScheduleBuildViaPriceInput",
    "PriceScheduleBuildViaPriceOutput",
    "FUNCTIONS",
]
