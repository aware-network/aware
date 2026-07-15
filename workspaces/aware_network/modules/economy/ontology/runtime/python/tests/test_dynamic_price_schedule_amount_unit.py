from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

import aware_economy.price_reservation_settlement as settlement_module
from aware_economy.price_reservation_settlement import (
    _resolve_schedule_amount,
    finalize_price_reservation,
)
from aware_economy.handlers.impl.price.price_reservation import set_status
from aware_economy.handlers.impl.price.rate_snapshot import build_via_price_schedule
from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.coin.coin_enums import CoinType
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.price_enums import PriceType
from aware_economy_ontology.price.price_reservation import PriceReservation
from aware_economy_ontology.price.price_reservation_enums import (
    PriceReservationStatus,
)
from aware_economy_ontology.price.price_schedule import PriceSchedule
from aware_economy_ontology.price.rate_snapshot import RateSnapshot
from aware_meta.materialization import MaterializationLaneContext


def _coin(*, decimals: int = 2) -> Coin:
    return Coin.model_construct(
        id=uuid4(),
        symbol="USD",
        name="US Dollar",
        type=CoinType.fiat,
        decimals=decimals,
    )


def _dynamic_price(*, coin: Coin) -> tuple[Price, PriceSchedule]:
    price = Price.model_construct(
        id=uuid4(),
        coin_id=coin.id,
        name="metered-operation",
        type=PriceType.dynamic,
        price_schedules=[],
    )
    schedule = PriceSchedule.model_construct(
        id=uuid4(),
        price_id=price.id,
        pricing_policy_id=uuid4(),
        name="cost-plus-20",
        version=1,
        effective_from="2026-07-01T00:00:00Z",
        fixed_amount=None,
        markup_percentage=Decimal("20"),
    )
    return price, schedule


def test_dynamic_price_is_exact_cost_basis_plus_schedule_markup() -> None:
    coin = _coin()
    price, schedule = _dynamic_price(coin=coin)

    resolved = _resolve_schedule_amount(
        price=price,
        schedule=schedule,
        coin=coin,
        cost_basis_amount=Decimal("10.00"),
        cost_basis_coin_id=coin.id,
        meter_evidence_ref="meter://estimate/1",
        evidence_phase="upper-bound",
    )

    assert resolved.cost_basis_amount == Decimal("10.00")
    assert resolved.markup_percentage == Decimal("20")
    assert resolved.markup_amount == Decimal("2.00")
    assert resolved.amount == Decimal("12.00")
    assert resolved.meter_evidence_ref == "meter://estimate/1"


@pytest.mark.asyncio
async def test_rate_snapshot_build_persists_complete_dynamic_metering_evidence() -> None:
    schedule_id = uuid4()
    snapshot = await build_via_price_schedule(
        price_schedule_id=schedule_id,
        snapshot_key="request-dynamic-1",
        quoted_amount=Decimal("6.00"),
        captured_at="2026-07-12T00:00:00Z",  # type: ignore[arg-type]
        cost_basis_amount=Decimal("5.00"),
        markup_percentage=Decimal("20"),
        markup_amount=Decimal("1.00"),
        meter_evidence_ref="meter://estimate/dynamic-1",
    )

    assert snapshot.cost_basis_amount == Decimal("5.00")
    assert snapshot.markup_percentage == Decimal("20")
    assert snapshot.markup_amount == Decimal("1.00")
    assert snapshot.meter_evidence_ref == "meter://estimate/dynamic-1"


@pytest.mark.parametrize(
    ("basis", "coin_matches", "evidence_ref", "message"),
    [
        (None, True, "meter://estimate/1", "requires upper-bound cost basis"),
        (Decimal("1.001"), True, "meter://estimate/1", "exceeds coin precision"),
        (Decimal("1.00"), False, "meter://estimate/1", "coin mismatch"),
        (Decimal("1.00"), True, "", "requires upper-bound meter_evidence_ref"),
    ],
)
def test_dynamic_price_fails_closed_on_invalid_metering_evidence(
    basis: Decimal | None,
    coin_matches: bool,
    evidence_ref: str,
    message: str,
) -> None:
    coin = _coin()
    price, schedule = _dynamic_price(coin=coin)

    with pytest.raises(ValueError, match=message):
        _resolve_schedule_amount(
            price=price,
            schedule=schedule,
            coin=coin,
            cost_basis_amount=basis,
            cost_basis_coin_id=coin.id if coin_matches else uuid4(),
            meter_evidence_ref=evidence_ref,
            evidence_phase="upper-bound",
        )


