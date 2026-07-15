from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import ContextManager, Protocol, TypeVar, cast
from uuid import UUID

from aware_api_runtime.invocation import ApiInvocationRuntimeProtocol
from aware_code.types import JsonObject
from aware_economy.capital_amount import canonical_amount_text, non_negative_amount
from aware_economy_ontology.coin.coin import Coin
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.price_enums import PriceType
from aware_economy_ontology.price.price_reservation import PriceReservation
from aware_economy_ontology.price.price_reservation_enums import PriceReservationStatus
from aware_economy_ontology.price.price_schedule import PriceSchedule
from aware_economy_ontology.price.rate_snapshot import RateSnapshot
from aware_economy_ontology.stable_ids import (
    stable_price_reservation_id,
    stable_rate_snapshot_id,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.models.orm_model import ORMModel


_TModel = TypeVar("_TModel", bound=ORMModel)


class _MetaRuntimeLaneProtocol(Protocol):
    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> ContextManager[object]: ...


@dataclass(frozen=True, slots=True)
class PriceReservationReserveReceipt:
    price_id: UUID
    price_schedule_id: UUID
    rate_snapshot_id: UUID
    price_reservation_id: UUID
    quoted_amount: Decimal
    cost_basis_amount: Decimal | None
    markup_percentage: Decimal | None
    markup_amount: Decimal | None
    meter_evidence_ref: str | None
    status: PriceReservationStatus


@dataclass(frozen=True, slots=True)
class PriceReservationFinalizeReceipt:
    price_reservation_id: UUID
    status: PriceReservationStatus
    final_amount: Decimal | None
    actual_cost_basis_amount: Decimal | None
    actual_markup_amount: Decimal | None
    meter_evidence_ref: str | None


@dataclass(frozen=True, slots=True)
class _ResolvedScheduleAmount:
    amount: Decimal
    cost_basis_amount: Decimal | None
    markup_percentage: Decimal | None
    markup_amount: Decimal | None
    meter_evidence_ref: str | None


def build_economy_price_lane(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
) -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Price",
        ),
    )


async def reserve_price_reservation(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    economy_price_lane: MaterializationLaneContext,
    price_id: UUID,
    request_hash: str,
    operation_key: str,
    pricing_policy_id: UUID | None,
    upper_bound_cost_basis_amount: Decimal | None,
    cost_basis_coin_id: UUID | None,
    meter_evidence_ref: str | None,
    commit: bool,
    publish: bool,
) -> PriceReservationReserveReceipt:
    request_hash_norm = (request_hash or "").strip()
    if not request_hash_norm:
        raise ValueError("reserve_price_reservation requires a non-empty request_hash")

    as_of = datetime.now(UTC)
    price = await _hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=Price,
        object_id=price_id,
        error_context="Economy price reservation reserve price hydration",
    )
    schedule = _select_active_price_schedule(price=price, as_of=as_of)
    if (
        pricing_policy_id is not None
        and schedule.pricing_policy_id != pricing_policy_id
    ):
        raise ValueError(
            "Economy active PriceSchedule does not match admitted pricing policy: "
            f"expected={pricing_policy_id} actual={schedule.pricing_policy_id}"
        )
    coin = await _hydrate_committed_lane_object(
        index=index,
        target_lane=MaterializationLaneContext(
            branch_id=price.coin_id,
            projection_hash=_find_projection_hash_by_name(
                index=index,
                projection_name="Coin",
            ),
        ),
        orm_class=Coin,
        object_id=price.coin_id,
        error_context="Economy price reservation reserve coin hydration",
    )
    quote = _resolve_schedule_amount(
        price=price,
        schedule=schedule,
        coin=coin,
        cost_basis_amount=upper_bound_cost_basis_amount,
        cost_basis_coin_id=cost_basis_coin_id,
        meter_evidence_ref=meter_evidence_ref,
        evidence_phase="upper-bound",
    )
    rate_snapshot_id = stable_rate_snapshot_id(
        price_schedule_id=schedule.id,
        snapshot_key=request_hash_norm,
    )
    price_reservation_id = stable_price_reservation_id(
        rate_snapshot_id=rate_snapshot_id,
        reservation_key=request_hash_norm,
    )

    snapshot_metadata = cast(
        JsonObject,
        {
            "reservation_key": request_hash_norm,
            "operation_key": operation_key,
            "price_id": str(price.id),
            "price_schedule_id": str(schedule.id),
            "pricing_policy_id": str(schedule.pricing_policy_id),
            "coin_id": str(price.coin_id),
            "price_type": price.type.value,
            "cost_basis_amount": _optional_amount_text(quote.cost_basis_amount),
            "markup_percentage": _optional_amount_text(quote.markup_percentage),
            "markup_amount": _optional_amount_text(quote.markup_amount),
            "meter_evidence_ref": quote.meter_evidence_ref,
        },
    )
    reservation_metadata = cast(
        JsonObject,
        {
            "request_hash": request_hash_norm,
            "operation_key": operation_key,
            "rate_snapshot_id": str(rate_snapshot_id),
        },
    )

    existing_snapshot = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=RateSnapshot,
        object_id=rate_snapshot_id,
    )
    runtime_lane = _bind_economy_price_lane(
        runtime=runtime,
        branch_id=economy_price_lane.branch_id,
        projection=economy_price_lane.projection_hash,
        actor_id=actor_id,
    )
    with runtime_lane.activate(commit=commit, publish=publish):
        if existing_snapshot is None:
            price_schedule_ref = PriceSchedule.model_construct(id=schedule.id)
            _ = await price_schedule_ref.capture_rate_snapshot(
                snapshot_key=request_hash_norm,
                quoted_amount=quote.amount,
                captured_at=as_of,
                cost_basis_amount=quote.cost_basis_amount,
                markup_percentage=quote.markup_percentage,
                markup_amount=quote.markup_amount,
                meter_evidence_ref=quote.meter_evidence_ref,
                additional_metadata=snapshot_metadata,
            )
        else:
            _require_matching_snapshot(existing=existing_snapshot, quote=quote)
        rate_snapshot_ref = RateSnapshot.model_construct(id=rate_snapshot_id)
        _ = await rate_snapshot_ref.create_price_reservation(
            reservation_key=request_hash_norm,
            reserved_at=as_of,
            additional_metadata=reservation_metadata,
            status=PriceReservationStatus.reserved,
        )

    return PriceReservationReserveReceipt(
        price_id=price_id,
        price_schedule_id=schedule.id,
        rate_snapshot_id=rate_snapshot_id,
        price_reservation_id=price_reservation_id,
        quoted_amount=quote.amount,
        cost_basis_amount=quote.cost_basis_amount,
        markup_percentage=quote.markup_percentage,
        markup_amount=quote.markup_amount,
        meter_evidence_ref=quote.meter_evidence_ref,
        status=PriceReservationStatus.reserved,
    )


