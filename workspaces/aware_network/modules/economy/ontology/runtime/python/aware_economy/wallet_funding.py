from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import TypeVar
from uuid import UUID

from aware_economy.capital_amount import (
    ZERO_AMOUNT,
    amount_equal,
    non_negative_amount,
    positive_amount,
)
from aware_economy.ontology.materialization import wallet_balance_amounts
from aware_economy.meta_runtime import (
    EconomyMetaRuntimeLane,
    EconomyMetaRuntimeLaneBinder,
)
from aware_economy_ontology.stable_ids import (
    stable_transaction_external_id,
    stable_transaction_id,
    stable_transaction_intent_external_expiration_id,
    stable_transaction_intent_id,
    stable_wallet_balance_id,
)
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
)
from aware_economy_ontology.transaction.transaction import Transaction
from aware_economy_ontology.transaction.transaction_enums import TransactionKind
from aware_economy_ontology.transaction.transaction_external import TransactionExternal
from aware_economy_ontology.transaction.transaction_intent import TransactionIntent
from aware_economy_ontology.transaction.transaction_intent_external_expiration import (
    TransactionIntentExternalExpiration,
)
from aware_economy_ontology.transaction.transaction_intent_enums import (
    TransactionIntentStatus,
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
class EconomyWalletFundingLanes:
    transaction_intent_projection_hash: str
    transaction_projection_hash: str
    transaction_external_projection_hash: str
    wallet_projection_hash: str


@dataclass(frozen=True, slots=True)
class EconomyWalletFundingRuntimeContext:
    lane_binder: EconomyMetaRuntimeLaneBinder
    index: MetaGraphRuntimeIndex
    lanes: EconomyWalletFundingLanes


@dataclass(frozen=True, slots=True)
class EconomyWalletFundingOperationContext:
    actor_id: UUID | None


@dataclass(frozen=True, slots=True)
class WalletFundingPrepareReceipt:
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    funding_intent_key: str
    idempotency_key: str
    provider_key: str
    provider_config_id: UUID
    provider_route_id: UUID
    provider_finance_entity_id: UUID
    recipient_finance_entity_id: UUID
    recipient_wallet_id: UUID
    recipient_wallet_public_id: UUID
    coin_id: UUID
    amount: Decimal
    capital_conversion_quote_id: UUID
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    conversion_mode: str
    quote_captured_at: datetime
    quote_expires_at: datetime | None
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class WalletFundingRecordReceipt:
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    capital_conversion_quote_id: UUID
    quote_hash: str
    transaction_external_id: UUID
    transaction_id: UUID
    transaction_nonce: int
    wallet_external_ingress_application_id: UUID
    wallet_balance_id: UUID
    provider_finance_entity_id: UUID
    recipient_finance_entity_id: UUID
    recipient_wallet_id: UUID
    recipient_wallet_public_id: UUID
    coin_id: UUID
    amount: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class WalletFundingCancelReceipt:
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    transaction_intent_external_expiration_id: UUID
    provider_config_id: UUID
    capital_conversion_quote_id: UUID
    quote_hash: str
    provider_key: str
    provider_event_id: str
    provider_public_reference: str
    status: str
    idempotent_replay: bool


@dataclass(frozen=True, slots=True)
class WalletBalanceDescribeReceipt:
    wallet_balance_id: UUID
    wallet_id: UUID
    coin_id: UUID
    balance: Decimal
    held_balance: Decimal
    available_balance: Decimal
    ready: bool
    last_transaction_id: UUID | None


def build_economy_wallet_funding_lanes(
    *,
    index: MetaGraphRuntimeIndex,
) -> EconomyWalletFundingLanes:
    return EconomyWalletFundingLanes(
        transaction_intent_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="TransactionIntent",
        ),
        transaction_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Transaction",
        ),
        transaction_external_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="TransactionExternal",
        ),
        wallet_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Wallet",
        ),
    )


def resolve_economy_wallet_funding_runtime_context(
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder,
    index: MetaGraphRuntimeIndex,
) -> EconomyWalletFundingRuntimeContext:
    return EconomyWalletFundingRuntimeContext(
        lane_binder=lane_binder,
        index=index,
        lanes=build_economy_wallet_funding_lanes(index=index),
    )


