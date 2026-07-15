from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.finance_readiness import (
    FinanceEntityReadinessReceipt,
    resolve_economy_finance_readiness_runtime_context,
    resolve_finance_entity_readiness,
)
from aware_economy.meta_runtime import (
    EconomyMetaRuntimeLane,
    EconomyMetaRuntimeLaneBinder,
)
from aware_economy.ontology.materialization import wallet_balance_amounts
from aware_economy_ontology.smart_contract.smart_contract import SmartContract
from aware_economy_ontology.smart_contract.smart_contract_enums import (
    SmartContractMemberType,
    SmartContractStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_economy_ontology.smart_contract.smart_contract_permit_enums import (
    SmartContractPermitStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation import (
    SmartContractReservation,
)
from aware_economy_ontology.smart_contract.smart_contract_reservation_enums import (
    ReservationStatus,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement import (
    SmartContractSettlement,
)
from aware_economy_ontology.smart_contract.smart_contract_settlement_enums import (
    SmartContractSettlementStatus,
)
from aware_economy_ontology.stable_ids import (
    stable_escrow_id,
    stable_smart_contract_permit_id,
    stable_smart_contract_reservation_id,
    stable_smart_contract_settlement_id,
    stable_transaction_id,
    stable_wallet_balance_id,
)
from aware_economy_ontology.price.rate_snapshot import RateSnapshot
from aware_economy_ontology.wallet.wallet import Wallet
from aware_economy_ontology.wallet.wallet_balance import WalletBalance
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.models.orm_model import ORMModel

_TModel = TypeVar("_TModel", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class EconomySmartContractSettlementLanes:
    price_projection_hash: str
    smart_contract_projection_hash: str
    wallet_projection_hash: str


@dataclass(frozen=True, slots=True)
class EconomySmartContractSettlementRuntimeContext:
    lane_binder: EconomyMetaRuntimeLaneBinder
    index: MetaGraphRuntimeIndex
    lanes: EconomySmartContractSettlementLanes


@dataclass(frozen=True, slots=True)
class EconomySmartContractSettlementOperationContext:
    actor_id: UUID | None


@dataclass(frozen=True, slots=True)
class SmartContractReservationPrepareReceipt:
    smart_contract_id: UUID
    permit_id: UUID
    reservation_id: UUID
    escrow_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    op_nonce: int
    coin_id: UUID
    max_cost: Decimal
    payer_balance: Decimal
    payer_held_balance: Decimal
    payer_available_balance: Decimal
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class ServiceOperationPermitEnsureReceipt:
    actor_id: UUID
    finance_role_key: str
    smart_contract_id: UUID
    permit_id: UUID
    parent_permit_id: UUID | None
    permit_nonce: int
    finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    price_schedule_id: UUID
    coin_id: UUID
    cap_amount: Decimal
    expires_at: datetime
    status: str
    refreshed: bool
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class SmartContractReservationReleaseReceipt:
    smart_contract_id: UUID
    permit_id: UUID
    reservation_id: UUID
    escrow_id: UUID
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    payer_wallet_balance_id: UUID
    coin_id: UUID
    released_amount: Decimal
    payer_balance: Decimal
    payer_previous_held_balance: Decimal
    payer_new_held_balance: Decimal
    payer_previous_available_balance: Decimal
    payer_new_available_balance: Decimal
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class SmartContractSettlementFinalizeReceipt:
    smart_contract_id: UUID
    permit_id: UUID
    reservation_id: UUID
    settlement_id: UUID
    transaction_id: UUID | None
    payer_finance_entity_id: UUID
    payer_wallet_id: UUID
    payer_wallet_public_id: UUID
    payer_wallet_balance_id: UUID
    payer_previous_balance: Decimal
    payer_new_balance: Decimal
    payer_previous_held_balance: Decimal
    payer_new_held_balance: Decimal
    payer_previous_available_balance: Decimal
    payer_new_available_balance: Decimal
    receiver_finance_entity_id: UUID
    receiver_wallet_id: UUID
    receiver_wallet_public_id: UUID
    receiver_wallet_balance_id: UUID
    receiver_previous_balance: Decimal
    receiver_new_balance: Decimal
    coin_id: UUID
    final_cost: Decimal
    status: str
    idempotent_replay: bool


def build_economy_smart_contract_settlement_lanes(
    *,
    index: MetaGraphRuntimeIndex,
) -> EconomySmartContractSettlementLanes:
    return EconomySmartContractSettlementLanes(
        price_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Price",
        ),
        smart_contract_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="SmartContract",
        ),
        wallet_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Wallet",
        ),
    )


def resolve_economy_smart_contract_settlement_runtime_context(
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder,
    index: MetaGraphRuntimeIndex,
) -> EconomySmartContractSettlementRuntimeContext:
    return EconomySmartContractSettlementRuntimeContext(
        lane_binder=lane_binder,
        index=index,
        lanes=build_economy_smart_contract_settlement_lanes(index=index),
    )


async def ensure_service_operation_permit(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    actor_id: UUID,
    finance_role_key: str,
    smart_contract_id: UUID,
    price_schedule_id: UUID,
    coin_id: UUID,
    cap_amount: Decimal,
    expires_at: datetime,
    commit: bool,
    publish: bool,
) -> ServiceOperationPermitEnsureReceipt:
    """Ensure an admitted actor has one sufficient active Service-operation permit."""

    cap_amount = positive_amount(
        cap_amount,
        field_name="service operation permit cap_amount",
    )
    expires_at = _require_future_datetime(
        expires_at,
        field_name="service operation permit expires_at",
    )
    readiness = await resolve_finance_entity_readiness(
        runtime_context=resolve_economy_finance_readiness_runtime_context(
            lane_binder=runtime_context.lane_binder,
            index=runtime_context.index,
        ),
        actor_id=actor_id,
        finance_role_key=finance_role_key,
    )
    if not readiness.finance_entity_ready or not readiness.wallet_ready:
        raise ValueError(
            "ensure_service_operation_permit requires committed FinanceEntity and Wallet readiness"
        )

    smart_contract = await _hydrate_smart_contract(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
    )
    if smart_contract.status != SmartContractStatus.active:
        raise ValueError(
            "ensure_service_operation_permit requires an active SmartContract: "
            f"status={_enum_value(smart_contract.status)}"
        )
    payer_members = [
        member
        for member in smart_contract.smart_contract_members
        if member.type == SmartContractMemberType.payer
        and member.finance_entity_id == readiness.finance_entity_id
    ]
    if len(payer_members) != 1:
        raise ValueError(
            "ensure_service_operation_permit requires exactly one admitted actor payer membership: "
            f"finance_entity_id={readiness.finance_entity_id} count={len(payer_members)}"
        )

    finance_permits = [
        permit
        for permit in smart_contract.smart_contract_permits
        if permit.finance_entity_id == readiness.finance_entity_id
    ]
    reusable = [
        permit
        for permit in finance_permits
        if _permit_satisfies_service_operation_envelope(
            permit=permit,
            smart_contract_id=smart_contract_id,
            price_schedule_id=price_schedule_id,
            coin_id=coin_id,
            cap_amount=cap_amount,
            expires_at=expires_at,
        )
    ]
    if reusable:
        permit = max(reusable, key=lambda item: item.permit_nonce)
        return _service_operation_permit_receipt(
            readiness=readiness,
            smart_contract_id=smart_contract_id,
            permit=permit,
            refreshed=False,
            idempotent_replay=True,
        )

    permit_nonce = (
        max(
            (permit.permit_nonce for permit in finance_permits),
            default=0,
        )
        + 1
    )
    prior_active_permits = [
        permit
        for permit in finance_permits
        if permit.status == SmartContractPermitStatus.active
    ]
    parent_id = (
        max(finance_permits, key=lambda item: item.permit_nonce).id
        if finance_permits
        else None
    )
    smart_contract_lane = _bind_smart_contract_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        smart_contract_id=smart_contract_id,
    )
    with smart_contract_lane.activate(commit=commit, publish=publish):
        for prior_permit in prior_active_permits:
            revoked = await prior_permit.revoke()
            if revoked.status != SmartContractPermitStatus.revoked:
                raise ValueError(
                    "service operation permit refresh failed to revoke prior permit"
                )
        permit = await smart_contract.open_session_permit(
            finance_entity_id=readiness.finance_entity_id,
            permit_nonce=permit_nonce,
            cap_amount=cap_amount,
            expires_at=expires_at,
            price_schedule_id=price_schedule_id,
            coin_id=coin_id,
            parent_id=parent_id,
        )
    _validate_service_operation_permit(
        permit=permit,
        smart_contract_id=smart_contract_id,
        finance_entity_id=readiness.finance_entity_id,
        permit_nonce=permit_nonce,
        price_schedule_id=price_schedule_id,
        coin_id=coin_id,
        cap_amount=cap_amount,
        expires_at=expires_at,
        parent_id=parent_id,
    )
    return _service_operation_permit_receipt(
        readiness=readiness,
        smart_contract_id=smart_contract_id,
        permit=permit,
        refreshed=bool(finance_permits),
        idempotent_replay=False,
    )


