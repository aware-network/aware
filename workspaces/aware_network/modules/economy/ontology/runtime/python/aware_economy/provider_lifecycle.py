from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from aware_code.types import JsonObject
from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.meta_runtime import (
    EconomyMetaRuntimeLane,
    EconomyMetaRuntimeLaneBinder,
)
from aware_economy.ontology.materialization import wallet_balance_amounts
from aware_economy_ontology.stable_ids import (
    stable_provider_lifecycle_receipt_id,
    stable_wallet_balance_id,
)
from aware_economy_ontology.transaction.provider_lifecycle_receipt import (
    ProviderLifecycleReceipt,
)
from aware_economy_ontology.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
    ProviderLifecycleStatus,
)
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
class EconomyProviderLifecycleLanes:
    provider_lifecycle_receipt_projection_hash: str
    wallet_projection_hash: str


@dataclass(frozen=True, slots=True)
class EconomyProviderLifecycleRuntimeContext:
    lane_binder: EconomyMetaRuntimeLaneBinder
    index: MetaGraphRuntimeIndex
    lanes: EconomyProviderLifecycleLanes


@dataclass(frozen=True, slots=True)
class EconomyProviderLifecycleOperationContext:
    actor_id: UUID | None


@dataclass(frozen=True, slots=True)
class ProviderLifecycleRecordReceipt:
    provider_lifecycle_receipt_id: UUID
    wallet_balance_id: UUID
    provider_key: str
    provider_event_id: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    idempotency_key: str
    provider_finance_entity_id: UUID
    wallet_finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    coin_id: UUID
    amount: Decimal
    event_kind: str
    status: str
    previous_balance: Decimal
    new_balance: Decimal
    previous_held_balance: Decimal
    new_held_balance: Decimal
    previous_available_balance: Decimal
    new_available_balance: Decimal
    provider_payment_reference: str
    provider_payload_hash: str
    transaction_id: UUID
    transaction_external_id: UUID
    idempotent_replay: bool


def build_economy_provider_lifecycle_lanes(
    *,
    index: MetaGraphRuntimeIndex,
) -> EconomyProviderLifecycleLanes:
    return EconomyProviderLifecycleLanes(
        provider_lifecycle_receipt_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="ProviderLifecycleReceipt",
        ),
        wallet_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Wallet",
        ),
    )


def resolve_economy_provider_lifecycle_runtime_context(
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder,
    index: MetaGraphRuntimeIndex,
) -> EconomyProviderLifecycleRuntimeContext:
    return EconomyProviderLifecycleRuntimeContext(
        lane_binder=lane_binder,
        index=index,
        lanes=build_economy_provider_lifecycle_lanes(index=index),
    )