async def prepare_wallet_funding(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    operation_context: EconomyWalletFundingOperationContext,
    provider_config_id: UUID,
    provider_route_id: UUID,
    provider_finance_entity_id: UUID,
    recipient_finance_entity_id: UUID,
    recipient_wallet_id: UUID,
    recipient_wallet_public_id: UUID,
    coin_id: UUID,
    amount: Decimal,
    funding_intent_key: str,
    idempotency_key: str,
    provider_key: str,
    external_currency: str,
    external_minor_unit_exponent: int,
    conversion_mode: ExternalCapitalConversionMode,
    created_at: datetime,
    commit: bool,
    publish: bool,
) -> WalletFundingPrepareReceipt:
    if not commit:
        raise ValueError("wallet funding prepare requires a durable commit")
    funding_intent_key_norm = _require_non_empty(
        funding_intent_key,
        field_name="funding_intent_key",
    ).casefold()
    idempotency_key_norm = _require_non_empty(
        idempotency_key,
        field_name="idempotency_key",
    )
    provider_key_norm = _require_non_empty(
        provider_key,
        field_name="provider_key",
    ).casefold()
    amount = positive_amount(amount, field_name="wallet funding amount")
    await _hydrate_recipient_wallet(
        index=runtime_context.index,
        lanes=runtime_context.lanes,
        wallet_id=recipient_wallet_id,
        wallet_public_id=recipient_wallet_public_id,
        error_context="wallet funding prepare recipient wallet hydration",
    )
    intent_id = stable_transaction_intent_id(
        provider_config_id=provider_config_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        funding_intent_key=funding_intent_key_norm,
    )
    existing = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntent,
        object_id=intent_id,
    )
    if existing is not None:
        _validate_prepared_intent(
            existing,
            provider_config_id=provider_config_id,
            provider_route_id=provider_route_id,
            recipient_finance_entity_id=recipient_finance_entity_id,
            recipient_wallet_id=recipient_wallet_id,
            recipient_wallet_public_id=recipient_wallet_public_id,
            funding_intent_key=funding_intent_key_norm,
            idempotency_key=idempotency_key_norm,
            provider_key=provider_key_norm,
            coin_id=coin_id,
            amount=amount,
            external_currency=external_currency,
            conversion_mode=conversion_mode,
        )
        return await _wallet_funding_prepare_receipt(
            runtime_context=runtime_context,
            intent=existing,
            provider_finance_entity_id=provider_finance_entity_id,
            idempotent_replay=True,
        )

    lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=intent_id,
        projection=runtime_context.lanes.transaction_intent_projection_hash,
    )
    with lane.activate(commit=commit, publish=publish):
        intent = await TransactionIntent.create(
            provider_config_id=provider_config_id,
            recipient_finance_entity_id=recipient_finance_entity_id,
            recipient_wallet_id=recipient_wallet_id,
            recipient_wallet_public_id=recipient_wallet_public_id,
            funding_intent_key=funding_intent_key_norm,
            coin_id=coin_id,
            amount=amount,
            provider_key=provider_key_norm,
            idempotency_key=idempotency_key_norm,
            provider_route_id=provider_route_id,
            external_currency=external_currency,
            external_minor_unit_exponent=external_minor_unit_exponent,
            conversion_mode=conversion_mode,
            created_at=created_at,
            quote_expires_at=None,
            metadata_json=None,
        )

    intent = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntent,
        object_id=intent_id,
        error_context="wallet funding prepared intent hydration",
    )
    return await _wallet_funding_prepare_receipt(
        runtime_context=runtime_context,
        intent=intent,
        provider_finance_entity_id=provider_finance_entity_id,
        idempotent_replay=False,
    )


async def hydrate_wallet_funding_intent_at_commit(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    transaction_intent_id: UUID,
    transaction_intent_commit_id: UUID,
) -> TransactionIntent:
    commit = await FSCommitStore().get_commit(
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        commit_id=transaction_intent_commit_id,
    )
    if commit is None:
        raise ValueError(
            "wallet funding context commit does not belong to the TransactionIntent lane"
        )
    intent = await _hydrate_lane_object_at_commit(
        index=runtime_context.index,
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        commit_id=transaction_intent_commit_id,
        object_instance_graph_id=commit.object_instance_graph_id,
        orm_class=TransactionIntent,
        object_id=transaction_intent_id,
        error_context="wallet funding context intent hydration",
    )
    if intent is None:
        raise RuntimeError("wallet funding context intent hydration returned no object")
    return intent