async def prepare_smart_contract_reservation(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    smart_contract_id: UUID,
    permit_id: UUID,
    permit_nonce: int,
    payer_finance_entity_id: UUID,
    payer_wallet_id: UUID,
    payer_wallet_public_id: UUID,
    args_hash: str,
    max_cost: Decimal,
    rate_snapshot_id: UUID,
    deadline: datetime,
    coin_id: UUID,
    commit: bool,
    publish: bool,
) -> SmartContractReservationPrepareReceipt:
    args_hash_norm = _require_non_empty(args_hash, field_name="args_hash")
    max_cost = positive_amount(max_cost, field_name="max_cost")
    if permit_nonce <= 0:
        raise ValueError("prepare_smart_contract_reservation requires permit_nonce > 0")

    payer_wallet = await _hydrate_wallet(
        runtime_context=runtime_context,
        wallet_id=payer_wallet_id,
        wallet_public_id=payer_wallet_public_id,
        error_context="smart-contract reservation payer wallet hydration",
    )
    payer_balance, payer_held, payer_available = _wallet_coin_balance_amounts(
        wallet=payer_wallet,
        coin_id=coin_id,
    )
    smart_contract = await _hydrate_smart_contract(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
    )
    permit = _require_permit(
        smart_contract=smart_contract,
        permit_id=permit_id,
    )
    _validate_permit_envelope(
        permit=permit,
        smart_contract_id=smart_contract_id,
        permit_nonce=permit_nonce,
        payer_finance_entity_id=payer_finance_entity_id,
        coin_id=coin_id,
    )
    await _validate_rate_snapshot_matches_permit_schedule(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
        permit=permit,
        rate_snapshot_id=rate_snapshot_id,
    )
    existing = _find_reservation_by_args_hash(
        permit=permit,
        args_hash=args_hash_norm,
    )
    if existing is not None:
        _validate_existing_reservation(
            reservation=existing,
            permit_id=permit_id,
            op_nonce=existing.op_nonce,
            args_hash=args_hash_norm,
            max_cost=max_cost,
            rate_snapshot_id=rate_snapshot_id,
            coin_id=coin_id,
        )
        return SmartContractReservationPrepareReceipt(
            smart_contract_id=smart_contract_id,
            permit_id=permit_id,
            reservation_id=existing.id,
            escrow_id=_reservation_escrow_id(
                reservation=existing,
                payer_wallet_public_id=payer_wallet_public_id,
            ),
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            op_nonce=existing.op_nonce,
            coin_id=coin_id,
            max_cost=positive_amount(
                existing.max_cost,
                field_name="reservation max_cost",
            ),
            payer_balance=payer_balance,
            payer_held_balance=payer_held,
            payer_available_balance=payer_available,
            status=_enum_value(existing.status),
            idempotent_replay=True,
        )

    _validate_permit_cumulative_cap(
        permit=permit,
        new_max_cost=max_cost,
    )

    if payer_available < max_cost:
        raise ValueError(
            "prepare_smart_contract_reservation insufficient payer wallet available balance: "
            f"wallet_id={payer_wallet_id} coin_id={coin_id} available={payer_available} "
            f"held={payer_held} balance={payer_balance} max_cost={max_cost}"
        )

    op_nonce = _next_permit_op_nonce(permit=permit)
    smart_contract_lane = _bind_smart_contract_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        smart_contract_id=smart_contract_id,
    )
    with smart_contract_lane.activate(commit=commit, publish=publish):
        reservation = await smart_contract.reserve_operation(
            permit_id=permit_id,
            permit_nonce=permit_nonce,
            finance_entity_id=payer_finance_entity_id,
            payer_wallet_public_id=payer_wallet_public_id,
            op_nonce=op_nonce,
            args_hash=args_hash_norm,
            max_cost=max_cost,
            rate_snapshot_id=rate_snapshot_id,
            deadline=deadline,
            coin_id=coin_id,
        )

    wallet_balance = await _reserve_wallet_hold(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet=payer_wallet,
        coin_id=coin_id,
        amount=max_cost,
        commit=commit,
        publish=publish,
    )
    payer_balance, payer_held, payer_available = wallet_balance_amounts(wallet_balance)

    _validate_existing_reservation(
        reservation=reservation,
        permit_id=permit_id,
        op_nonce=op_nonce,
        args_hash=args_hash_norm,
        max_cost=max_cost,
        rate_snapshot_id=rate_snapshot_id,
        coin_id=coin_id,
    )
    return SmartContractReservationPrepareReceipt(
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        reservation_id=reservation.id,
        escrow_id=_reservation_escrow_id(
            reservation=reservation,
            payer_wallet_public_id=payer_wallet_public_id,
        ),
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        op_nonce=op_nonce,
        coin_id=coin_id,
        max_cost=positive_amount(
            reservation.max_cost,
            field_name="reservation max_cost",
        ),
        payer_balance=payer_balance,
        payer_held_balance=payer_held,
        payer_available_balance=payer_available,
        status=_enum_value(reservation.status),
        idempotent_replay=False,
    )