async def record_provider_lifecycle_event(
    *,
    runtime_context: EconomyProviderLifecycleRuntimeContext,
    operation_context: EconomyProviderLifecycleOperationContext,
    provider_finance_entity_id: UUID,
    provider_key: str,
    provider_event_id: str,
    provider_lifecycle_object_id: str,
    provider_lifecycle_effect_key: str,
    wallet_finance_entity_id: UUID,
    wallet_id: UUID,
    wallet_public_id: UUID,
    coin_id: UUID,
    amount: Decimal | int | str,
    event_kind: ProviderLifecycleEventKind | str,
    provider_payment_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
    metadata_json: JsonObject | None = None,
    transaction_id: UUID,
    transaction_external_id: UUID,
    commit: bool = True,
    publish: bool = False,
) -> ProviderLifecycleRecordReceipt:
    provider_key_norm = _require_non_empty(
        provider_key, field_name="provider_key"
    ).casefold()
    provider_event_id_norm = _require_non_empty(
        provider_event_id,
        field_name="provider_event_id",
    )
    provider_lifecycle_object_id_norm = _require_non_empty(
        provider_lifecycle_object_id,
        field_name="provider_lifecycle_object_id",
    )
    event_kind_norm = _parse_event_kind(event_kind)
    provider_lifecycle_effect_key_norm = _require_non_empty(
        provider_lifecycle_effect_key,
        field_name="provider_lifecycle_effect_key",
    ).casefold()
    if provider_lifecycle_effect_key_norm != event_kind_norm.value:
        raise ValueError("provider lifecycle effect key must match event_kind")
    provider_payment_reference_norm = _require_non_empty(
        provider_payment_reference,
        field_name="provider_payment_reference",
    )
    provider_payload_hash_norm = _require_non_empty(
        provider_payload_hash,
        field_name="provider_payload_hash",
    ).casefold()
    if external_created_at.tzinfo is None or external_created_at.utcoffset() is None:
        raise ValueError("provider lifecycle requires timezone-aware provider time")
    idempotency_key_norm = (
        f"{provider_key_norm}:lifecycle:"
        f"{provider_lifecycle_object_id_norm}:{provider_lifecycle_effect_key_norm}"
    )
    amount_value = positive_amount(amount, field_name="provider lifecycle amount")
    receipt_id = stable_provider_lifecycle_receipt_id(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key_norm,
        provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
        provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
    )
    wallet_balance_id = stable_wallet_balance_id(
        wallet_id=wallet_id,
        coin_id=coin_id,
    )

    existing_receipt = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=receipt_id,
        projection_hash=runtime_context.lanes.provider_lifecycle_receipt_projection_hash,
        orm_class=ProviderLifecycleReceipt,
        object_id=receipt_id,
    )
    if existing_receipt is not None:
        _validate_existing_receipt(
            receipt=existing_receipt,
            provider_key=provider_key_norm,
            provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
            provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
            idempotency_key=idempotency_key_norm,
            provider_finance_entity_id=provider_finance_entity_id,
            wallet_finance_entity_id=wallet_finance_entity_id,
            wallet_id=wallet_id,
            wallet_public_id=wallet_public_id,
            coin_id=coin_id,
            amount=amount_value,
            event_kind=event_kind_norm,
            provider_payment_reference=provider_payment_reference_norm,
            transaction_id=transaction_id,
            transaction_external_id=transaction_external_id,
        )
        return _receipt_from_existing(
            receipt=existing_receipt,
            wallet_balance_id=wallet_balance_id,
        )

    wallet = await _hydrate_wallet(
        index=runtime_context.index,
        lanes=runtime_context.lanes,
        wallet_id=wallet_id,
        wallet_public_id=wallet_public_id,
    )
    (
        previous_balance,
        previous_held_balance,
        previous_available_balance,
    ) = _wallet_coin_balance_amounts(wallet=wallet, coin_id=coin_id)
    status = _status_for_event_kind(event_kind_norm)

    wallet_lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=wallet_id,
        projection=runtime_context.lanes.wallet_projection_hash,
    )
    with wallet_lane.activate(commit=commit, publish=publish):
        wallet_balance = await _apply_wallet_effect(
            wallet=wallet,
            coin_id=coin_id,
            amount=amount_value,
            event_kind=event_kind_norm,
            previous_available_balance=previous_available_balance,
            previous_held_balance=previous_held_balance,
        )
    (
        new_balance,
        new_held_balance,
        new_available_balance,
    ) = wallet_balance_amounts(wallet_balance)
    wallet_balance_id = wallet_balance.id

    receipt_lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=receipt_id,
        projection=runtime_context.lanes.provider_lifecycle_receipt_projection_hash,
    )
    with receipt_lane.activate(commit=commit, publish=publish):
        receipt = await ProviderLifecycleReceipt.record(
            provider_finance_entity_id=provider_finance_entity_id,
            provider_key=provider_key_norm,
            provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
            provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
            provider_event_id=provider_event_id_norm,
            wallet_finance_entity_id=wallet_finance_entity_id,
            wallet_id=wallet_id,
            wallet_public_id=wallet_public_id,
            coin_id=coin_id,
            amount=amount_value,
            event_kind=event_kind_norm,
            status=status,
            idempotency_key=idempotency_key_norm,
            previous_balance=previous_balance,
            new_balance=new_balance,
            previous_held_balance=previous_held_balance,
            new_held_balance=new_held_balance,
            previous_available_balance=previous_available_balance,
            new_available_balance=new_available_balance,
            provider_payment_reference=provider_payment_reference_norm,
            provider_payload_hash=provider_payload_hash_norm,
            external_created_at=external_created_at,
            metadata_json=metadata_json,
            transaction_id=transaction_id,
            transaction_external_id=transaction_external_id,
        )

    return ProviderLifecycleRecordReceipt(
        provider_lifecycle_receipt_id=receipt.id,
        wallet_balance_id=wallet_balance_id,
        provider_key=provider_key_norm,
        provider_event_id=provider_event_id_norm,
        provider_lifecycle_object_id=provider_lifecycle_object_id_norm,
        provider_lifecycle_effect_key=provider_lifecycle_effect_key_norm,
        idempotency_key=idempotency_key_norm,
        provider_finance_entity_id=provider_finance_entity_id,
        wallet_finance_entity_id=wallet_finance_entity_id,
        wallet_id=wallet_id,
        wallet_public_id=wallet_public_id,
        coin_id=coin_id,
        amount=amount_value,
        event_kind=event_kind_norm.value,
        status=status.value,
        previous_balance=previous_balance,
        new_balance=new_balance,
        previous_held_balance=previous_held_balance,
        new_held_balance=new_held_balance,
        previous_available_balance=previous_available_balance,
        new_available_balance=new_available_balance,
        provider_payment_reference=provider_payment_reference_norm,
        provider_payload_hash=provider_payload_hash_norm,
        transaction_id=transaction_id,
        transaction_external_id=transaction_external_id,
        idempotent_replay=False,
    )