async def _wallet_funding_prepare_receipt(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    intent: TransactionIntent,
    provider_finance_entity_id: UUID,
    idempotent_replay: bool,
) -> WalletFundingPrepareReceipt:
    quote = intent.capital_conversion_quote
    if quote is None:
        raise ValueError(
            "wallet funding intent is missing its capital conversion quote"
        )
    head = await FSCommitStore().head(
        branch_id=intent.id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
    )
    if head is None or not head.get("commit_id"):
        raise ValueError("wallet funding intent durable commit is missing")
    return WalletFundingPrepareReceipt(
        transaction_intent_id=intent.id,
        transaction_intent_commit_id=UUID(str(head["commit_id"])),
        funding_intent_key=intent.funding_intent_key,
        idempotency_key=intent.idempotency_key,
        provider_key=intent.provider_key,
        provider_config_id=intent.provider_config_id,
        provider_route_id=quote.provider_route_id,
        provider_finance_entity_id=provider_finance_entity_id,
        recipient_finance_entity_id=intent.recipient_finance_entity_id,
        recipient_wallet_id=intent.recipient_wallet_id,
        recipient_wallet_public_id=intent.recipient_wallet_public_id,
        coin_id=intent.coin_id,
        amount=positive_amount(intent.amount, field_name="wallet funding amount"),
        capital_conversion_quote_id=quote.id,
        quote_hash=quote.quote_hash,
        external_amount_minor=quote.external_amount_minor,
        external_currency=quote.external_currency,
        conversion_mode=quote.conversion_mode.value,
        quote_captured_at=quote.captured_at,
        quote_expires_at=quote.expires_at,
        status=intent.status.value,
        idempotent_replay=idempotent_replay,
    )