async def finalize_smart_contract_settlement(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    smart_contract_id: UUID,
    permit_id: UUID,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    final_cost: Decimal,
    commit: bool,
    publish: bool,
) -> SmartContractSettlementFinalizeReceipt:
    final_cost = non_negative_amount(
        final_cost,
        field_name="finalize_smart_contract_settlement final_cost",
    )

    smart_contract = await _hydrate_smart_contract(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
    )
    reservation = _require_reservation(
        smart_contract=smart_contract,
        reservation_id=reservation_id,
    )
    settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=reservation_id,
    )
    existing_settlement = _find_settlement(
        reservation=reservation,
        settlement_id=settlement_id,
    )
    payer_wallet = await _hydrate_wallet(
        runtime_context=runtime_context,
        wallet_id=payer_wallet_id,
        wallet_public_id=payer_wallet_public_id,
        error_context="smart-contract settlement payer wallet hydration",
    )
    receiver_wallet = await _hydrate_wallet(
        runtime_context=runtime_context,
        wallet_id=receiver_wallet_id,
        wallet_public_id=receiver_wallet_public_id,
        error_context="smart-contract settlement receiver wallet hydration",
    )
    reserved_amount = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    if final_cost > reserved_amount:
        raise ValueError(
            "finalize_smart_contract_settlement final_cost exceeds reserved max_cost: "
            f"final_cost={final_cost} reserved_amount={reserved_amount}"
        )
    if reservation.status in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError(
            "reservation is terminal and cannot prepare settlement: "
            f"{_enum_value(reservation.status)}"
        )
    (
        payer_previous,
        payer_previous_held,
        payer_previous_available,
    ) = _wallet_coin_balance_amounts(wallet=payer_wallet, coin_id=coin_id)
    receiver_previous = _wallet_coin_balance(wallet=receiver_wallet, coin_id=coin_id)
    transaction_id = (
        stable_transaction_id(
            capital_origin_id=payer_wallet_public_id,
            target_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            nonce=reservation.op_nonce,
        )
        if final_cost > ZERO_AMOUNT
        else None
    )

    if _is_settled_replay(
        reservation=reservation,
        settlement=existing_settlement,
    ):
        _validate_existing_settlement(
            settlement=existing_settlement,
            reservation_id=reservation_id,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_finance_entity_id=receiver_finance_entity_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            final_cost=final_cost,
        )
        return SmartContractSettlementFinalizeReceipt(
            smart_contract_id=smart_contract_id,
            permit_id=permit_id,
            reservation_id=reservation_id,
            settlement_id=existing_settlement.id,
            transaction_id=transaction_id,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            payer_wallet_balance_id=_wallet_balance_id(
                wallet=payer_wallet,
                coin_id=coin_id,
            ),
            payer_previous_balance=payer_previous,
            payer_new_balance=payer_previous,
            payer_previous_held_balance=payer_previous_held,
            payer_new_held_balance=payer_previous_held,
            payer_previous_available_balance=payer_previous_available,
            payer_new_available_balance=payer_previous_available,
            receiver_finance_entity_id=receiver_finance_entity_id,
            receiver_wallet_id=receiver_wallet_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            receiver_wallet_balance_id=_wallet_balance_id(
                wallet=receiver_wallet,
                coin_id=coin_id,
            ),
            receiver_previous_balance=receiver_previous,
            receiver_new_balance=receiver_previous,
            coin_id=coin_id,
            final_cost=final_cost,
            status=_enum_value(existing_settlement.status),
            idempotent_replay=True,
        )

    payer_new = payer_previous - final_cost
    payer_new_held = payer_previous_held - reserved_amount
    receiver_new = receiver_previous + final_cost
    _validate_conservation(
        payer_previous=payer_previous,
        payer_new=payer_new,
        receiver_previous=receiver_previous,
        receiver_new=receiver_new,
        final_cost=final_cost,
    )
    _validate_hold_settlement(
        payer_previous_held=payer_previous_held,
        payer_new_held=payer_new_held,
        reserved_amount=reserved_amount,
        final_cost=final_cost,
    )

    smart_contract_lane = _bind_smart_contract_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        smart_contract_id=smart_contract_id,
    )
    with smart_contract_lane.activate(commit=commit, publish=publish):
        prepared = await smart_contract.prepare_settlement(
            permit_id=permit_id,
            reservation_id=reservation_id,
            final_cost=final_cost,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_finance_entity_id=receiver_finance_entity_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
        )

    _validate_existing_settlement(
        settlement=prepared,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
    )

    payer_balance = await _settle_wallet_hold(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet=payer_wallet,
        coin_id=coin_id,
        reserved_amount=reserved_amount,
        final_cost=final_cost,
        commit=commit,
        publish=publish,
    )
    receiver_balance = await _reconcile_wallet_balance(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet=receiver_wallet,
        coin_id=coin_id,
        expected_balance=receiver_previous,
        new_balance=receiver_new,
        commit=commit,
        publish=publish,
    )

    refreshed_smart_contract = await _hydrate_smart_contract(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
    )
    finalize_lane = _bind_smart_contract_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        smart_contract_id=smart_contract_id,
    )
    with finalize_lane.activate(commit=commit, publish=publish):
        settlement = await refreshed_smart_contract.finalize_settlement(
            permit_id=permit_id,
            reservation_id=reservation_id,
            final_cost=final_cost,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_public_id=payer_wallet_public_id,
            receiver_finance_entity_id=receiver_finance_entity_id,
            receiver_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
        )

    _validate_existing_settlement(
        settlement=settlement,
        reservation_id=reservation_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_public_id=payer_wallet_public_id,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        coin_id=coin_id,
        final_cost=final_cost,
    )
    payer_new_total, payer_new_held, payer_new_available = wallet_balance_amounts(
        payer_balance
    )
    return SmartContractSettlementFinalizeReceipt(
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        reservation_id=reservation_id,
        settlement_id=settlement.id,
        transaction_id=transaction_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        payer_wallet_balance_id=payer_balance.id,
        payer_previous_balance=payer_previous,
        payer_new_balance=payer_new_total,
        payer_previous_held_balance=payer_previous_held,
        payer_new_held_balance=payer_new_held,
        payer_previous_available_balance=payer_previous_available,
        payer_new_available_balance=payer_new_available,
        receiver_finance_entity_id=receiver_finance_entity_id,
        receiver_wallet_id=receiver_wallet_id,
        receiver_wallet_public_id=receiver_wallet_public_id,
        receiver_wallet_balance_id=receiver_balance.id,
        receiver_previous_balance=receiver_previous,
        receiver_new_balance=non_negative_amount(
            receiver_balance.balance,
            field_name="receiver wallet balance",
        ),
        coin_id=coin_id,
        final_cost=final_cost,
        status=_enum_value(settlement.status),
        idempotent_replay=False,
    )


