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
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus

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
    from aware_economy_ontology.price.price_reservation import PriceReservation


class RateSnapshot(ORMModel):
    # Relationships
    price_reservations: list[PriceReservation] = Field(default_factory=list, exclude=True)

    # Attributes
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    captured_at: datetime
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    quoted_amount: Annotated[Decimal, DecimalWire()]
    snapshot_key: str

    # Foreign Keys
    price_schedule_id: UUID = Field(description="Foreign key for PriceSchedule.rate_snapshots")

    async def create_price_reservation(
        self,
        reservation_key: str,
        reserved_at: datetime,
        additional_metadata: JsonObject | None = {},
        status: PriceReservationStatus = PriceReservationStatus.reserved,
    ) -> PriceReservation:
        """
        Creates one canonical reservation receipt under this RateSnapshot.

        Receipt: PriceReservation(status=reserved) linked to this RateSnapshot.
        """

        payload = {
            "reservation_key": reservation_key,
            "reserved_at": reserved_at,
            "additional_metadata": additional_metadata,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="create_price_reservation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_economy_ontology.price.price_reservation import PriceReservation

        if isinstance(value, PriceReservation):
            return value
        return PriceReservation.validate_invocation_value(value)

    @classmethod
    async def build_via_price_schedule(
        cls,
        price_schedule_id: UUID,
        snapshot_key: str,
        quoted_amount: Annotated[Decimal, DecimalWire()],
        captured_at: datetime,
        cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = None,
        markup_percentage: Annotated[Decimal, DecimalWire()] | None = None,
        markup_amount: Annotated[Decimal, DecimalWire()] | None = None,
        meter_evidence_ref: str | None = None,
        additional_metadata: JsonObject | None = {},
    ) -> RateSnapshot:
        """Creates one immutable snapshot under a PriceSchedule."""

        payload = {
            "price_schedule_id": price_schedule_id,
            "snapshot_key": snapshot_key,
            "quoted_amount": quoted_amount,
            "captured_at": captured_at,
            "cost_basis_amount": cost_basis_amount,
            "markup_percentage": markup_percentage,
            "markup_amount": markup_amount,
            "meter_evidence_ref": meter_evidence_ref,
            "additional_metadata": additional_metadata,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_price_schedule", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RateSnapshot):
            return value
        return RateSnapshot.validate_invocation_value(value)


class RateSnapshotCreatePriceReservationInput(BaseModel):
    reservation_key: str
    reserved_at: datetime
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    status: PriceReservationStatus = Field(default=PriceReservationStatus.reserved)


class RateSnapshotCreatePriceReservationOutput(BaseModel):
    value: PriceReservation


class RateSnapshotBuildViaPriceScheduleInput(BaseModel):
    price_schedule_id: UUID = Field(description="Foreign key for PriceSchedule.rate_snapshots")
    snapshot_key: str
    quoted_amount: Annotated[Decimal, DecimalWire()]
    captured_at: datetime
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)


class RateSnapshotBuildViaPriceScheduleOutput(BaseModel):
    value: RateSnapshot


FUNCTIONS = {
    "RateSnapshot": {
        "create_price_reservation": {
            "canonical": {
                "name": "create_price_reservation",
                "description": "Creates one canonical reservation receipt under this RateSnapshot.\n\nReceipt: PriceReservation(status=reserved) linked to this RateSnapshot.",
                "is_constructor": False,
            },
            "input": RateSnapshotCreatePriceReservationInput,
            "output": RateSnapshotCreatePriceReservationOutput,
        },
        "build_via_price_schedule": {
            "canonical": {
                "name": "build_via_price_schedule",
                "description": "Creates one immutable snapshot under a PriceSchedule.",
                "is_constructor": True,
            },
            "input": RateSnapshotBuildViaPriceScheduleInput,
            "output": RateSnapshotBuildViaPriceScheduleOutput,
        },
    },
}

__all__ = [
    "RateSnapshot",
    "RateSnapshotCreatePriceReservationInput",
    "RateSnapshotCreatePriceReservationOutput",
    "RateSnapshotBuildViaPriceScheduleInput",
    "RateSnapshotBuildViaPriceScheduleOutput",
    "FUNCTIONS",
]