@pytest.mark.asyncio
async def test_price_reservation_persists_complete_actual_metering_evidence() -> None:
    reservation = PriceReservation.model_construct(
        id=uuid4(),
        rate_snapshot_id=uuid4(),
        reservation_key="request-1",
        reserved_at="2026-07-12T00:00:00Z",
        status=PriceReservationStatus.reserved,
    )

    updated = await set_status(
        reservation,
        status=PriceReservationStatus.settled,
        final_amount=Decimal("9.60"),
        actual_cost_basis_amount=Decimal("8.00"),
        actual_markup_amount=Decimal("1.60"),
        meter_evidence_ref="meter://actual/1",
    )

    assert updated.final_amount == Decimal("9.60")
    assert updated.actual_cost_basis_amount == Decimal("8.00")
    assert updated.actual_markup_amount == Decimal("1.60")
    assert updated.meter_evidence_ref == "meter://actual/1"


@pytest.mark.asyncio
async def test_price_reservation_rejects_partial_or_cancelled_metering_evidence() -> None:
    reservation = PriceReservation.model_construct(
        id=uuid4(),
        rate_snapshot_id=uuid4(),
        reservation_key="request-2",
        reserved_at="2026-07-12T00:00:00Z",
        status=PriceReservationStatus.reserved,
    )

    with pytest.raises(ValueError, match="complete actual metering evidence"):
        await set_status(
            reservation,
            status=PriceReservationStatus.settled,
            final_amount=Decimal("9.60"),
            actual_cost_basis_amount=Decimal("8.00"),
        )

    with pytest.raises(ValueError, match="non-settled status"):
        await set_status(
            reservation,
            status=PriceReservationStatus.cancelled,
            final_amount=Decimal("0"),
        )


@pytest.mark.asyncio
async def test_actual_dynamic_price_above_reserved_upper_bound_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coin = _coin()
    price, schedule = _dynamic_price(coin=coin)
    snapshot = RateSnapshot.model_construct(
        id=uuid4(),
        price_schedule_id=schedule.id,
        snapshot_key="request-3",
        quoted_amount=Decimal("12.00"),
        captured_at="2026-07-12T00:00:00Z",
        cost_basis_amount=Decimal("10.00"),
        markup_percentage=Decimal("20"),
        markup_amount=Decimal("2.00"),
        meter_evidence_ref="meter://estimate/3",
    )
    reservation = PriceReservation.model_construct(
        id=uuid4(),
        rate_snapshot_id=snapshot.id,
        reservation_key="request-3",
        reserved_at="2026-07-12T00:00:00Z",
        status=PriceReservationStatus.reserved,
    )
    objects = {
        PriceReservation: reservation,
        RateSnapshot: snapshot,
        PriceSchedule: schedule,
        Price: price,
        Coin: coin,
    }

    async def _hydrate(**kwargs):  # type: ignore[no-untyped-def]
        return objects[kwargs["orm_class"]]

    monkeypatch.setattr(
        settlement_module,
        "_hydrate_committed_lane_object",
        _hydrate,
    )
    monkeypatch.setattr(
        settlement_module,
        "_find_projection_hash_by_name",
        lambda **_kwargs: "sha256:coin",
    )

    with pytest.raises(ValueError, match="exceeds reserved quote"):
        await finalize_price_reservation(
            runtime=object(),  # type: ignore[arg-type]
            index=object(),  # type: ignore[arg-type]
            actor_id=uuid4(),
            economy_price_lane=MaterializationLaneContext(
                branch_id=uuid4(),
                projection_hash="sha256:price",
            ),
            price_reservation_id=reservation.id,
            status=PriceReservationStatus.settled,
            actual_cost_basis_amount=Decimal("11.00"),
            cost_basis_coin_id=coin.id,
            meter_evidence_ref="meter://actual/3",
            commit=True,
            publish=False,
        )