async def record_verified_wallet_funding(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    operation_context: EconomyWalletFundingOperationContext,
    transaction_intent_id: UUID,
    transaction_intent_commit_id: UUID,
    provider_config_id: UUID,
    provider_finance_entity_id: UUID,
    provider_key: str,
    provider_event_id: str,
    idempotency_key: str,
    capital_conversion_quote_id: UUID,
    quote_hash: str,
    external_amount_minor: int,
    external_currency: str,
    provider_public_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
    commit: bool,
    publish: bool,
) -> WalletFundingRecordReceipt:
    if not commit:
        raise ValueError("verified wallet funding requires durable commits")
    provider_key_norm = _require_non_empty(
        provider_key,
        field_name="provider_key",
    ).casefold()
    provider_event_id_norm = _require_non_empty(
        provider_event_id,
        field_name="provider_event_id",
    )
    idempotency_key_norm = _require_non_empty(
        idempotency_key,
        field_name="idempotency_key",
    )
    provider_public_reference = _require_non_empty(
        provider_public_reference,
        field_name="provider_public_reference",
    )
    provider_payload_hash = _require_non_empty(
        provider_payload_hash,
        field_name="provider_payload_hash",
    ).lower()
    quote_hash = _require_non_empty(
        quote_hash,
        field_name="quote_hash",
    ).lower()
    external_currency = _require_non_empty(
        external_currency,
        field_name="external_currency",
    ).upper()
    if external_created_at.tzinfo is None or external_created_at.utcoffset() is None:
        raise ValueError(
            "verified wallet funding requires timezone-aware provider time"
        )

    prepared_intent = await hydrate_wallet_funding_intent_at_commit(
        runtime_context=runtime_context,
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
    )
    quote = prepared_intent.capital_conversion_quote
    if quote is None:
        raise ValueError("verified wallet funding intent quote is missing")
    _validate_verified_funding_evidence(
        intent=prepared_intent,
        provider_config_id=provider_config_id,
        provider_key=provider_key_norm,
        capital_conversion_quote_id=capital_conversion_quote_id,
        quote_hash=quote_hash,
        external_amount_minor=external_amount_minor,
        external_currency=external_currency,
        external_created_at=external_created_at,
    )
    amount = positive_amount(
        prepared_intent.amount,
        field_name="wallet funding amount",
    )
    recipient_finance_entity_id = prepared_intent.recipient_finance_entity_id
    recipient_wallet_id = prepared_intent.recipient_wallet_id
    recipient_wallet_public_id = prepared_intent.recipient_wallet_public_id
    coin_id = prepared_intent.coin_id

    transaction_nonce = _stable_transaction_nonce(
        transaction_intent_id=transaction_intent_id,
        provider_event_id=provider_event_id_norm,
    )
    transaction_id = stable_transaction_id(
        capital_origin_id=capital_conversion_quote_id,
        target_wallet_public_id=recipient_wallet_public_id,
        coin_id=coin_id,
        nonce=transaction_nonce,
    )
    transaction = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=transaction_id,
        projection_hash=runtime_context.lanes.transaction_projection_hash,
        orm_class=Transaction,
        object_id=transaction_id,
    )
    transaction_existed = transaction is not None
    if transaction is None:
        transaction_lane = _bind_lane(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=transaction_id,
            projection=runtime_context.lanes.transaction_projection_hash,
        )
        with transaction_lane.activate(commit=True, publish=publish):
            transaction = await Transaction.create_external_ingress(
                capital_origin_id=capital_conversion_quote_id,
                target_wallet_public_id=recipient_wallet_public_id,
                coin_id=coin_id,
                coin_amount=amount,
                nonce=transaction_nonce,
                description=f"Wallet funding intent {transaction_intent_id}",
                idempotency_key=idempotency_key_norm,
            )
    else:
        _validate_external_ingress_transaction(
            transaction=transaction,
            capital_conversion_quote_id=capital_conversion_quote_id,
            recipient_wallet_public_id=recipient_wallet_public_id,
            coin_id=coin_id,
            amount=amount,
            transaction_nonce=transaction_nonce,
            idempotency_key=idempotency_key_norm,
        )

    external_id = stable_transaction_external_id(
        provider_config_id=provider_config_id,
        provider_event_id=provider_event_id_norm,
    )
    existing_external = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=external_id,
        projection_hash=runtime_context.lanes.transaction_external_projection_hash,
        orm_class=TransactionExternal,
        object_id=external_id,
    )
    external_existed = existing_external is not None
    if existing_external is None:
        external_lane = _bind_lane(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=external_id,
            projection=runtime_context.lanes.transaction_external_projection_hash,
        )
        with external_lane.activate(commit=True, publish=publish):
            external = await TransactionExternal.record(
                transaction_id=transaction.id,
                transaction_intent_id=transaction_intent_id,
                provider_config_id=provider_config_id,
                capital_conversion_quote_id=capital_conversion_quote_id,
                provider_finance_entity_id=provider_finance_entity_id,
                provider_key=provider_key_norm,
                provider_event_id=provider_event_id_norm,
                idempotency_key=idempotency_key_norm,
                quote_hash=quote_hash,
                external_amount_minor=external_amount_minor,
                external_currency=external_currency,
                provider_public_reference=provider_public_reference,
                provider_payload_hash=provider_payload_hash,
                external_created_at=external_created_at,
            )
    else:
        _validate_existing_external_evidence(
            external=existing_external,
            transaction_id=transaction_id,
            transaction_intent_id=transaction_intent_id,
            provider_config_id=provider_config_id,
            provider_finance_entity_id=provider_finance_entity_id,
            provider_key=provider_key_norm,
            provider_event_id=provider_event_id_norm,
            idempotency_key=idempotency_key_norm,
            capital_conversion_quote_id=capital_conversion_quote_id,
            quote_hash=quote_hash,
            external_amount_minor=external_amount_minor,
            external_currency=external_currency,
            provider_public_reference=provider_public_reference,
            provider_payload_hash=provider_payload_hash,
            external_created_at=external_created_at,
        )
        external = existing_external

    wallet = await _hydrate_recipient_wallet(
        index=runtime_context.index,
        lanes=runtime_context.lanes,
        wallet_id=recipient_wallet_id,
        wallet_public_id=recipient_wallet_public_id,
        error_context="wallet funding record recipient wallet hydration",
    )
    application_existed = any(
        application.transaction_id == transaction_id
        for application in wallet.external_ingress_applications
    )
    wallet_lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=recipient_wallet_id,
        projection=runtime_context.lanes.wallet_projection_hash,
    )
    with wallet_lane.activate(commit=True, publish=publish):
        application = await wallet.apply_external_ingress(
            transaction_id=transaction_id,
            coin_id=coin_id,
            amount=amount,
        )

    current_intent = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntent,
        object_id=transaction_intent_id,
        error_context="wallet funding confirmation intent hydration",
    )
    intent_was_confirmed = current_intent.status == TransactionIntentStatus.confirmed
    intent_lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=transaction_intent_id,
        projection=runtime_context.lanes.transaction_intent_projection_hash,
    )
    with intent_lane.activate(commit=True, publish=publish):
        confirmed_intent = await current_intent.confirm(
            occurred_at=external_created_at,
        )

    return WalletFundingRecordReceipt(
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
        capital_conversion_quote_id=capital_conversion_quote_id,
        quote_hash=quote_hash,
        transaction_external_id=external.id,
        transaction_id=transaction.id,
        transaction_nonce=transaction_nonce,
        wallet_external_ingress_application_id=application.id,
        wallet_balance_id=stable_wallet_balance_id(
            wallet_id=recipient_wallet_id,
            coin_id=coin_id,
        ),
        provider_finance_entity_id=provider_finance_entity_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        recipient_wallet_id=recipient_wallet_id,
        recipient_wallet_public_id=recipient_wallet_public_id,
        coin_id=coin_id,
        amount=amount,
        previous_balance=non_negative_amount(
            application.previous_balance,
            field_name="wallet funding previous balance",
        ),
        new_balance=non_negative_amount(
            application.new_balance,
            field_name="wallet funding new balance",
        ),
        status=confirmed_intent.status.value,
        idempotent_replay=(
            transaction_existed
            and external_existed
            and application_existed
            and intent_was_confirmed
        ),
    )