async def finalize_price_reservation(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    economy_price_lane: MaterializationLaneContext,
    price_reservation_id: UUID,
    status: PriceReservationStatus,
    actual_cost_basis_amount: Decimal | None,
    cost_basis_coin_id: UUID | None,
    meter_evidence_ref: str | None,
    commit: bool,
    publish: bool,
) -> PriceReservationFinalizeReceipt:
    reservation = await _hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=PriceReservation,
        object_id=price_reservation_id,
        error_context="Economy price reservation finalize reservation hydration",
    )
    snapshot = await _hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=RateSnapshot,
        object_id=reservation.rate_snapshot_id,
        error_context="Economy price reservation finalize rate snapshot hydration",
    )
    schedule = await _hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=PriceSchedule,
        object_id=snapshot.price_schedule_id,
        error_context="Economy price reservation finalize price schedule hydration",
    )
    price = await _hydrate_committed_lane_object(
        index=index,
        target_lane=economy_price_lane,
        orm_class=Price,
        object_id=schedule.price_id,
        error_context="Economy price reservation finalize price hydration",
    )
    coin = await _hydrate_committed_lane_object(
        index=index,
        target_lane=MaterializationLaneContext(
            branch_id=price.coin_id,
            projection_hash=_find_projection_hash_by_name(
                index=index,
                projection_name="Coin",
            ),
        ),
        orm_class=Coin,
        object_id=price.coin_id,
        error_context="Economy price reservation finalize coin hydration",
    )
    final_quote: _ResolvedScheduleAmount | None = None
    if status == PriceReservationStatus.settled:
        final_quote = _resolve_schedule_amount(
            price=price,
            schedule=schedule,
            coin=coin,
            cost_basis_amount=actual_cost_basis_amount,
            cost_basis_coin_id=cost_basis_coin_id,
            meter_evidence_ref=meter_evidence_ref,
            evidence_phase="actual",
        )
        reserved_amount = non_negative_amount(
            snapshot.quoted_amount,
            field_name="price reservation reserved quote",
        )
        if final_quote.amount > reserved_amount:
            raise ValueError(
                "Economy actual metered price exceeds reserved quote: "
                f"actual={final_quote.amount} reserved={reserved_amount}"
            )
        if (
            snapshot.cost_basis_amount is not None
            and final_quote.cost_basis_amount is not None
            and final_quote.cost_basis_amount > snapshot.cost_basis_amount
        ):
            raise ValueError(
                "Economy actual cost basis exceeds reserved upper bound: "
                f"actual={final_quote.cost_basis_amount} "
                f"upper_bound={snapshot.cost_basis_amount}"
            )
    elif any(
        value is not None
        for value in (
            actual_cost_basis_amount,
            cost_basis_coin_id,
            meter_evidence_ref,
        )
    ):
        raise ValueError(
            "Economy cancelled price reservation must not carry actual metering evidence"
        )
    runtime_lane = _bind_economy_price_lane(
        runtime=runtime,
        branch_id=economy_price_lane.branch_id,
        projection=economy_price_lane.projection_hash,
        actor_id=actor_id,
    )
    with runtime_lane.activate(commit=commit, publish=publish):
        reservation_ref = PriceReservation.model_construct(id=price_reservation_id)
        updated = await reservation_ref.set_status(
            status=status,
            final_amount=(final_quote.amount if final_quote is not None else None),
            actual_cost_basis_amount=(
                final_quote.cost_basis_amount if final_quote is not None else None
            ),
            actual_markup_amount=(
                final_quote.markup_amount if final_quote is not None else None
            ),
            meter_evidence_ref=(
                final_quote.meter_evidence_ref if final_quote is not None else None
            ),
        )

    return PriceReservationFinalizeReceipt(
        price_reservation_id=price_reservation_id,
        status=updated.status,
        final_amount=(
            non_negative_amount(
                updated.final_amount,
                field_name="price reservation final_amount",
            )
            if updated.final_amount is not None
            else None
        ),
        actual_cost_basis_amount=(
            non_negative_amount(
                updated.actual_cost_basis_amount,
                field_name="price reservation actual_cost_basis_amount",
            )
            if updated.actual_cost_basis_amount is not None
            else None
        ),
        actual_markup_amount=(
            non_negative_amount(
                updated.actual_markup_amount,
                field_name="price reservation actual_markup_amount",
            )
            if updated.actual_markup_amount is not None
            else None
        ),
        meter_evidence_ref=updated.meter_evidence_ref,
    )