def _status_for_event_kind(
    event_kind: ProviderLifecycleEventKind,
) -> ProviderLifecycleStatus:
    if event_kind is ProviderLifecycleEventKind.dispute:
        return ProviderLifecycleStatus.held
    if event_kind is ProviderLifecycleEventKind.dispute_release:
        return ProviderLifecycleStatus.released
    return ProviderLifecycleStatus.applied


async def _apply_wallet_effect(
    *,
    wallet: Wallet,
    coin_id: UUID,
    amount: Decimal,
    event_kind: ProviderLifecycleEventKind,
    previous_available_balance: Decimal,
    previous_held_balance: Decimal,
) -> WalletBalance:
    if event_kind is ProviderLifecycleEventKind.dispute:
        _require_available(
            operation="provider lifecycle dispute",
            available=previous_available_balance,
            amount=amount,
        )
        return await wallet.reserve_coin_hold(
            coin_id=coin_id,
            amount=amount,
        )
    if event_kind is ProviderLifecycleEventKind.dispute_release:
        if amount > previous_held_balance:
            raise ValueError(
                "provider lifecycle dispute_release insufficient held balance: "
                f"wallet_id={wallet.id} coin_id={coin_id} held={previous_held_balance} amount={amount}"
            )
        return await wallet.release_coin_hold(
            coin_id=coin_id,
            amount=amount,
        )
    if event_kind is ProviderLifecycleEventKind.chargeback:
        if amount > previous_held_balance:
            raise ValueError(
                "provider lifecycle chargeback insufficient held balance: "
                f"wallet_id={wallet.id} coin_id={coin_id} "
                f"held={previous_held_balance} amount={amount}"
            )
        return await wallet.settle_coin_hold(
            coin_id=coin_id,
            reserved_amount=amount,
            final_cost=amount,
        )

    if event_kind is ProviderLifecycleEventKind.refund:
        _require_available(
            operation="provider lifecycle refund",
            available=previous_available_balance,
            amount=amount,
        )
        return await wallet.apply_coin_delta(
            coin_id=coin_id,
            delta=-amount,
        )
    raise ValueError(f"unsupported provider lifecycle event kind: {event_kind.value}")