async def record_wallet_funding_expiration(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    operation_context: EconomyWalletFundingOperationContext,
    transaction_intent_id: UUID,
    transaction_intent_commit_id: UUID,
    provider_config_id: UUID,
    provider_key: str,
    provider_event_id: str,
    idempotency_key: str,
    capital_conversion_quote_id: UUID,
    quote_hash: str,
    provider_public_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
    commit: bool,
    publish: bool,
) -> WalletFundingCancelReceipt:
    if not commit:
        raise ValueError("wallet funding expiration requires a durable commit")
    provider_key = _require_non_empty(
        provider_key,
        field_name="provider_key",
    ).casefold()
    provider_event_id = _require_non_empty(
        provider_event_id,
        field_name="provider_event_id",
    )
    idempotency_key = _require_non_empty(
        idempotency_key,
        field_name="idempotency_key",
    )
    provider_public_reference = _require_non_empty(
        provider_public_reference,
        field_name="provider_public_reference",
    )
    provider_payload_hash = _require_non_empty(
        provider_payload_hash,
        field_name="provider_payload_hash",
    ).casefold()
    quote_hash = _require_non_empty(
        quote_hash,
        field_name="quote_hash",
    ).casefold()
    if external_created_at.tzinfo is None or external_created_at.utcoffset() is None:
        raise ValueError(
            "wallet funding expiration requires timezone-aware provider time"
        )

    prepared_intent = await hydrate_wallet_funding_intent_at_commit(
        runtime_context=runtime_context,
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
    )
    prepared_quote = prepared_intent.capital_conversion_quote
    if prepared_quote is None:
        raise ValueError("wallet funding expiration intent quote is missing")
    expected_context = (
        provider_config_id,
        provider_key,
        capital_conversion_quote_id,
        quote_hash,
    )
    actual_context = (
        prepared_intent.provider_config_id,
        prepared_intent.provider_key,
        prepared_quote.id,
        prepared_quote.quote_hash,
    )
    if actual_context != expected_context:
        raise ValueError("wallet funding expiration committed context mismatch")
    if external_created_at < prepared_intent.created_at:
        raise ValueError("wallet funding expiration cannot predate the intent")

    current_intent = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntent,
        object_id=transaction_intent_id,
        error_context="wallet funding expiration intent hydration",
    )
    expiration_id = stable_transaction_intent_external_expiration_id(
        provider_config_id=provider_config_id,
        provider_event_id=provider_event_id,
    )
    existing_expiration = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntentExternalExpiration,
        object_id=expiration_id,
    )
    if existing_expiration is not None:
        expected_evidence = (
            transaction_intent_id,
            provider_config_id,
            capital_conversion_quote_id,
            provider_key,
            provider_event_id,
            idempotency_key,
            quote_hash,
            provider_public_reference,
            provider_payload_hash,
            external_created_at,
        )
        actual_evidence = (
            existing_expiration.transaction_intent_id,
            existing_expiration.provider_config_id,
            existing_expiration.capital_conversion_quote_id,
            existing_expiration.provider_key,
            existing_expiration.provider_event_id,
            existing_expiration.idempotency_key,
            existing_expiration.quote_hash,
            existing_expiration.provider_public_reference,
            existing_expiration.provider_payload_hash,
            existing_expiration.external_created_at,
        )
        if actual_evidence != expected_evidence:
            raise ValueError("wallet funding expiration replay evidence mismatch")
        if current_intent.status != TransactionIntentStatus.canceled:
            raise RuntimeError(
                "wallet funding expiration evidence exists without canceled intent"
            )
        return WalletFundingCancelReceipt(
            transaction_intent_id=transaction_intent_id,
            transaction_intent_commit_id=transaction_intent_commit_id,
            transaction_intent_external_expiration_id=existing_expiration.id,
            provider_config_id=provider_config_id,
            capital_conversion_quote_id=capital_conversion_quote_id,
            quote_hash=quote_hash,
            provider_key=provider_key,
            provider_event_id=provider_event_id,
            provider_public_reference=provider_public_reference,
            status=current_intent.status.value,
            idempotent_replay=True,
        )
    if current_intent.status == TransactionIntentStatus.canceled:
        raise RuntimeError(
            "wallet funding intent is canceled without matching external expiration evidence"
        )

    intent_lane = _bind_lane(
        runtime_context=runtime_context,
        operation_context=operation_context,
        branch_id=transaction_intent_id,
        projection=runtime_context.lanes.transaction_intent_projection_hash,
    )
    with intent_lane.activate(commit=True, publish=publish):
        expiration = await current_intent.cancel_from_external_evidence(
            provider_config_id=provider_config_id,
            capital_conversion_quote_id=capital_conversion_quote_id,
            provider_key=provider_key,
            provider_event_id=provider_event_id,
            idempotency_key=idempotency_key,
            quote_hash=quote_hash,
            provider_public_reference=provider_public_reference,
            provider_payload_hash=provider_payload_hash,
            external_created_at=external_created_at,
        )

    canceled_intent = await _hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=transaction_intent_id,
        projection_hash=runtime_context.lanes.transaction_intent_projection_hash,
        orm_class=TransactionIntent,
        object_id=transaction_intent_id,
        error_context="wallet funding canceled intent hydration",
    )
    if canceled_intent.status != TransactionIntentStatus.canceled:
        raise RuntimeError(
            "wallet funding expiration evidence committed without canceled intent"
        )

    return WalletFundingCancelReceipt(
        transaction_intent_id=transaction_intent_id,
        transaction_intent_commit_id=transaction_intent_commit_id,
        transaction_intent_external_expiration_id=expiration.id,
        provider_config_id=provider_config_id,
        capital_conversion_quote_id=capital_conversion_quote_id,
        quote_hash=quote_hash,
        provider_key=provider_key,
        provider_event_id=provider_event_id,
        provider_public_reference=provider_public_reference,
        status=canceled_intent.status.value,
        idempotent_replay=False,
    )