def _select_active_price_schedule(*, price: Price, as_of: datetime) -> PriceSchedule:
    candidates = tuple(
        schedule
        for schedule in price.price_schedules
        if schedule.effective_from <= as_of
        and (schedule.effective_until is None or as_of <= schedule.effective_until)
    )
    if len(candidates) != 1:
        raise RuntimeError(
            "Economy settlement requires exactly one active PriceSchedule for reserve flow: "
            + f"price_id={price.id} active_count={len(candidates)}"
        )
    return candidates[0]


def _resolve_schedule_amount(
    *,
    price: Price,
    schedule: PriceSchedule,
    coin: Coin,
    cost_basis_amount: Decimal | None,
    cost_basis_coin_id: UUID | None,
    meter_evidence_ref: str | None,
    evidence_phase: str,
) -> _ResolvedScheduleAmount:
    if price.type == PriceType.fixed:
        if schedule.fixed_amount is None or schedule.markup_percentage is not None:
            raise RuntimeError(
                "Economy fixed Price requires fixed_amount and no markup_percentage: "
                f"price_schedule_id={schedule.id}"
            )
        if any(
            value is not None
            for value in (cost_basis_amount, cost_basis_coin_id, meter_evidence_ref)
        ):
            raise ValueError(
                f"Economy fixed Price does not accept {evidence_phase} metering evidence"
            )
        amount = _coin_amount(
            schedule.fixed_amount,
            coin=coin,
            field_name="price schedule fixed_amount",
        )
        return _ResolvedScheduleAmount(
            amount=amount,
            cost_basis_amount=None,
            markup_percentage=None,
            markup_amount=None,
            meter_evidence_ref=None,
        )
    if price.type != PriceType.dynamic:
        raise RuntimeError(f"Unsupported Economy Price type: {price.type!r}")
    if schedule.fixed_amount is not None or schedule.markup_percentage is None:
        raise RuntimeError(
            "Economy dynamic Price requires markup_percentage and no fixed_amount: "
            f"price_schedule_id={schedule.id}"
        )
    if cost_basis_amount is None or cost_basis_coin_id is None:
        raise ValueError(
            f"Economy dynamic Price requires {evidence_phase} cost basis and coin"
        )
    if cost_basis_coin_id != price.coin_id:
        raise ValueError(
            "Economy dynamic Price cost-basis coin mismatch: "
            f"expected={price.coin_id} actual={cost_basis_coin_id}"
        )
    evidence_ref = (meter_evidence_ref or "").strip()
    if not evidence_ref:
        raise ValueError(
            f"Economy dynamic Price requires {evidence_phase} meter_evidence_ref"
        )
    basis = _coin_amount(
        cost_basis_amount,
        coin=coin,
        field_name=f"{evidence_phase} cost_basis_amount",
    )
    markup_percentage = non_negative_amount(
        schedule.markup_percentage,
        field_name="price schedule markup_percentage",
    )
    amount = _quantize_coin(
        basis + (basis * markup_percentage / Decimal("100")),
        coin=coin,
    )
    return _ResolvedScheduleAmount(
        amount=amount,
        cost_basis_amount=basis,
        markup_percentage=markup_percentage,
        markup_amount=amount - basis,
        meter_evidence_ref=evidence_ref,
    )