async def release_smart_contract_reservation(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    smart_contract_id: UUID,
    permit_id: UUID,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_id: UUID,
    payer_wallet_public_id: UUID,
    coin_id: UUID,
    status: ReservationStatus,
    commit: bool,
    publish: bool,
) -> SmartContractReservationReleaseReceipt:
    if status not in {ReservationStatus.cancelled, ReservationStatus.expired}:
        raise ValueError(
            "release_smart_contract_reservation status must be cancelled or expired"
        )

    smart_contract = await _hydrate_smart_contract(
        runtime_context=runtime_context,
        smart_contract_id=smart_contract_id,
    )
    reservation = _require_reservation(
        smart_contract=smart_contract,
        reservation_id=reservation_id,
    )
    permit = _require_permit_for_reservation(
        smart_contract=smart_contract,
        reservation_id=reservation_id,
    )
    if str(permit.id) != str(permit_id):
        raise ValueError("smart-contract reservation permit_id mismatch")
    if str(permit.finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError("smart-contract reservation payer_finance_entity_id mismatch")
    if permit.coin_id != coin_id:
        raise ValueError("smart-contract reservation coin_id mismatch")
    reserved_amount = positive_amount(
        reservation.max_cost,
        field_name="reservation max_cost",
    )
    escrow_id = _reservation_escrow_id(
        reservation=reservation,
        payer_wallet_public_id=payer_wallet_public_id,
    )
    payer_wallet = await _hydrate_wallet(
        runtime_context=runtime_context,
        wallet_id=payer_wallet_id,
        wallet_public_id=payer_wallet_public_id,
        error_context="smart-contract reservation release payer wallet hydration",
    )
    (
        payer_balance,
        payer_previous_held,
        payer_previous_available,
    ) = _wallet_coin_balance_amounts(wallet=payer_wallet, coin_id=coin_id)

    if reservation.status == status:
        return SmartContractReservationReleaseReceipt(
            smart_contract_id=smart_contract_id,
            permit_id=permit_id,
            reservation_id=reservation_id,
            escrow_id=escrow_id,
            payer_finance_entity_id=payer_finance_entity_id,
            payer_wallet_id=payer_wallet_id,
            payer_wallet_public_id=payer_wallet_public_id,
            payer_wallet_balance_id=_wallet_balance_id(
                wallet=payer_wallet,
                coin_id=coin_id,
            ),
            coin_id=coin_id,
            released_amount=reserved_amount,
            payer_balance=payer_balance,
            payer_previous_held_balance=payer_previous_held,
            payer_new_held_balance=payer_previous_held,
            payer_previous_available_balance=payer_previous_available,
            payer_new_available_balance=payer_previous_available,
            status=_enum_value(reservation.status),
            idempotent_replay=True,
        )

    smart_contract_lane = _bind_smart_contract_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        smart_contract_id=smart_contract_id,
    )
    with smart_contract_lane.activate(commit=commit, publish=publish):
        released_reservation = await smart_contract.release_reservation(
            permit_id=permit_id,
            reservation_id=reservation_id,
            status=status,
        )

    if released_reservation.status != status:
        raise ValueError(
            "release_smart_contract_reservation status mismatch after release: "
            f"actual={released_reservation.status} expected={status}"
        )

    wallet_balance = await _release_wallet_hold(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet=payer_wallet,
        coin_id=coin_id,
        amount=reserved_amount,
        commit=commit,
        publish=publish,
    )
    payer_balance, payer_new_held, payer_new_available = wallet_balance_amounts(
        wallet_balance
    )
    return SmartContractReservationReleaseReceipt(
        smart_contract_id=smart_contract_id,
        permit_id=permit_id,
        reservation_id=reservation_id,
        escrow_id=escrow_id,
        payer_finance_entity_id=payer_finance_entity_id,
        payer_wallet_id=payer_wallet_id,
        payer_wallet_public_id=payer_wallet_public_id,
        payer_wallet_balance_id=wallet_balance.id,
        coin_id=coin_id,
        released_amount=reserved_amount,
        payer_balance=payer_balance,
        payer_previous_held_balance=payer_previous_held,
        payer_new_held_balance=payer_new_held,
        payer_previous_available_balance=payer_previous_available,
        payer_new_available_balance=payer_new_available,
        status=_enum_value(released_reservation.status),
        idempotent_replay=False,
    )