async def describe_wallet_balance(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    wallet_id: UUID,
    coin_id: UUID,
) -> WalletBalanceDescribeReceipt:
    wallet_balance_id = stable_wallet_balance_id(wallet_id=wallet_id, coin_id=coin_id)
    wallet = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=wallet_id,
        projection_hash=runtime_context.lanes.wallet_projection_hash,
        orm_class=Wallet,
        object_id=wallet_id,
    )
    if wallet is None:
        return WalletBalanceDescribeReceipt(
            wallet_balance_id=wallet_balance_id,
            wallet_id=wallet_id,
            coin_id=coin_id,
            balance=ZERO_AMOUNT,
            held_balance=ZERO_AMOUNT,
            available_balance=ZERO_AMOUNT,
            ready=False,
            last_transaction_id=None,
        )
    wallet_balance = _find_wallet_balance(wallet=wallet, coin_id=coin_id)
    if wallet_balance is None:
        return WalletBalanceDescribeReceipt(
            wallet_balance_id=wallet_balance_id,
            wallet_id=wallet_id,
            coin_id=coin_id,
            balance=ZERO_AMOUNT,
            held_balance=ZERO_AMOUNT,
            available_balance=ZERO_AMOUNT,
            ready=False,
            last_transaction_id=None,
        )
    balance, held_balance, available_balance = wallet_balance_amounts(wallet_balance)
    return WalletBalanceDescribeReceipt(
        wallet_balance_id=wallet_balance.id,
        wallet_id=wallet_id,
        coin_id=coin_id,
        balance=balance,
        held_balance=held_balance,
        available_balance=available_balance,
        ready=True,
        last_transaction_id=_last_transaction_id(wallet=wallet, coin_id=coin_id),
    )


async def _hydrate_recipient_wallet(
    *,
    index: MetaGraphRuntimeIndex,
    lanes: EconomyWalletFundingLanes,
    wallet_id: UUID,
    wallet_public_id: UUID,
    error_context: str,
) -> Wallet:
    wallet = await _maybe_hydrate_committed_lane_object(
        index=index,
        branch_id=wallet_id,
        projection_hash=lanes.wallet_projection_hash,
        orm_class=Wallet,
        object_id=wallet_id,
    )
    if wallet is None:
        raise RuntimeError(f"{error_context}: missing Wallet object_id={wallet_id}")
    if wallet.wallet_public_id != wallet_public_id:
        raise ValueError("wallet funding wallet_public_id mismatch")
    return wallet


def _bind_lane(
    *,
    runtime_context: EconomyWalletFundingRuntimeContext,
    operation_context: EconomyWalletFundingOperationContext,
    branch_id: UUID,
    projection: str,
) -> EconomyMetaRuntimeLane:
    return runtime_context.lane_binder.bind(
        branch_id=branch_id,
        projection=projection,
        actor_id=operation_context.actor_id,
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

    return await _hydrate_lane_object_at_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=UUID(str(target_head["commit_id"])),
        object_instance_graph_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        orm_class=orm_class,
        object_id=object_id,
        error_context=f"committed {orm_class.__name__} hydration",
        missing_ok=True,
    )


