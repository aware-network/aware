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

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_economy.capital_amount import non_negative_amount
from aware_economy_ontology.stable_ids import stable_price_reservation_id

# --- AWARE: USER_IMPORTS END


async def set_status(
    price_reservation: PriceReservation,
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

    # --- AWARE: LOGIC START set_status
    current = price_reservation.status
    if final_amount is not None:
        final_amount = non_negative_amount(
            final_amount,
            field_name="price reservation final_amount",
        )
    if actual_cost_basis_amount is not None:
        actual_cost_basis_amount = non_negative_amount(
            actual_cost_basis_amount,
            field_name="price reservation actual_cost_basis_amount",
        )
    if actual_markup_amount is not None:
        actual_markup_amount = non_negative_amount(
            actual_markup_amount,
            field_name="price reservation actual_markup_amount",
        )
    meter_evidence_ref = (meter_evidence_ref or "").strip() if meter_evidence_ref is not None else None
    metering_values = (
        actual_cost_basis_amount,
        actual_markup_amount,
        meter_evidence_ref,
    )
    if any(value is not None for value in metering_values) and not all(value is not None for value in metering_values):
        raise ValueError("price_reservation.set_status requires complete actual metering evidence")

    terminal = {
        PriceReservationStatus.cancelled,
        PriceReservationStatus.settled,
    }
    if current in terminal and status != current:
        raise ValueError(f"price_reservation status is terminal and cannot transition: {current} -> {status}")
    if current in terminal:
        expected = (
            price_reservation.final_amount,
            price_reservation.actual_cost_basis_amount,
            price_reservation.actual_markup_amount,
            price_reservation.meter_evidence_ref,
        )
        requested = (
            final_amount,
            actual_cost_basis_amount,
            actual_markup_amount,
            meter_evidence_ref,
        )
        if requested != expected:
            raise ValueError("price_reservation terminal replay conflicts with committed evidence")
        return price_reservation
    if status == PriceReservationStatus.settled:
        if final_amount is None and price_reservation.final_amount is None:
            raise ValueError("price_reservation.set_status(settled) requires final_amount when unset")
    elif any(value is not None for value in (final_amount, *metering_values)):
        raise ValueError("price_reservation non-settled status must not carry final metering evidence")
    if final_amount is not None:
        price_reservation.final_amount = final_amount
    if actual_cost_basis_amount is not None:
        price_reservation.actual_cost_basis_amount = actual_cost_basis_amount
        price_reservation.actual_markup_amount = actual_markup_amount
        price_reservation.meter_evidence_ref = meter_evidence_ref
    price_reservation.status = status
    return price_reservation
    # --- AWARE: LOGIC END set_status


async def build_via_rate_snapshot(
    rate_snapshot_id: UUID,
    reservation_key: str,
    reserved_at: datetime,
    additional_metadata: JsonObject | None = JsonObject(),
    status: PriceReservationStatus = PriceReservationStatus.reserved,
) -> PriceReservation:
    """
    Creates one Economy-owned price reservation receipt under a RateSnapshot.

    Receipt: PriceReservation(status=reserved) linked to the authoritative quoted RateSnapshot.
    """

    # --- AWARE: LOGIC START build_via_rate_snapshot
    reservation_key_norm = (reservation_key or "").strip()
    if not reservation_key_norm:
        raise ValueError("price_reservation.build_via_rate_snapshot requires a non-empty reservation_key")

    return PriceReservation(
        id=stable_price_reservation_id(
            rate_snapshot_id=rate_snapshot_id,
            reservation_key=reservation_key_norm,
        ),
        rate_snapshot_id=rate_snapshot_id,
        reservation_key=reservation_key_norm,
        reserved_at=reserved_at,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
        status=status,
    )
    # --- AWARE: LOGIC END build_via_rate_snapshot