def _coin_amount(value: object, *, coin: Coin, field_name: str) -> Decimal:
    amount = non_negative_amount(value, field_name=field_name)
    quantized = _quantize_coin(amount, coin=coin)
    if quantized != amount:
        raise ValueError(
            f"{field_name} exceeds coin precision: decimals={coin.decimals} value={amount}"
        )
    return quantized


def _quantize_coin(value: Decimal, *, coin: Coin) -> Decimal:
    if coin.decimals < 0:
        raise ValueError(f"Coin decimals must be >= 0: coin_id={coin.id}")
    quantum = Decimal(1).scaleb(-coin.decimals)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


def _optional_amount_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return canonical_amount_text(value)


def _require_matching_snapshot(
    *, existing: RateSnapshot, quote: _ResolvedScheduleAmount
) -> None:
    expected = (
        quote.amount,
        quote.cost_basis_amount,
        quote.markup_percentage,
        quote.markup_amount,
        quote.meter_evidence_ref,
    )
    actual = (
        existing.quoted_amount,
        existing.cost_basis_amount,
        existing.markup_percentage,
        existing.markup_amount,
        existing.meter_evidence_ref,
    )
    if actual != expected:
        raise ValueError(
            "Economy price reservation idempotency conflict for committed rate snapshot: "
            f"expected={expected!r} actual={actual!r}"
        )


def _bind_economy_price_lane(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    branch_id: UUID,
    projection: str,
    actor_id: UUID | None,
) -> _MetaRuntimeLaneProtocol:
    return runtime.bind(
        branch_id=branch_id,
        projection=projection,
        actor_id=actor_id,
    )


async def _hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    orm_class: type[_TModel],
    object_id: UUID,
    error_context: str,
) -> _TModel:
    obj = await _maybe_hydrate_committed_lane_object(
        index=index,
        target_lane=target_lane,
        orm_class=orm_class,
        object_id=object_id,
    )
    if obj is None:
        commit_store = FSCommitStore()
        lane_head = await commit_store.head(
            branch_id=target_lane.branch_id,
            projection_hash=target_lane.projection_hash,
        )
        raise RuntimeError(
            f"{error_context}: missing {orm_class.__name__} object_id={object_id} "
            f"branch_id={target_lane.branch_id} "
            f"projection_hash={target_lane.projection_hash} "
            f"aware_root={getattr(commit_store, '_aware_root', None)} "
            f"lane_head={lane_head!r}"
        )
    return obj


async def _maybe_hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    target_lane: MaterializationLaneContext,
    orm_class: type[_TModel],
    object_id: UUID,
) -> _TModel | None:
    target_head = await FSCommitStore().head(
        branch_id=target_lane.branch_id,
        projection_hash=target_lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None

    opg = index.opg_by_hash.get(target_lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Economy settlement could not resolve projection hash for committed lane hydration: "
            + repr(target_lane.projection_hash)
        )

    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=target_lane.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=target_lane.branch_id,
        preferred_model_type=orm_class,
    )
    hydrated = session.imap_get(orm_class, object_id)
    if hydrated is None:
        return None
    return hydrated


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    matches = tuple(
        sorted(
            str(projection_hash)
            for projection_hash, opg in index.opg_by_hash.items()
            if (opg.name or "").strip() == target
        )
    )
    if len(matches) != 1:
        raise ValueError(
            f"Expected one Economy runtime projection named {projection_name!r}, got {matches!r}"
        )
    return matches[0]


__all__ = [
    "PriceReservationFinalizeReceipt",
    "PriceReservationReserveReceipt",
    "build_economy_price_lane",
    "finalize_price_reservation",
    "reserve_price_reservation",
]
