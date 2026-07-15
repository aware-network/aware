from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Economy Ontology
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus
from aware_economy_ontology.price.price_reservation import PriceReservation
from aware_economy_ontology.price.rate_snapshot import RateSnapshot

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Economy Runtime
from aware_economy.capital_amount import non_negative_amount
from aware_economy.stable_ids import stable_rate_snapshot_id

# --- AWARE: USER_IMPORTS END


async def create_price_reservation(
    rate_snapshot: RateSnapshot,
    reservation_key: str,
    reserved_at: datetime,
    additional_metadata: JsonObject | None = JsonObject(),
    status: PriceReservationStatus = PriceReservationStatus.reserved,
) -> PriceReservation:
    """
    Creates one canonical reservation receipt under this RateSnapshot.

    Receipt: PriceReservation(status=reserved) linked to this RateSnapshot.
    """

    # --- AWARE: LOGIC START create_price_reservation
    reservation = await PriceReservation.build_via_rate_snapshot(
        rate_snapshot_id=rate_snapshot.id,
        reservation_key=reservation_key,
        reserved_at=reserved_at,
        additional_metadata=additional_metadata,
        status=status,
    )
    for existing in rate_snapshot.price_reservations:
        if str(existing.id) == str(reservation.id):
            return existing
    rate_snapshot.price_reservations.append(reservation)
    return reservation
    # --- AWARE: LOGIC END create_price_reservation


async def build_via_price_schedule(
    price_schedule_id: UUID,
    snapshot_key: str,
    quoted_amount: Annotated[Decimal, DecimalWire()],
    captured_at: datetime,
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = None,
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = None,
    markup_amount: Annotated[Decimal, DecimalWire()] | None = None,
    meter_evidence_ref: str | None = None,
    additional_metadata: JsonObject | None = JsonObject(),
) -> RateSnapshot:
    """
    Creates one immutable snapshot under a PriceSchedule.
    """

    # --- AWARE: LOGIC START build_via_price_schedule
    snapshot_key_norm = snapshot_key.strip()
    if not snapshot_key_norm:
        raise ValueError("rate_snapshot.build_via_price_schedule requires a non-empty snapshot_key")
    quoted_amount = non_negative_amount(
        quoted_amount,
        field_name="rate snapshot quoted_amount",
    )
    if cost_basis_amount is not None:
        cost_basis_amount = non_negative_amount(
            cost_basis_amount,
            field_name="rate snapshot cost_basis_amount",
        )
    if markup_percentage is not None:
        markup_percentage = non_negative_amount(
            markup_percentage,
            field_name="rate snapshot markup_percentage",
        )
    if markup_amount is not None:
        markup_amount = non_negative_amount(
            markup_amount,
            field_name="rate snapshot markup_amount",
        )
    meter_evidence_ref = (meter_evidence_ref or "").strip() if meter_evidence_ref is not None else None
    metering_values = (
        cost_basis_amount,
        markup_percentage,
        markup_amount,
        meter_evidence_ref,
    )
    if any(value is not None for value in metering_values) and not all(value is not None for value in metering_values):
        raise ValueError("rate_snapshot.build_via_price_schedule requires complete metering evidence")

    rate_snapshot_id = stable_rate_snapshot_id(
        price_schedule_id=price_schedule_id,
        snapshot_key=snapshot_key_norm,
    )
    return RateSnapshot(
        id=rate_snapshot_id,
        price_schedule_id=price_schedule_id,
        snapshot_key=snapshot_key_norm,
        quoted_amount=quoted_amount,
        captured_at=captured_at,
        cost_basis_amount=cost_basis_amount,
        markup_percentage=markup_percentage,
        markup_amount=markup_amount,
        meter_evidence_ref=meter_evidence_ref,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
    )
    # --- AWARE: LOGIC END build_via_price_schedule