def _bind_smart_contract_lane(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    smart_contract_id: UUID,
) -> EconomyMetaRuntimeLane:
    return runtime_context.lane_binder.bind(
        branch_id=smart_contract_id,
        projection=runtime_context.lanes.smart_contract_projection_hash,
        actor_id=operation_context.actor_id,
    )


def _bind_wallet_lane(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    wallet_id: UUID,
) -> EconomyMetaRuntimeLane:
    return runtime_context.lane_binder.bind(
        branch_id=wallet_id,
        projection=runtime_context.lanes.wallet_projection_hash,
        actor_id=operation_context.actor_id,
    )


async def _hydrate_smart_contract(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    smart_contract_id: UUID,
) -> SmartContract:
    return await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=smart_contract_id,
        projection_hash=runtime_context.lanes.smart_contract_projection_hash,
        orm_class=SmartContract,
        object_id=smart_contract_id,
        error_context="smart-contract settlement SmartContract hydration",
    )


async def _hydrate_wallet(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    wallet_id: UUID,
    wallet_public_id: UUID,
    error_context: str,
) -> Wallet:
    wallet = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=wallet_id,
        projection_hash=runtime_context.lanes.wallet_projection_hash,
        orm_class=Wallet,
        object_id=wallet_id,
        error_context=error_context,
    )
    if wallet.wallet_public_id != wallet_public_id:
        raise ValueError(f"{error_context}: wallet_public_id mismatch")
    return wallet


async def _validate_rate_snapshot_matches_permit_schedule(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    smart_contract_id: UUID,
    permit: SmartContractPermit,
    rate_snapshot_id: UUID,
) -> None:
    snapshot = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=smart_contract_id,
        projection_hash=runtime_context.lanes.price_projection_hash,
        orm_class=RateSnapshot,
        object_id=rate_snapshot_id,
        error_context=(
            "smart-contract reservation RateSnapshot hydration for permit schedule"
        ),
    )
    if snapshot.price_schedule_id != permit.price_schedule_id:
        raise ValueError(
            "smart-contract reservation rate_snapshot price_schedule_id mismatch: "
            f"permit_price_schedule_id={permit.price_schedule_id} "
            f"rate_snapshot_price_schedule_id={snapshot.price_schedule_id} "
            f"rate_snapshot_id={rate_snapshot_id}"
        )


async def _reconcile_wallet_balance(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    wallet: Wallet,
    coin_id: UUID,
    expected_balance: Decimal,
    new_balance: Decimal,
    commit: bool,
    publish: bool,
) -> WalletBalance:
    wallet_lane = _bind_wallet_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet_id=wallet.id,
    )
    with wallet_lane.activate(commit=commit, publish=publish):
        return await wallet.reconcile_coin_balance(
            coin_id=coin_id,
            expected_balance=expected_balance,
            new_balance=new_balance,
        )


async def _reserve_wallet_hold(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    wallet: Wallet,
    coin_id: UUID,
    amount: Decimal,
    commit: bool,
    publish: bool,
) -> WalletBalance:
    wallet_lane = _bind_wallet_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet_id=wallet.id,
    )
    with wallet_lane.activate(commit=commit, publish=publish):
        return await wallet.reserve_coin_hold(
            coin_id=coin_id,
            amount=amount,
        )


async def _release_wallet_hold(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    wallet: Wallet,
    coin_id: UUID,
    amount: Decimal,
    commit: bool,
    publish: bool,
) -> WalletBalance:
    wallet_lane = _bind_wallet_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet_id=wallet.id,
    )
    with wallet_lane.activate(commit=commit, publish=publish):
        return await wallet.release_coin_hold(
            coin_id=coin_id,
            amount=amount,
        )