def _require_available(
    *,
    operation: str,
    available: Decimal,
    amount: Decimal,
) -> None:
    if amount > available:
        raise ValueError(
            f"{operation} insufficient wallet available balance: "
            f"available={available} amount={amount}"
        )


def _parse_event_kind(
    value: ProviderLifecycleEventKind | str,
) -> ProviderLifecycleEventKind:
    if isinstance(value, ProviderLifecycleEventKind):
        return value
    raw = str(value or "").strip().casefold()
    try:
        return ProviderLifecycleEventKind(raw)
    except ValueError as exc:
        raise ValueError(
            f"event_kind must be one of {[item.value for item in ProviderLifecycleEventKind]}"
        ) from exc


def _receipt_from_existing(
    *,
    receipt: ProviderLifecycleReceipt,
    wallet_balance_id: UUID,
) -> ProviderLifecycleRecordReceipt:
    return ProviderLifecycleRecordReceipt(
        provider_lifecycle_receipt_id=receipt.id,
        wallet_balance_id=wallet_balance_id,
        provider_key=receipt.provider_key,
        provider_event_id=receipt.provider_event_id,
        provider_lifecycle_object_id=receipt.provider_lifecycle_object_id,
        provider_lifecycle_effect_key=receipt.provider_lifecycle_effect_key,
        idempotency_key=receipt.idempotency_key,
        provider_finance_entity_id=receipt.provider_finance_entity_id,
        wallet_finance_entity_id=receipt.wallet_finance_entity_id,
        wallet_id=receipt.wallet_id,
        wallet_public_id=receipt.wallet_public_id,
        coin_id=receipt.coin_id,
        amount=non_negative_amount(
            receipt.amount, field_name="provider lifecycle amount"
        ),
        event_kind=receipt.event_kind.value,
        status=receipt.status.value,
        previous_balance=non_negative_amount(
            receipt.previous_balance,
            field_name="previous_balance",
        ),
        new_balance=non_negative_amount(
            receipt.new_balance,
            field_name="new_balance",
        ),
        previous_held_balance=non_negative_amount(
            receipt.previous_held_balance,
            field_name="previous_held_balance",
        ),
        new_held_balance=non_negative_amount(
            receipt.new_held_balance,
            field_name="new_held_balance",
        ),
        previous_available_balance=non_negative_amount(
            receipt.previous_available_balance,
            field_name="previous_available_balance",
        ),
        new_available_balance=non_negative_amount(
            receipt.new_available_balance,
            field_name="new_available_balance",
        ),
        provider_payment_reference=receipt.provider_payment_reference,
        provider_payload_hash=receipt.provider_payload_hash,
        transaction_id=receipt.transaction_id,
        transaction_external_id=receipt.transaction_external_id,
        idempotent_replay=True,
    )