async def _hydrate_lane_object_at_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    object_instance_graph_id: UUID | None,
    orm_class: type[_TModel],
    object_id: UUID,
    error_context: str,
    missing_ok: bool = False,
) -> _TModel | None:

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Economy wallet funding could not resolve projection hash for committed lane hydration: "
            + repr(projection_hash)
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        oig_id=object_instance_graph_id,
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
        if missing_ok:
            return None
        raise RuntimeError(
            f"{error_context}: missing {orm_class.__name__} object_id={object_id}"
        )
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


def _validate_verified_funding_evidence(
    intent: TransactionIntent,
    *,
    provider_config_id: UUID,
    provider_key: str,
    capital_conversion_quote_id: UUID,
    quote_hash: str,
    external_amount_minor: int,
    external_currency: str,
    external_created_at: datetime,
) -> None:
    quote = intent.capital_conversion_quote
    if quote is None:
        raise ValueError("verified wallet funding quote is missing")
    if intent.provider_config_id != provider_config_id:
        raise ValueError("verified wallet funding provider configuration mismatch")
    if intent.provider_key != provider_key:
        raise ValueError("verified wallet funding provider key mismatch")
    if intent.capital_conversion_quote_id != capital_conversion_quote_id:
        raise ValueError("verified wallet funding quote identity mismatch")
    if quote.id != capital_conversion_quote_id:
        raise ValueError("verified wallet funding contained quote mismatch")
    if len(quote_hash) != 64:
        raise ValueError("verified wallet funding quote hash must be 64 hex characters")
    try:
        int(quote_hash, 16)
    except ValueError as exc:
        raise ValueError(
            "verified wallet funding quote hash must be 64 hex characters"
        ) from exc
    if quote.quote_hash != quote_hash:
        raise ValueError("verified wallet funding quote hash mismatch")
    if external_amount_minor <= 0:
        raise ValueError("verified wallet funding external amount must be positive")
    if quote.external_amount_minor != external_amount_minor:
        raise ValueError("verified wallet funding external amount mismatch")
    if quote.external_currency != external_currency:
        raise ValueError("verified wallet funding external currency mismatch")
    if external_created_at < quote.captured_at:
        raise ValueError("verified wallet funding evidence predates the capital quote")
    if quote.expires_at is not None and external_created_at > quote.expires_at:
        raise ValueError("verified wallet funding evidence arrived after quote expiry")
    if intent.status == TransactionIntentStatus.canceled:
        raise ValueError("verified wallet funding intent is canceled")


def _validate_external_ingress_transaction(
    *,
    transaction: Transaction,
    capital_conversion_quote_id: UUID,
    recipient_wallet_public_id: UUID,
    coin_id: UUID,
    amount: Decimal,
    transaction_nonce: int,
    idempotency_key: str,
) -> None:
    if transaction.source_wallet_public_id is not None:
        raise ValueError(
            "external ingress transaction source WalletPublic must be absent"
        )
    if transaction.capital_origin_id != capital_conversion_quote_id:
        raise ValueError("external ingress transaction capital origin mismatch")
    if transaction.target_wallet_public_id != recipient_wallet_public_id:
        raise ValueError("external ingress transaction target WalletPublic mismatch")
    if transaction.coin_id != coin_id:
        raise ValueError("external ingress transaction Coin mismatch")
    if transaction.nonce != transaction_nonce:
        raise ValueError("external ingress transaction nonce mismatch")
    if transaction.kind != TransactionKind.external_ingress:
        raise ValueError("external ingress transaction kind mismatch")
    if transaction.idempotency_key != idempotency_key:
        raise ValueError("external ingress transaction idempotency key mismatch")
    if not amount_equal(transaction.coin_amount, amount):
        raise ValueError("external ingress transaction amount mismatch")


def _validate_existing_external_evidence(
    *,
    external: TransactionExternal,
    transaction_id: UUID,
    transaction_intent_id: UUID,
    provider_config_id: UUID,
    provider_finance_entity_id: UUID,
    provider_key: str,
    provider_event_id: str,
    idempotency_key: str,
    capital_conversion_quote_id: UUID,
    quote_hash: str,
    external_amount_minor: int,
    external_currency: str,
    provider_public_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
) -> None:
    expected = (
        transaction_id,
        transaction_intent_id,
        provider_config_id,
        provider_finance_entity_id,
        provider_key,
        provider_event_id,
        idempotency_key,
        capital_conversion_quote_id,
        quote_hash,
        external_amount_minor,
        external_currency,
        provider_public_reference,
        provider_payload_hash,
        external_created_at,
    )
    actual = (
        external.transaction_id,
        external.transaction_intent_id,
        external.provider_config_id,
        external.provider_finance_entity_id,
        external.provider_key,
        external.provider_event_id,
        external.idempotency_key,
        external.capital_conversion_quote_id,
        external.quote_hash,
        external.external_amount_minor,
        external.external_currency,
        external.provider_public_reference,
        external.provider_payload_hash,
        external.external_created_at,
    )
    if actual != expected:
        raise ValueError("existing external funding evidence mismatch")


