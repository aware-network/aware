from __future__ import annotations

# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
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


class PriceReservation(ORMModel):
    # Attributes
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    reservation_key: str
    reserved_at: datetime
    status: PriceReservationStatus = Field(default=PriceReservationStatus.reserved)

    # Foreign Keys
    rate_snapshot_id: UUID = Field(description="Foreign key for RateSnapshot.price_reservations")

    async def set_status(
        self,
        status: PriceReservationStatus,
        final_amount: Annotated[Decimal, DecimalWire()] | None = None,
        actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = None,
        actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = None,
        meter_evidence_ref: str | None = None,
    ) -> PriceReservation:
        """
        Updates one price reservation lifecycle status and optional settled amount.

        Receipt: PriceReservation status/final amount and actual metering transition.
        """

        payload = {
            "status": status,
            "final_amount": final_amount,
            "actual_cost_basis_amount": actual_cost_basis_amount,
            "actual_markup_amount": actual_markup_amount,
            "meter_evidence_ref": meter_evidence_ref,
        }
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PriceReservation):
            return value
        return PriceReservation.validate_invocation_value(value)

    @classmethod
    async def build_via_rate_snapshot(
        cls,
        rate_snapshot_id: UUID,
        reservation_key: str,
        reserved_at: datetime,
        additional_metadata: JsonObject | None = {},
        status: PriceReservationStatus = PriceReservationStatus.reserved,
    ) -> PriceReservation:
        """
        Creates one Economy-owned price reservation receipt under a RateSnapshot.

        Receipt: PriceReservation(status=reserved) linked to the authoritative quoted RateSnapshot.
        """

        payload = {
            "rate_snapshot_id": rate_snapshot_id,
            "reservation_key": reservation_key,
            "reserved_at": reserved_at,
            "additional_metadata": additional_metadata,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_rate_snapshot", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, PriceReservation):
            return value
        return PriceReservation.validate_invocation_value(value)


class PriceReservationSetStatusInput(BaseModel):
    status: PriceReservationStatus
    final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)


class PriceReservationSetStatusOutput(BaseModel):
    value: PriceReservation


class PriceReservationBuildViaRateSnapshotInput(BaseModel):
    rate_snapshot_id: UUID = Field(description="Foreign key for RateSnapshot.price_reservations")
    reservation_key: str
    reserved_at: datetime
    additional_metadata: JsonObject | None = Field(default_factory=JsonObject)
    status: PriceReservationStatus = Field(default=PriceReservationStatus.reserved)


class PriceReservationBuildViaRateSnapshotOutput(BaseModel):
    value: PriceReservation


FUNCTIONS = {
    "PriceReservation": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Updates one price reservation lifecycle status and optional settled amount.\n\nReceipt: PriceReservation status/final amount and actual metering transition.",
                "is_constructor": False,
            },
            "input": PriceReservationSetStatusInput,
            "output": PriceReservationSetStatusOutput,
        },
        "build_via_rate_snapshot": {
            "canonical": {
                "name": "build_via_rate_snapshot",
                "description": "Creates one Economy-owned price reservation receipt under a RateSnapshot.\n\nReceipt: PriceReservation(status=reserved) linked to the authoritative quoted RateSnapshot.",
                "is_constructor": True,
            },
            "input": PriceReservationBuildViaRateSnapshotInput,
            "output": PriceReservationBuildViaRateSnapshotOutput,
        },
    },
}

__all__ = [
    "PriceReservation",
    "PriceReservationSetStatusInput",
    "PriceReservationSetStatusOutput",
    "PriceReservationBuildViaRateSnapshotInput",
    "PriceReservationBuildViaRateSnapshotOutput",
    "FUNCTIONS",
]