def _validate_existing_receipt(
    *,
    receipt: ProviderLifecycleReceipt,
    provider_key: str,
    provider_lifecycle_object_id: str,
    provider_lifecycle_effect_key: str,
    idempotency_key: str,
    provider_finance_entity_id: UUID,
    wallet_finance_entity_id: UUID,
    wallet_id: UUID,
    wallet_public_id: UUID,
    coin_id: UUID,
    amount: Decimal,
    event_kind: ProviderLifecycleEventKind,
    provider_payment_reference: str,
    transaction_id: UUID,
    transaction_external_id: UUID,
) -> None:
    if receipt.provider_key != provider_key:
        raise ValueError("provider lifecycle existing provider_key mismatch")
    if receipt.provider_lifecycle_object_id != provider_lifecycle_object_id:
        raise ValueError(
            "provider lifecycle existing provider_lifecycle_object_id mismatch"
        )
    if receipt.provider_lifecycle_effect_key != provider_lifecycle_effect_key:
        raise ValueError(
            "provider lifecycle existing provider_lifecycle_effect_key mismatch"
        )
    if receipt.idempotency_key != idempotency_key:
        raise ValueError("provider lifecycle existing idempotency_key mismatch")
    if receipt.provider_finance_entity_id != provider_finance_entity_id:
        raise ValueError(
            "provider lifecycle existing provider_finance_entity_id mismatch"
        )
    if receipt.wallet_finance_entity_id != wallet_finance_entity_id:
        raise ValueError(
            "provider lifecycle existing wallet_finance_entity_id mismatch"
        )
    if receipt.wallet_id != wallet_id:
        raise ValueError("provider lifecycle existing wallet_id mismatch")
    if receipt.wallet_public_id != wallet_public_id:
        raise ValueError("provider lifecycle existing wallet_public_id mismatch")
    if receipt.coin_id != coin_id:
        raise ValueError("provider lifecycle existing coin_id mismatch")
    if not amount_equal(receipt.amount, amount):
        raise ValueError("provider lifecycle existing amount mismatch")
    if receipt.event_kind is not event_kind:
        raise ValueError("provider lifecycle existing event_kind mismatch")
    if receipt.provider_payment_reference != provider_payment_reference:
        raise ValueError(
            "provider lifecycle existing provider_payment_reference mismatch"
        )
    if receipt.transaction_id != transaction_id:
        raise ValueError("provider lifecycle existing transaction_id mismatch")
    if receipt.transaction_external_id != transaction_external_id:
        raise ValueError("provider lifecycle existing transaction_external_id mismatch")


async def _hydrate_wallet(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: EconomyProviderLifecycleLanes,
    wallet_id: UUID,
    wallet_public_id: UUID,
) -> Wallet:
    wallet = await _maybe_hydrate_committed_lane_object(
        index=index,
        branch_id=wallet_id,
        projection_hash=lanes.wallet_projection_hash,
        orm_class=Wallet,
        object_id=wallet_id,
    )
    if wallet is None:
        raise RuntimeError(f"provider lifecycle missing Wallet object_id={wallet_id}")
    if wallet.wallet_public_id != wallet_public_id:
        raise ValueError("provider lifecycle wallet_public_id mismatch")
    return wallet


def _wallet_coin_balance_amounts(
    *,
    wallet: Wallet,
    coin_id: UUID,
) -> tuple[Decimal, Decimal, Decimal]:
    wallet_balance = _find_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        return ZERO_AMOUNT, ZERO_AMOUNT, ZERO_AMOUNT
    return wallet_balance_amounts(wallet_balance)


def _find_wallet_balance(*, wallet: Wallet, coin_id: UUID) -> WalletBalance | None:
    matches = [
        wallet_balance
        for wallet_balance in wallet.wallet_balances
        if wallet_balance.wallet_id == wallet.id and wallet_balance.coin_id == coin_id
    ]
    if len(matches) > 1:
        raise ValueError(
            "provider lifecycle wallet balance context is ambiguous: "
            f"wallet_id={wallet.id} coin_id={coin_id}"
        )
    return matches[0] if matches else None


def _bind_lane(
    *,
    runtime_context: EconomyProviderLifecycleRuntimeContext,
    operation_context: EconomyProviderLifecycleOperationContext,
    branch_id: UUID,
    projection: str,
) -> EconomyMetaRuntimeLane:
    return runtime_context.lane_binder.bind(
        branch_id=branch_id,
        projection=projection,
        actor_id=operation_context.actor_id,
    )


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
            "Economy provider lifecycle could not resolve projection hash "
            f"for committed lane hydration: {projection_hash!r}"
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


def _require_non_empty(value: str, *, field_name: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    return raw


__all__ = [
    "EconomyProviderLifecycleLanes",
    "EconomyProviderLifecycleOperationContext",
    "EconomyProviderLifecycleRuntimeContext",
    "ProviderLifecycleRecordReceipt",
    "build_economy_provider_lifecycle_lanes",
    "record_provider_lifecycle_event",
    "resolve_economy_provider_lifecycle_runtime_context",
]
