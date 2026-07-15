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
from aware_economy_ontology.price.price_schedule import PriceSchedule
from aware_economy_ontology.price.rate_snapshot import RateSnapshot

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
# Economy Runtime
from aware_economy.capital_amount import non_negative_amount

# Economy Runtime
from aware_economy.stable_ids import stable_price_schedule_id

# --- AWARE: USER_IMPORTS END


async def capture_rate_snapshot(
    price_schedule: PriceSchedule,
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
    Captures one immutable pricing snapshot under this schedule.

    Receipt: RateSnapshot linked to this PriceSchedule.
    """

    # --- AWARE: LOGIC START capture_rate_snapshot
    quoted_amount = non_negative_amount(
        quoted_amount,
        field_name="rate snapshot quoted_amount",
    )
    snapshot = await RateSnapshot.build_via_price_schedule(
        price_schedule_id=price_schedule.id,
        snapshot_key=snapshot_key,
        quoted_amount=quoted_amount,
        captured_at=captured_at,
        cost_basis_amount=cost_basis_amount,
        markup_percentage=markup_percentage,
        markup_amount=markup_amount,
        meter_evidence_ref=meter_evidence_ref,
        additional_metadata=additional_metadata,
    )
    price_schedule.rate_snapshots.append(snapshot)
    return snapshot
    # --- AWARE: LOGIC END capture_rate_snapshot


async def build_via_price(
    price_id: UUID,
    pricing_policy_id: UUID,
    name: str,
    effective_from: datetime,
    version: int = 1,
    effective_until: datetime | None = None,
    fixed_amount: Annotated[Decimal, DecimalWire()] | None = None,
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = None,
    additional_metadata: JsonObject | None = JsonObject(),
) -> PriceSchedule:
    """
    Creates one schedule under a Price.

    Receipt: PriceSchedule linked to Price + PricingPolicy with a validity window.
    """

    # --- AWARE: LOGIC START build_via_price
    name_norm = name.strip()
    if not name_norm:
        raise ValueError("price_schedule.build_via_price requires a non-empty name")
    if version < 1:
        raise ValueError("price_schedule.build_via_price requires version >= 1")
    if effective_until is not None and effective_until < effective_from:
        raise ValueError("price_schedule.build_via_price requires effective_until >= effective_from")
    if fixed_amount is None and markup_percentage is None:
        raise ValueError("price_schedule.build_via_price requires fixed_amount or markup_percentage")
    if fixed_amount is not None and markup_percentage is not None:
        raise ValueError("price_schedule.build_via_price accepts one pricing mode per schedule")
    if fixed_amount is not None:
        fixed_amount = non_negative_amount(
            fixed_amount,
            field_name="price schedule fixed_amount",
        )
    if markup_percentage is not None:
        markup_percentage = non_negative_amount(
            markup_percentage,
            field_name="price schedule markup_percentage",
        )

    price_schedule_id = stable_price_schedule_id(
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        name=name_norm,
        version=version,
    )
    return PriceSchedule(
        id=price_schedule_id,
        price_id=price_id,
        pricing_policy_id=pricing_policy_id,
        name=name_norm,
        version=version,
        effective_from=effective_from,
        effective_until=effective_until,
        fixed_amount=fixed_amount,
        markup_percentage=markup_percentage,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
    )
    # --- AWARE: LOGIC END build_via_price