async def _settle_wallet_hold(
    *,
    runtime_context: EconomySmartContractSettlementRuntimeContext,
    operation_context: EconomySmartContractSettlementOperationContext,
    wallet: Wallet,
    coin_id: UUID,
    reserved_amount: Decimal,
    final_cost: Decimal,
    commit: bool,
    publish: bool,
) -> WalletBalance:
    wallet_lane = _bind_wallet_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        wallet_id=wallet.id,
    )
    with wallet_lane.activate(commit=commit, publish=publish):
        return await wallet.settle_coin_hold(
            coin_id=coin_id,
            reserved_amount=reserved_amount,
            final_cost=final_cost,
        )


async def _hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    orm_class: type[_TModel],
    object_id: UUID,
    error_context: str,
) -> _TModel:
    obj = await _maybe_hydrate_committed_lane_object(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        orm_class=orm_class,
        object_id=object_id,
    )
    if obj is None:
        raise RuntimeError(
            f"{error_context}: missing {orm_class.__name__} object_id={object_id}"
        )
    return obj


async def _maybe_hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    orm_class: type[_TModel],
    object_id: UUID,
) -> _TModel | None:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Economy smart-contract settlement could not resolve projection hash: "
            + repr(projection_hash)
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
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
        branch_id=branch_id,
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


def _find_reservation(
    *,
    smart_contract: SmartContract,
    reservation_id: UUID,
) -> SmartContractReservation | None:
    for permit in smart_contract.smart_contract_permits:
        for reservation in permit.smart_contract_reservations:
            if str(reservation.id) == str(reservation_id):
                return reservation
    return None


def _require_permit(
    *,
    smart_contract: SmartContract,
    permit_id: UUID,
) -> SmartContractPermit:
    for permit in smart_contract.smart_contract_permits:
        if str(permit.id) == str(permit_id):
            return permit
    raise ValueError(f"smart-contract permit not found: {permit_id}")


