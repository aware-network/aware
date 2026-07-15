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
from aware_economy_ontology.price.price_enums import PriceType
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.price_schedule import PriceSchedule

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
# Economy Runtime
from aware_economy.capital_amount import non_negative_amount
from aware_economy.stable_ids import stable_price_id

# --- AWARE: USER_IMPORTS END


async def build(
    coin_id: UUID, name: str, type: PriceType, additional_metadata: JsonObject | None = JsonObject()
) -> Price:
    """
    Creates one Economy-owned price primitive.

    Receipt: Price linked to Coin as a stable pricing family root.
    """

    # --- AWARE: LOGIC START build
    name_norm = name.strip()
    if not name_norm:
        raise ValueError("price.build requires a non-empty name")

    price_type = getattr(type, "value", str(type))
    if price_type not in {PriceType.fixed.value, PriceType.dynamic.value}:
        raise ValueError(f"price.build does not support unknown price type: {price_type}")

    price_id = stable_price_id(
        coin_id=coin_id,
        name=name_norm,
        type=str(price_type),
    )
    return Price(
        id=price_id,
        coin_id=coin_id,
        name=name_norm,
        type=type,
        additional_metadata=(additional_metadata if additional_metadata is not None else JsonObject({})),
    )
    # --- AWARE: LOGIC END build


async def create_price_schedule(
    price: Price,
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
    Creates one schedule under this Price.

    Receipt: PriceSchedule linked to this Price and the referenced PricingPolicy.
    """

    # --- AWARE: LOGIC START create_price_schedule
    price_type = getattr(price.type, "value", str(price.type))
    if price_type == PriceType.fixed.value:
        if fixed_amount is None:
            raise ValueError("price.create_price_schedule fixed prices require fixed_amount")
        fixed_amount = non_negative_amount(
            fixed_amount,
            field_name="price fixed_amount",
        )
        if markup_percentage is not None:
            raise ValueError("price.create_price_schedule fixed prices must not provide markup_percentage")
    elif price_type == PriceType.dynamic.value:
        if markup_percentage is None:
            raise ValueError("price.create_price_schedule dynamic prices require markup_percentage")
        markup_percentage = non_negative_amount(
            markup_percentage,
            field_name="price markup_percentage",
        )
        if fixed_amount is not None:
            raise ValueError("price.create_price_schedule dynamic prices must not provide fixed_amount")
    else:
        raise ValueError(f"price.create_price_schedule does not support unknown price type: {price_type}")

    schedule = await PriceSchedule.build_via_price(
        price_id=price.id,
        pricing_policy_id=pricing_policy_id,
        name=name,
        effective_from=effective_from,
        version=version,
        effective_until=effective_until,
        fixed_amount=fixed_amount,
        markup_percentage=markup_percentage,
        additional_metadata=additional_metadata,
    )
    price.price_schedules.append(schedule)
    return schedule
    # --- AWARE: LOGIC END create_price_schedule