def _validate_prepared_intent(
    intent: TransactionIntent,
    *,
    provider_config_id: UUID,
    provider_route_id: UUID,
    recipient_finance_entity_id: UUID,
    recipient_wallet_id: UUID,
    recipient_wallet_public_id: UUID,
    funding_intent_key: str,
    idempotency_key: str,
    provider_key: str,
    coin_id: UUID,
    amount: Decimal,
    external_currency: str,
    conversion_mode: ExternalCapitalConversionMode,
) -> None:
    quote = intent.capital_conversion_quote
    if quote is None:
        raise ValueError("wallet funding existing intent quote is missing")
    expected = {
        "provider_config_id": provider_config_id,
        "provider_route_id": provider_route_id,
        "recipient_finance_entity_id": recipient_finance_entity_id,
        "recipient_wallet_id": recipient_wallet_id,
        "recipient_wallet_public_id": recipient_wallet_public_id,
        "funding_intent_key": funding_intent_key,
        "idempotency_key": idempotency_key,
        "provider_key": provider_key,
        "coin_id": coin_id,
        "external_currency": external_currency.strip().upper(),
        "conversion_mode": conversion_mode,
    }
    actual = {
        "provider_config_id": intent.provider_config_id,
        "provider_route_id": quote.provider_route_id,
        "recipient_finance_entity_id": intent.recipient_finance_entity_id,
        "recipient_wallet_id": intent.recipient_wallet_id,
        "recipient_wallet_public_id": intent.recipient_wallet_public_id,
        "funding_intent_key": intent.funding_intent_key,
        "idempotency_key": intent.idempotency_key,
        "provider_key": intent.provider_key,
        "coin_id": intent.coin_id,
        "external_currency": quote.external_currency,
        "conversion_mode": quote.conversion_mode,
    }
    if actual != expected:
        raise ValueError("wallet funding existing intent committed context mismatch")
    if not amount_equal(intent.amount, amount) or not amount_equal(
        quote.target_amount,
        amount,
    ):
        raise ValueError("wallet funding existing intent amount mismatch")


def _stable_transaction_nonce(
    *,
    transaction_intent_id: UUID,
    provider_event_id: str,
) -> int:
    digest = sha256(f"{transaction_intent_id}:{provider_event_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % 2_147_483_647 + 1


def _find_wallet_balance(*, wallet: Wallet, coin_id: UUID) -> WalletBalance | None:
    matches = [
        wallet_balance
        for wallet_balance in wallet.wallet_balances
        if wallet_balance.wallet_id == wallet.id and wallet_balance.coin_id == coin_id
    ]
    if len(matches) > 1:
        raise ValueError(
            "wallet funding wallet balance context is ambiguous: "
            f"wallet_id={wallet.id} coin_id={coin_id}"
        )
    return matches[0] if matches else None


def _wallet_coin_balance(*, wallet: Wallet, coin_id: UUID) -> Decimal:
    wallet_balance = _find_wallet_balance(wallet=wallet, coin_id=coin_id)
    return (
        non_negative_amount(
            wallet_balance.balance,
            field_name="wallet balance",
        )
        if wallet_balance is not None
        else ZERO_AMOUNT
    )


def _last_transaction_id(*, wallet: Wallet, coin_id: UUID) -> UUID | None:
    candidates = [
        transaction.id
        for transaction in wallet.transactions
        if transaction.coin_id == coin_id
    ]
    return sorted(candidates, key=str)[-1] if candidates else None


def _require_non_empty(value: str, *, field_name: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is required")
    return raw


__all__ = [
    "EconomyWalletFundingLanes",
    "EconomyWalletFundingOperationContext",
    "EconomyWalletFundingRuntimeContext",
    "WalletBalanceDescribeReceipt",
    "WalletFundingPrepareReceipt",
    "WalletFundingCancelReceipt",
    "WalletFundingRecordReceipt",
    "build_economy_wallet_funding_lanes",
    "describe_wallet_balance",
    "hydrate_wallet_funding_intent_at_commit",
    "prepare_wallet_funding",
    "record_verified_wallet_funding",
    "record_wallet_funding_expiration",
    "resolve_economy_wallet_funding_runtime_context",
]