def _validate_permit_envelope(
    *,
    permit: SmartContractPermit,
    smart_contract_id: UUID,
    permit_nonce: int,
    payer_finance_entity_id: UUID,
    coin_id: UUID,
) -> None:
    expected_permit_id = stable_smart_contract_permit_id(
        smart_contract_id=smart_contract_id,
        finance_entity_id=payer_finance_entity_id,
        permit_nonce=permit_nonce,
    )
    if str(permit.id) != str(expected_permit_id):
        raise ValueError(
            "smart-contract spend envelope permit_id mismatch: "
            f"actual={permit.id} expected={expected_permit_id}"
        )
    if permit.smart_contract_id != smart_contract_id:
        raise ValueError("smart-contract spend envelope smart_contract_id mismatch")
    if str(permit.finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError(
            "smart-contract spend envelope finance_entity_id must match payer"
        )
    if int(permit.permit_nonce) != int(permit_nonce):
        raise ValueError("smart-contract spend envelope permit_nonce mismatch")
    if permit.coin_id != coin_id:
        raise ValueError("smart-contract spend envelope coin_id mismatch")
    if permit.status != SmartContractPermitStatus.active:
        raise ValueError(
            f"smart-contract spend envelope is not active: {permit.status}"
        )
    permit_now = (
        datetime.now(permit.expires_at.tzinfo)
        if permit.expires_at.tzinfo is not None
        else datetime.utcnow()
    )
    if permit.expires_at <= permit_now:
        raise ValueError("smart-contract spend envelope is expired")


def _find_reservation_by_args_hash(
    *,
    permit: SmartContractPermit,
    args_hash: str,
) -> SmartContractReservation | None:
    for reservation in permit.smart_contract_reservations:
        if reservation.args_hash == args_hash:
            return reservation
    return None


def _next_permit_op_nonce(*, permit: SmartContractPermit) -> int:
    max_reservation_nonce = max(
        (
            int(reservation.op_nonce)
            for reservation in permit.smart_contract_reservations
        ),
        default=0,
    )
    current_nonce = max(int(getattr(permit, "nonce", 0)), max_reservation_nonce)
    return current_nonce + 1


def _validate_permit_cumulative_cap(
    *,
    permit: SmartContractPermit,
    new_max_cost: Decimal,
) -> None:
    cap_amount = positive_amount(
        permit.cap_amount,
        field_name="smart contract permit cap_amount",
    )
    committed_amount = _permit_committed_envelope_amount(permit=permit)
    requested_total = committed_amount + new_max_cost
    if requested_total > cap_amount:
        raise ValueError(
            "smart-contract spend envelope cap exceeded: "
            f"committed={committed_amount} requested={new_max_cost} "
            f"cap_amount={cap_amount}"
        )


def _permit_committed_envelope_amount(*, permit: SmartContractPermit) -> Decimal:
    total = ZERO_AMOUNT
    for reservation in permit.smart_contract_reservations:
        status = _enum_value(reservation.status)
        if status in {
            ReservationStatus.cancelled.value,
            ReservationStatus.expired.value,
        }:
            continue
        if (
            status == ReservationStatus.settled.value
            and reservation.final_cost is not None
        ):
            total += non_negative_amount(
                reservation.final_cost,
                field_name="settled reservation final_cost",
            )
            continue
        total += positive_amount(
            reservation.max_cost,
            field_name="active reservation max_cost",
        )
    return total


def _require_reservation(
    *,
    smart_contract: SmartContract,
    reservation_id: UUID,
) -> SmartContractReservation:
    reservation = _find_reservation(
        smart_contract=smart_contract,
        reservation_id=reservation_id,
    )
    if reservation is None:
        raise ValueError(f"reservation not found: {reservation_id}")
    return reservation


def _require_permit_for_reservation(
    *,
    smart_contract: SmartContract,
    reservation_id: UUID,
) -> SmartContractPermit:
    for permit in smart_contract.smart_contract_permits:
        for reservation in permit.smart_contract_reservations:
            if str(reservation.id) == str(reservation_id):
                return permit
    raise ValueError(f"reservation not found: {reservation_id}")


def _find_settlement(
    *,
    reservation: SmartContractReservation,
    settlement_id: UUID,
) -> SmartContractSettlement | None:
    for settlement in reservation.smart_contract_settlements:
        if str(settlement.id) == str(settlement_id):
            return settlement
    return None


def _is_settled_replay(
    *,
    reservation: SmartContractReservation,
    settlement: SmartContractSettlement | None,
) -> bool:
    return (
        settlement is not None
        and reservation.status == ReservationStatus.settled
        and settlement.status == SmartContractSettlementStatus.settled
    )


def _validate_existing_reservation(
    *,
    reservation: SmartContractReservation,
    permit_id: UUID,
    op_nonce: int,
    args_hash: str,
    max_cost: Decimal,
    rate_snapshot_id: UUID,
    coin_id: UUID,
) -> None:
    expected_reservation_id = stable_smart_contract_reservation_id(
        smart_contract_permit_id=permit_id,
        op_nonce=op_nonce,
    )
    if str(reservation.id) != str(expected_reservation_id):
        raise ValueError("smart-contract reservation id mismatch")
    if str(reservation.smart_contract_permit_id) != str(permit_id):
        raise ValueError("smart-contract reservation permit_id mismatch")
    if reservation.op_nonce != op_nonce:
        raise ValueError("smart-contract reservation op_nonce mismatch")
    if reservation.args_hash != args_hash:
        raise ValueError("smart-contract reservation args_hash mismatch")
    if not amount_equal(reservation.max_cost, max_cost):
        raise ValueError("smart-contract reservation max_cost mismatch")
    if str(reservation.rate_snapshot_id) != str(rate_snapshot_id):
        raise ValueError("smart-contract reservation rate_snapshot_id mismatch")
    if reservation.escrow is not None and str(reservation.escrow.coin_id) != str(
        coin_id
    ):
        raise ValueError("smart-contract reservation escrow coin_id mismatch")


def _validate_existing_settlement(
    *,
    settlement: SmartContractSettlement,
    reservation_id: UUID,
    payer_finance_entity_id: UUID,
    payer_wallet_public_id: UUID,
    receiver_finance_entity_id: UUID,
    receiver_wallet_public_id: UUID,
    coin_id: UUID,
    final_cost: Decimal,
) -> None:
    expected_settlement_id = stable_smart_contract_settlement_id(
        smart_contract_reservation_id=reservation_id,
    )
    if str(settlement.id) != str(expected_settlement_id):
        raise ValueError("smart-contract settlement id mismatch")
    if str(settlement.smart_contract_reservation_id) != str(reservation_id):
        raise ValueError("smart-contract settlement reservation_id mismatch")
    if str(settlement.payer_finance_entity_id) != str(payer_finance_entity_id):
        raise ValueError("smart-contract settlement payer_finance_entity_id mismatch")
    if str(settlement.payer_wallet_public_id) != str(payer_wallet_public_id):
        raise ValueError("smart-contract settlement payer_wallet_public_id mismatch")
    if str(settlement.receiver_finance_entity_id) != str(receiver_finance_entity_id):
        raise ValueError(
            "smart-contract settlement receiver_finance_entity_id mismatch"
        )
    if str(settlement.receiver_wallet_public_id) != str(receiver_wallet_public_id):
        raise ValueError("smart-contract settlement receiver_wallet_public_id mismatch")
    if str(settlement.coin_id) != str(coin_id):
        raise ValueError("smart-contract settlement coin_id mismatch")
    if not amount_equal(settlement.final_cost, final_cost):
        raise ValueError("smart-contract settlement final_cost mismatch")


def _reservation_escrow_id(
    *,
    reservation: SmartContractReservation,
    payer_wallet_public_id: UUID,
) -> UUID:
    expected = stable_escrow_id(
        wallet_public_id=payer_wallet_public_id,
        op_nonce=reservation.op_nonce,
    )
    if reservation.escrow_id is not None and str(reservation.escrow_id) != str(
        expected
    ):
        raise ValueError("smart-contract reservation escrow_id mismatch")
    if reservation.escrow is not None and str(reservation.escrow.id) != str(expected):
        raise ValueError("smart-contract reservation escrow relation mismatch")
    return expected


def _wallet_coin_balance(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> Decimal:
    balance, _, _ = _wallet_coin_balance_amounts(wallet=wallet, coin_id=coin_id)
    return balance


def _wallet_coin_balance_amounts(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> tuple[Decimal, Decimal, Decimal]:
    balance = _find_wallet_balance(wallet=wallet, coin_id=coin_id)
    if balance is None:
        return ZERO_AMOUNT, ZERO_AMOUNT, ZERO_AMOUNT
    return wallet_balance_amounts(balance)


def _wallet_balance_id(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> UUID:
    balance = _find_wallet_balance(wallet=wallet, coin_id=coin_id)
    return (
        balance.id
        if balance is not None
        else stable_wallet_balance_id(wallet_id=wallet.id, coin_id=coin_id)
    )


def _find_wallet_balance(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> WalletBalance | None:
    matches = [
        wallet_balance
        for wallet_balance in wallet.wallet_balances
        if wallet_balance.wallet_id == wallet.id and wallet_balance.coin_id == coin_id
    ]
    if len(matches) > 1:
        raise ValueError(
            "smart-contract settlement wallet balance is ambiguous: "
            f"wallet_id={wallet.id} coin_id={coin_id} count={len(matches)}"
        )
    return matches[0] if matches else None


def _validate_conservation(
    *,
    payer_previous: Decimal,
    payer_new: Decimal,
    receiver_previous: Decimal,
    receiver_new: Decimal,
    final_cost: Decimal,
) -> None:
    if payer_new < ZERO_AMOUNT:
        raise ValueError(
            "finalize_smart_contract_settlement insufficient payer balance"
        )
    payer_delta = payer_previous - payer_new
    receiver_delta = receiver_new - receiver_previous
    if payer_delta < ZERO_AMOUNT:
        raise ValueError("finalize_smart_contract_settlement payer delta must be >= 0")
    if receiver_delta < ZERO_AMOUNT:
        raise ValueError(
            "finalize_smart_contract_settlement receiver delta must be >= 0"
        )
    if payer_delta != receiver_delta:
        raise ValueError(
            "finalize_smart_contract_settlement conservation mismatch: "
            f"payer_delta={payer_delta} receiver_delta={receiver_delta}"
        )
    if payer_delta != final_cost:
        raise ValueError(
            "finalize_smart_contract_settlement amount mismatch: "
            f"payer_delta={payer_delta} final_cost={final_cost}"
        )


def _validate_hold_settlement(
    *,
    payer_previous_held: Decimal,
    payer_new_held: Decimal,
    reserved_amount: Decimal,
    final_cost: Decimal,
) -> None:
    if payer_new_held < ZERO_AMOUNT:
        raise ValueError(
            "finalize_smart_contract_settlement insufficient payer held balance"
        )
    if final_cost > reserved_amount:
        raise ValueError(
            "finalize_smart_contract_settlement final_cost exceeds reserved amount"
        )
    held_delta = payer_previous_held - payer_new_held
    if held_delta != reserved_amount:
        raise ValueError(
            "finalize_smart_contract_settlement held amount mismatch: "
            f"held_delta={held_delta} reserved_amount={reserved_amount}"
        )


def _require_non_empty(value: str, *, field_name: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    return raw


def _require_future_datetime(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    normalized = value.astimezone(UTC)
    if normalized <= datetime.now(UTC):
        raise ValueError(f"{field_name} must be in the future")
    return normalized


def _permit_satisfies_service_operation_envelope(
    *,
    permit: SmartContractPermit,
    smart_contract_id: UUID,
    price_schedule_id: UUID,
    coin_id: UUID,
    cap_amount: Decimal,
    expires_at: datetime,
) -> bool:
    if permit.status != SmartContractPermitStatus.active:
        return False
    if permit.smart_contract_id != smart_contract_id:
        return False
    if permit.price_schedule_id != price_schedule_id or permit.coin_id != coin_id:
        return False
    if permit.expires_at.tzinfo is None:
        return False
    if permit.expires_at.astimezone(UTC) < expires_at:
        return False
    return permit.cap_amount >= cap_amount


def _validate_service_operation_permit(
    *,
    permit: SmartContractPermit,
    smart_contract_id: UUID,
    finance_entity_id: UUID,
    permit_nonce: int,
    price_schedule_id: UUID,
    coin_id: UUID,
    cap_amount: Decimal,
    expires_at: datetime,
    parent_id: UUID | None,
) -> None:
    expected_id = stable_smart_contract_permit_id(
        smart_contract_id=smart_contract_id,
        finance_entity_id=finance_entity_id,
        permit_nonce=permit_nonce,
    )
    if permit.id != expected_id:
        raise ValueError("service operation permit id mismatch")
    if permit.smart_contract_id != smart_contract_id:
        raise ValueError("service operation permit smart_contract_id mismatch")
    if permit.finance_entity_id != finance_entity_id:
        raise ValueError("service operation permit finance_entity_id mismatch")
    if permit.permit_nonce != permit_nonce:
        raise ValueError("service operation permit nonce mismatch")
    if permit.price_schedule_id != price_schedule_id:
        raise ValueError("service operation permit price_schedule_id mismatch")
    if permit.coin_id != coin_id:
        raise ValueError("service operation permit coin_id mismatch")
    if not amount_equal(permit.cap_amount, cap_amount):
        raise ValueError("service operation permit cap_amount mismatch")
    if permit.expires_at != expires_at:
        raise ValueError("service operation permit expires_at mismatch")
    if permit.status != SmartContractPermitStatus.active:
        raise ValueError("service operation permit must be active")
    if permit.smart_contract_permit_id != parent_id:
        raise ValueError("service operation permit parent_id mismatch")


def _service_operation_permit_receipt(
    *,
    readiness: FinanceEntityReadinessReceipt,
    smart_contract_id: UUID,
    permit: SmartContractPermit,
    refreshed: bool,
    idempotent_replay: bool,
) -> ServiceOperationPermitEnsureReceipt:
    return ServiceOperationPermitEnsureReceipt(
        actor_id=readiness.actor_id,
        finance_role_key=readiness.finance_role_key,
        smart_contract_id=smart_contract_id,
        permit_id=permit.id,
        parent_permit_id=permit.smart_contract_permit_id,
        permit_nonce=permit.permit_nonce,
        finance_entity_id=readiness.finance_entity_id,
        wallet_id=readiness.wallet_id,
        wallet_public_id=readiness.wallet_public_id,
        price_schedule_id=permit.price_schedule_id,
        coin_id=permit.coin_id,
        cap_amount=positive_amount(
            permit.cap_amount,
            field_name="service operation permit cap_amount",
        ),
        expires_at=permit.expires_at,
        status=_enum_value(permit.status),
        refreshed=refreshed,
        idempotent_replay=idempotent_replay,
    )


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


__all__ = [
    "EconomySmartContractSettlementOperationContext",
    "EconomySmartContractSettlementRuntimeContext",
    "ServiceOperationPermitEnsureReceipt",
    "SmartContractReservationPrepareReceipt",
    "SmartContractReservationReleaseReceipt",
    "SmartContractSettlementFinalizeReceipt",
    "build_economy_smart_contract_settlement_lanes",
    "finalize_smart_contract_settlement",
    "ensure_service_operation_permit",
    "prepare_smart_contract_reservation",
    "release_smart_contract_reservation",
    "resolve_economy_smart_contract_settlement_runtime_context",
]
