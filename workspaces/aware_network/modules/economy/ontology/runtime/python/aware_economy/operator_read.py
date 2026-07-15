from __future__ import annotations

from collections.abc import Awaitable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from inspect import isawaitable
from typing import Any, TypeVar, cast
from uuid import UUID

from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalBalanceSummary,
)
from aware_economy_service_dto.economy.service import EconomyWalletCapitalEscrowSummary
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalConversionQuoteSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveRequest,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveResponse,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFundingProviderSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalProviderLifecycleSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalReservationSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalSettlementSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalTransactionExternalSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalTransactionIntentSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalTransactionSummary,
)
from aware_economy_service_dto.economy.view import (
    EconomyWalletCapitalActionViewStateV1,
)
from aware_economy_service_dto.economy.view import (
    EconomyWalletCapitalActivityViewStateV1,
)
from aware_economy_service_dto.economy.view import (
    EconomyWalletCapitalBalanceViewStateV1,
)
from aware_economy_service_dto.economy.view import (
    EconomyWalletCapitalFundingIntentViewStateV1,
)
from aware_economy_service_dto.economy.view import (
    EconomyWalletCapitalFundingProviderViewStateV1,
)
from aware_economy_service_dto.economy.view import EconomyWalletCapitalViewStateV1
from aware_economy_ontology_orm_models.escrow.escrow import Escrow as EscrowOrmModel
from aware_economy_ontology_orm_models.external_capital.external_capital_provider_config import (
    ExternalCapitalProviderConfig as ExternalCapitalProviderConfigOrmModel,
)
from aware_economy_ontology_orm_models.external_capital.external_capital_provider_route import (
    ExternalCapitalProviderRoute as ExternalCapitalProviderRouteOrmModel,
)
from aware_economy_ontology_orm_models.finance.finance_entity import (
    FinanceEntity as FinanceEntityOrmModel,
)
from aware_economy_ontology_orm_models.smart_contract.smart_contract_reservation import (
    SmartContractReservation as SmartContractReservationOrmModel,
)
from aware_economy_ontology_orm_models.smart_contract.smart_contract_settlement import (
    SmartContractSettlement as SmartContractSettlementOrmModel,
)
from aware_economy_ontology_orm_models.transaction.provider_lifecycle_receipt import (
    ProviderLifecycleReceipt as ProviderLifecycleReceiptOrmModel,
)
from aware_economy_ontology_orm_models.transaction.capital_conversion_quote import (
    CapitalConversionQuote as CapitalConversionQuoteOrmModel,
)
from aware_economy_ontology_orm_models.transaction.transaction import (
    Transaction as TransactionOrmModel,
)
from aware_economy_ontology_orm_models.transaction.transaction_external import (
    TransactionExternal as TransactionExternalOrmModel,
)
from aware_economy_ontology_orm_models.transaction.transaction_intent import (
    TransactionIntent as TransactionIntentOrmModel,
)
from aware_economy_ontology_orm_models.wallet.wallet import Wallet as WalletOrmModel
from aware_economy_ontology_orm_models.wallet.wallet_balance import (
    WalletBalance as WalletBalanceOrmModel,
)

_T = TypeVar("_T")
_MAX_LIMIT = 200
ECONOMY_WALLET_CAPITAL_API_VIEW_REF = "economy.wallet_capital"
ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF = "Wallet.home"
ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF = (
    "aware_economy.operator_read.resolve_wallet_capital_view_state_from_economy_replica"
)
_FINAL_FUNDING_INTENT_STATUSES = frozenset(
    {
        "applied",
        "cancelled",
        "canceled",
        "confirmed",
        "failed",
        "processed",
        "settled",
    }
)


@dataclass(frozen=True, slots=True)
class EconomyOperatorReplicaReadModels:
    wallet_model: Any
    wallet_balance_model: Any
    finance_entity_model: Any
    external_capital_provider_config_model: Any
    external_capital_provider_route_model: Any
    capital_conversion_quote_model: Any
    transaction_intent_model: Any
    transaction_external_model: Any
    transaction_model: Any
    provider_lifecycle_receipt_model: Any
    escrow_model: Any
    smart_contract_reservation_model: Any
    smart_contract_settlement_model: Any


DEFAULT_ECONOMY_OPERATOR_REPLICA_READ_MODELS = EconomyOperatorReplicaReadModels(
    wallet_model=WalletOrmModel,
    wallet_balance_model=WalletBalanceOrmModel,
    finance_entity_model=FinanceEntityOrmModel,
    external_capital_provider_config_model=ExternalCapitalProviderConfigOrmModel,
    external_capital_provider_route_model=ExternalCapitalProviderRouteOrmModel,
    capital_conversion_quote_model=CapitalConversionQuoteOrmModel,
    transaction_intent_model=TransactionIntentOrmModel,
    transaction_external_model=TransactionExternalOrmModel,
    transaction_model=TransactionOrmModel,
    provider_lifecycle_receipt_model=ProviderLifecycleReceiptOrmModel,
    escrow_model=EscrowOrmModel,
    smart_contract_reservation_model=SmartContractReservationOrmModel,
    smart_contract_settlement_model=SmartContractSettlementOrmModel,
)


async def resolve_wallet_capital_frame_from_economy_replica(
    *,
    request: EconomyWalletCapitalFrameResolveRequest,
    models: EconomyOperatorReplicaReadModels | None = None,
) -> EconomyWalletCapitalFrameResolveResponse:
    read_models = (
        models if models is not None else DEFAULT_ECONOMY_OPERATOR_REPLICA_READ_MODELS
    )
    _ = _optional_uuid(request.actor_id, field_name="actor_id")
    wallet_id = _required_uuid(request.wallet_id, field_name="wallet_id")
    coin_id = _optional_uuid(request.coin_id, field_name="coin_id")
    limit = _bounded_limit(getattr(request, "limit", None))

    wallet = await _by_id(read_models.wallet_model, wallet_id)
    if wallet is None:
        return EconomyWalletCapitalFrameResolveResponse(
            wallet_id=str(wallet_id),
            wallet_public_id=None,
            finance_entity_id=None,
            coin_id=_optional_uuid_text(coin_id),
            ready=False,
            balances=[],
            funding_providers=[],
            transaction_intents=[],
            transaction_externals=[],
            transactions=[],
            reservations=[],
            escrows=[],
            settlements=[],
            provider_lifecycle_receipts=[],
            activity_count=0,
            info="economy wallet not found",
        )

    wallet_public_id = _optional_uuid_attr(wallet, "wallet_public_id")
    finance_entity = await _finance_entity_for_wallet(
        read_models=read_models,
        wallet_id=wallet_id,
    )
    finance_entity_id = (
        _optional_uuid_attr(finance_entity, "id")
        if finance_entity is not None
        else None
    )

    balances = await _wallet_balance_summaries(
        read_models=read_models,
        wallet_id=wallet_id,
        wallet_public_id=wallet_public_id,
        finance_entity_id=finance_entity_id,
        coin_id=coin_id,
        limit=limit,
    )
    funding_providers = (
        await _funding_provider_summaries(
            read_models=read_models,
            coin_id=coin_id,
        )
        if request.include_funding_providers
        else []
    )
    transaction_intents = (
        await _transaction_intent_summaries(
            read_models=read_models,
            finance_entity_id=finance_entity_id,
            coin_id=coin_id,
            limit=limit,
        )
        if request.include_transaction_intents
        else []
    )
    transactions = (
        await _transaction_summaries(
            read_models=read_models,
            wallet_public_id=wallet_public_id,
            coin_id=coin_id,
            limit=limit,
        )
        if request.include_transactions
        else []
    )
    transaction_externals = (
        await _transaction_external_summaries(
            read_models=read_models,
            transactions=transactions,
            limit=limit,
        )
        if request.include_transaction_externals
        else []
    )
    escrows = (
        await _escrow_summaries(
            read_models=read_models,
            wallet_public_id=wallet_public_id,
            coin_id=coin_id,
            limit=limit,
        )
        if request.include_escrows
        else []
    )
    reservations = (
        await _reservation_summaries(
            read_models=read_models,
            escrows=escrows,
            limit=limit,
        )
        if request.include_reservations
        else []
    )
    settlements = (
        await _settlement_summaries(
            read_models=read_models,
            wallet_public_id=wallet_public_id,
            reservation_summaries=reservations,
            coin_id=coin_id,
            limit=limit,
        )
        if request.include_settlements
        else []
    )
    provider_lifecycle_receipts = (
        await _provider_lifecycle_summaries(
            read_models=read_models,
            wallet_id=wallet_id,
            coin_id=coin_id,
            limit=limit,
        )
        if request.include_provider_lifecycle
        else []
    )
    activity_count = (
        len(transaction_intents)
        + len(transaction_externals)
        + len(transactions)
        + len(reservations)
        + len(escrows)
        + len(settlements)
        + len(provider_lifecycle_receipts)
    )
    return EconomyWalletCapitalFrameResolveResponse(
        wallet_id=str(wallet_id),
        wallet_public_id=_optional_uuid_text(wallet_public_id),
        finance_entity_id=_optional_uuid_text(finance_entity_id),
        coin_id=_optional_uuid_text(coin_id),
        ready=bool(balances),
        balances=balances,
        funding_providers=funding_providers,
        transaction_intents=transaction_intents,
        transaction_externals=transaction_externals,
        transactions=transactions,
        reservations=reservations,
        escrows=escrows,
        settlements=settlements,
        provider_lifecycle_receipts=provider_lifecycle_receipts,
        activity_count=activity_count,
        info="economy wallet capital frame resolved",
    )


async def resolve_wallet_capital_view_state_from_economy_replica(
    *,
    request: EconomyWalletCapitalFrameResolveRequest,
    models: EconomyOperatorReplicaReadModels | None = None,
) -> EconomyWalletCapitalViewStateV1:
    frame = await resolve_wallet_capital_frame_from_economy_replica(
        request=request,
        models=models,
    )
    return wallet_capital_view_state_from_frame(frame)


def wallet_capital_view_state_from_frame(
    frame: EconomyWalletCapitalFrameResolveResponse,
    *,
    provenance: Mapping[str, object] | None = None,
) -> EconomyWalletCapitalViewStateV1:
    selected_coin_id = frame.coin_id or (
        frame.balances[0].coin_id if frame.balances else None
    )
    balances = [_wallet_balance_view_state(balance) for balance in frame.balances]
    activity = _wallet_capital_activity(frame)
    blockers = _wallet_capital_blockers(frame=frame, selected_coin_id=selected_coin_id)
    funding_providers = _wallet_capital_funding_providers(
        frame=frame,
        default_coin_id=selected_coin_id,
    )
    pending_funding_intents = _wallet_capital_pending_funding_intents(frame)
    actions = _wallet_capital_actions(
        frame=frame,
        selected_coin_id=selected_coin_id,
        can_fund_wallet=not blockers,
        blockers=blockers,
    )
    return EconomyWalletCapitalViewStateV1(
        view_ref=ECONOMY_WALLET_CAPITAL_API_VIEW_REF,
        root_projection_ref=ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF,
        operation="refresh_wallet_capital",
        status=_wallet_capital_view_status(frame=frame, blockers=blockers),
        status_tone=_wallet_capital_status_tone(frame=frame, blockers=blockers),
        wallet_id=frame.wallet_id,
        wallet_public_id=frame.wallet_public_id,
        finance_entity_id=frame.finance_entity_id,
        coin_id=selected_coin_id,
        ready=frame.ready,
        refresh_action_key="refresh_wallet_capital",
        funding_action_key="fund_wallet",
        action_keys=[action.action_key for action in actions],
        actions=actions,
        action_count=len(actions),
        can_fund_wallet=not blockers,
        funding_status="ready" if not blockers else "blocked",
        funding_disabled_reason="; ".join(blockers) if blockers else None,
        funding_providers=funding_providers,
        funding_provider_count=len(funding_providers),
        pending_funding_intents=pending_funding_intents,
        pending_funding_intent_count=len(pending_funding_intents),
        balances=balances,
        activity=activity,
        activity_count=len(activity),
        transaction_intent_count=len(frame.transaction_intents),
        transaction_external_count=len(frame.transaction_externals),
        transaction_count=len(frame.transactions),
        reservation_count=len(frame.reservations),
        escrow_count=len(frame.escrows),
        settlement_count=len(frame.settlements),
        provider_lifecycle_receipt_count=len(frame.provider_lifecycle_receipts),
        info=frame.info,
        empty_message="No wallet capital activity yet.",
        blockers=blockers,
        provenance={
            "source_kind": "ontology_replica",
            "state_provider_ref": ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF,
            "api_view_ref": ECONOMY_WALLET_CAPITAL_API_VIEW_REF,
            "root_projection_ref": ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF,
            "frame_operation": frame.operation,
            "balance_count": len(balances),
            "activity_count": len(activity),
            **dict(provenance or {}),
        },
    )


async def _finance_entity_for_wallet(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_id: UUID,
) -> object | None:
    finance_entities = await _many(
        read_models.finance_entity_model, wallet_id=wallet_id
    )
    finance_entities.sort(
        key=lambda item: (
            _str_attr(item, "role_key", default="primary") != "primary",
            _str_attr(item, "role_key", default="primary"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return finance_entities[0] if finance_entities else None


async def _wallet_balance_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_id: UUID,
    wallet_public_id: UUID | None,
    finance_entity_id: UUID | None,
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalBalanceSummary]:
    rows = await _many(read_models.wallet_balance_model, wallet_id=wallet_id)
    rows = _filter_by_optional_coin(rows, coin_id=coin_id)
    rows.sort(
        key=lambda item: (
            _uuid_text(_uuid_attr(item, "coin_id")),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalBalanceSummary(
            wallet_balance_id=_uuid_text(_uuid_attr(row, "id")),
            wallet_id=_uuid_text(wallet_id),
            wallet_public_id=_optional_uuid_text(wallet_public_id),
            finance_entity_id=_optional_uuid_text(finance_entity_id),
            coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
            balance=_decimal_attr(row, "balance"),
            held_balance=_decimal_attr(row, "held_balance"),
            available_balance=_available_amount(row),
        )
        for row in rows[:limit]
    ]


async def _funding_provider_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    coin_id: UUID | None,
) -> list[EconomyWalletCapitalFundingProviderSummary]:
    configs = await _many(read_models.external_capital_provider_config_model)
    active_configs_by_id = {
        _uuid_attr(config, "id"): config
        for config in configs
        if _status_text(config, "status") == "active"
    }
    route_filters: dict[str, object] = {}
    if coin_id is not None:
        route_filters["target_coin_id"] = coin_id
    routes = await _many(
        read_models.external_capital_provider_route_model,
        **route_filters,
    )
    summaries: list[EconomyWalletCapitalFundingProviderSummary] = []
    for route in routes:
        if _status_text(route, "status") != "active":
            continue
        provider_config_id = _uuid_attr(
            route,
            "external_capital_provider_config_id",
        )
        config = active_configs_by_id.get(provider_config_id)
        if config is None:
            continue
        summaries.append(
            EconomyWalletCapitalFundingProviderSummary(
                provider_config_id=str(provider_config_id),
                provider_route_id=_uuid_text(_uuid_attr(route, "id")),
                provider_finance_entity_id=_uuid_text(
                    _uuid_attr(config, "provider_finance_entity_id")
                ),
                provider_key=_str_attr(config, "provider_key"),
                label=_optional_str_attr(config, "label"),
                route_key=_str_attr(route, "route_key"),
                target_coin_id=_uuid_text(_uuid_attr(route, "target_coin_id")),
                external_currency=_str_attr(route, "external_currency"),
                external_minor_unit_exponent=_int_attr(
                    route,
                    "external_minor_unit_exponent",
                ),
                conversion_mode=_status_text(route, "conversion_mode"),
                min_external_amount_minor=_optional_int_attr(
                    route,
                    "min_external_amount_minor",
                ),
                max_external_amount_minor=_optional_int_attr(
                    route,
                    "max_external_amount_minor",
                ),
                status="active",
            )
        )
    summaries.sort(
        key=lambda item: (
            item.provider_key,
            item.route_key,
            item.provider_route_id,
        )
    )
    return summaries


async def _transaction_intent_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    finance_entity_id: UUID | None,
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalTransactionIntentSummary]:
    if finance_entity_id is None:
        return []
    rows = _dedupe_by_id(
        await _many(
            read_models.transaction_intent_model,
            recipient_finance_entity_id=finance_entity_id,
        )
    )
    rows = _filter_by_optional_coin(rows, coin_id=coin_id)
    rows.sort(
        key=lambda item: (
            _str_attr(item, "funding_intent_key"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    quotes_by_id = {
        _uuid_attr(quote, "id"): quote
        for quote in await _many(read_models.capital_conversion_quote_model)
    }
    summaries: list[EconomyWalletCapitalTransactionIntentSummary] = []
    for row in rows[:limit]:
        quote_id = _uuid_attr(row, "capital_conversion_quote_id")
        quote = quotes_by_id.get(quote_id)
        if quote is None:
            raise RuntimeError(
                "Economy wallet capital intent is missing its committed "
                f"CapitalConversionQuote: {quote_id}"
            )
        summaries.append(
            EconomyWalletCapitalTransactionIntentSummary(
                transaction_intent_id=_uuid_text(_uuid_attr(row, "id")),
                provider_config_id=_uuid_text(_uuid_attr(row, "provider_config_id")),
                recipient_finance_entity_id=_uuid_text(
                    _uuid_attr(row, "recipient_finance_entity_id")
                ),
                recipient_wallet_id=_uuid_text(_uuid_attr(row, "recipient_wallet_id")),
                recipient_wallet_public_id=_uuid_text(
                    _uuid_attr(row, "recipient_wallet_public_id")
                ),
                coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
                amount=_decimal_attr(row, "amount"),
                funding_intent_key=_str_attr(row, "funding_intent_key"),
                idempotency_key=_str_attr(row, "idempotency_key"),
                provider_key=_str_attr(row, "provider_key"),
                status=_status_text(row, "status"),
                created_at=_datetime_text(row, "created_at"),
                updated_at=_optional_datetime_text(row, "updated_at"),
                capital_conversion_quote=_capital_conversion_quote_summary(quote),
            )
        )
    return summaries


def _capital_conversion_quote_summary(
    quote: object,
) -> EconomyWalletCapitalConversionQuoteSummary:
    return EconomyWalletCapitalConversionQuoteSummary(
        capital_conversion_quote_id=_uuid_text(_uuid_attr(quote, "id")),
        provider_route_id=_uuid_text(_uuid_attr(quote, "provider_route_id")),
        target_coin_id=_uuid_text(_uuid_attr(quote, "target_coin_id")),
        external_amount_minor=_int_attr(quote, "external_amount_minor"),
        external_currency=_str_attr(quote, "external_currency"),
        target_amount=_decimal_attr(quote, "target_amount"),
        conversion_mode=_status_text(quote, "conversion_mode"),
        quote_source=_str_attr(quote, "source"),
        quote_hash=_str_attr(quote, "quote_hash"),
        quote_captured_at=_datetime_text(quote, "captured_at"),
        quote_expires_at=_optional_datetime_text(quote, "expires_at"),
    )


async def _transaction_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_public_id: UUID | None,
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalTransactionSummary]:
    if wallet_public_id is None:
        return []
    rows = _dedupe_by_id(
        [
            *await _many(
                read_models.transaction_model,
                source_wallet_public_id=wallet_public_id,
            ),
            *await _many(
                read_models.transaction_model,
                target_wallet_public_id=wallet_public_id,
            ),
        ]
    )
    rows = _filter_by_optional_coin(rows, coin_id=coin_id)
    rows.sort(
        key=lambda item: (_int_attr(item, "nonce"), _uuid_text(_uuid_attr(item, "id")))
    )
    return [
        EconomyWalletCapitalTransactionSummary(
            transaction_id=_uuid_text(_uuid_attr(row, "id")),
            source_wallet_public_id=_uuid_text(
                _uuid_attr(row, "source_wallet_public_id")
            ),
            target_wallet_public_id=_uuid_text(
                _uuid_attr(row, "target_wallet_public_id")
            ),
            coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
            coin_amount=_decimal_attr(row, "coin_amount"),
            gas_price=_decimal_attr(row, "gas_price"),
            nonce=_int_attr(row, "nonce"),
            status=_status_text(row, "status"),
            transaction_hash=_str_attr(row, "transaction_hash"),
            idempotency_key=_optional_str_attr(row, "idempotency_key"),
            description=_optional_str_attr(row, "description"),
            confirmed_at=_optional_datetime_text(row, "confirmed_at"),
            source_previous_coin_balance=_optional_decimal_attr(
                row, "source_previous_coin_balance"
            ),
            target_previous_coin_balance=_optional_decimal_attr(
                row, "target_previous_coin_balance"
            ),
        )
        for row in rows[:limit]
    ]


async def _transaction_external_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    transactions: list[EconomyWalletCapitalTransactionSummary],
    limit: int,
) -> list[EconomyWalletCapitalTransactionExternalSummary]:
    rows: list[object] = []
    for transaction in transactions[:limit]:
        rows.extend(
            await _many(
                read_models.transaction_external_model,
                transaction_id=UUID(transaction.transaction_id),
            )
        )
    rows = _dedupe_by_id(rows)
    rows.sort(
        key=lambda item: (
            _optional_datetime_sort_key(item, "processed_at"),
            _str_attr(item, "provider_event_id"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalTransactionExternalSummary(
            transaction_external_id=_uuid_text(_uuid_attr(row, "id")),
            transaction_id=_uuid_text(_uuid_attr(row, "transaction_id")),
            transaction_intent_id=_uuid_text(_uuid_attr(row, "transaction_intent_id")),
            provider_config_id=_uuid_text(_uuid_attr(row, "provider_config_id")),
            capital_conversion_quote_id=_uuid_text(
                _uuid_attr(row, "capital_conversion_quote_id")
            ),
            provider_finance_entity_id=_uuid_text(
                _uuid_attr(row, "provider_finance_entity_id")
            ),
            provider_key=_str_attr(row, "provider_key"),
            provider_event_id=_str_attr(row, "provider_event_id"),
            provider_public_reference=_str_attr(row, "provider_public_reference"),
            provider_payload_hash=_str_attr(row, "provider_payload_hash"),
            external_amount_minor=_int_attr(row, "external_amount_minor"),
            external_currency=_str_attr(row, "external_currency"),
            quote_hash=_str_attr(row, "quote_hash"),
            idempotency_key=_str_attr(row, "idempotency_key"),
            status=_status_text(row, "status"),
            processed_at=_optional_datetime_text(row, "processed_at"),
            external_created_at=_optional_datetime_text(row, "external_created_at"),
            metadata_json=_json_object_attr(row, "metadata_json"),
        )
        for row in rows[:limit]
    ]


async def _escrow_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_public_id: UUID | None,
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalEscrowSummary]:
    if wallet_public_id is None:
        return []
    rows = await _many(read_models.escrow_model, wallet_public_id=wallet_public_id)
    rows = _filter_by_optional_coin(rows, coin_id=coin_id)
    rows.sort(
        key=lambda item: (
            _int_attr(item, "op_nonce"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalEscrowSummary(
            escrow_id=_uuid_text(_uuid_attr(row, "id")),
            wallet_public_id=_uuid_text(_uuid_attr(row, "wallet_public_id")),
            coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
            locked_amount=_decimal_attr(row, "locked_amount"),
            op_nonce=_int_attr(row, "op_nonce"),
            escrow_hash=_str_attr(row, "escrow_hash"),
            smart_contract_reservation_id=_uuid_text(
                _uuid_attr(row, "smart_contract_reservation_id")
            ),
            status=_status_text(row, "status"),
            description=_optional_str_attr(row, "description"),
        )
        for row in rows[:limit]
    ]


async def _reservation_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    escrows: list[EconomyWalletCapitalEscrowSummary],
    limit: int,
) -> list[EconomyWalletCapitalReservationSummary]:
    rows: list[object] = []
    for escrow in escrows[:limit]:
        row = await _by_id(
            read_models.smart_contract_reservation_model,
            UUID(escrow.smart_contract_reservation_id),
        )
        if row is not None:
            rows.append(row)
    rows = _dedupe_by_id(rows)
    rows.sort(
        key=lambda item: (
            _int_attr(item, "op_nonce"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalReservationSummary(
            reservation_id=_uuid_text(_uuid_attr(row, "id")),
            smart_contract_permit_id=_uuid_text(
                _uuid_attr(row, "smart_contract_permit_id")
            ),
            escrow_id=_optional_uuid_text(_optional_uuid_attr(row, "escrow_id")),
            rate_snapshot_id=_uuid_text(_uuid_attr(row, "rate_snapshot_id")),
            op_nonce=_int_attr(row, "op_nonce"),
            args_hash=_str_attr(row, "args_hash"),
            max_cost=_decimal_attr(row, "max_cost"),
            final_cost=_optional_decimal_attr(row, "final_cost"),
            status=_status_text(row, "status"),
            deadline=_optional_datetime_text(row, "deadline"),
        )
        for row in rows[:limit]
    ]


async def _settlement_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_public_id: UUID | None,
    reservation_summaries: list[EconomyWalletCapitalReservationSummary],
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalSettlementSummary]:
    rows: list[object] = []
    for reservation in reservation_summaries[:limit]:
        rows.extend(
            await _many(
                read_models.smart_contract_settlement_model,
                smart_contract_reservation_id=UUID(reservation.reservation_id),
            )
        )
    if wallet_public_id is not None:
        rows.extend(
            await _many(
                read_models.smart_contract_settlement_model,
                payer_wallet_public_id=wallet_public_id,
            )
        )
        rows.extend(
            await _many(
                read_models.smart_contract_settlement_model,
                receiver_wallet_public_id=wallet_public_id,
            )
        )
    rows = _dedupe_by_id(_filter_by_optional_coin(rows, coin_id=coin_id))
    rows.sort(
        key=lambda item: (
            _uuid_text(_uuid_attr(item, "smart_contract_reservation_id")),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalSettlementSummary(
            settlement_id=_uuid_text(_uuid_attr(row, "id")),
            smart_contract_reservation_id=_uuid_text(
                _uuid_attr(row, "smart_contract_reservation_id")
            ),
            payer_finance_entity_id=_uuid_text(
                _uuid_attr(row, "payer_finance_entity_id")
            ),
            payer_wallet_public_id=_uuid_text(
                _uuid_attr(row, "payer_wallet_public_id")
            ),
            receiver_finance_entity_id=_uuid_text(
                _uuid_attr(row, "receiver_finance_entity_id")
            ),
            receiver_wallet_public_id=_uuid_text(
                _uuid_attr(row, "receiver_wallet_public_id")
            ),
            coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
            final_cost=_decimal_attr(row, "final_cost"),
            status=_status_text(row, "status"),
        )
        for row in rows[:limit]
    ]


async def _provider_lifecycle_summaries(
    *,
    read_models: EconomyOperatorReplicaReadModels,
    wallet_id: UUID,
    coin_id: UUID | None,
    limit: int,
) -> list[EconomyWalletCapitalProviderLifecycleSummary]:
    rows = await _many(
        read_models.provider_lifecycle_receipt_model, wallet_id=wallet_id
    )
    rows = _filter_by_optional_coin(rows, coin_id=coin_id)
    rows.sort(
        key=lambda item: (
            _optional_datetime_sort_key(item, "processed_at"),
            _str_attr(item, "provider_event_id"),
            _uuid_text(_uuid_attr(item, "id")),
        )
    )
    return [
        EconomyWalletCapitalProviderLifecycleSummary(
            provider_lifecycle_receipt_id=_uuid_text(_uuid_attr(row, "id")),
            provider_finance_entity_id=_uuid_text(
                _uuid_attr(row, "provider_finance_entity_id")
            ),
            provider_key=_str_attr(row, "provider_key"),
            provider_event_id=_str_attr(row, "provider_event_id"),
            provider_lifecycle_object_id=_str_attr(row, "provider_lifecycle_object_id"),
            provider_lifecycle_effect_key=_str_attr(
                row, "provider_lifecycle_effect_key"
            ),
            idempotency_key=_str_attr(row, "idempotency_key"),
            wallet_finance_entity_id=_uuid_text(
                _uuid_attr(row, "wallet_finance_entity_id")
            ),
            wallet_id=_uuid_text(_uuid_attr(row, "wallet_id")),
            wallet_public_id=_uuid_text(_uuid_attr(row, "wallet_public_id")),
            coin_id=_uuid_text(_uuid_attr(row, "coin_id")),
            amount=_decimal_attr(row, "amount"),
            event_kind=_status_text(row, "event_kind"),
            status=_status_text(row, "status"),
            previous_balance=_decimal_attr(row, "previous_balance"),
            new_balance=_decimal_attr(row, "new_balance"),
            previous_held_balance=_decimal_attr(row, "previous_held_balance"),
            new_held_balance=_decimal_attr(row, "new_held_balance"),
            previous_available_balance=_decimal_attr(row, "previous_available_balance"),
            new_available_balance=_decimal_attr(row, "new_available_balance"),
            provider_payment_reference=_str_attr(row, "provider_payment_reference"),
            provider_payload_hash=_str_attr(row, "provider_payload_hash"),
            transaction_id=_uuid_text(_uuid_attr(row, "transaction_id")),
            transaction_external_id=_uuid_text(
                _uuid_attr(row, "transaction_external_id")
            ),
            processed_at=_optional_datetime_text(row, "processed_at"),
            external_created_at=_optional_datetime_text(row, "external_created_at"),
            metadata_json=_json_object_attr(row, "metadata_json"),
        )
        for row in rows[:limit]
    ]


async def _by_id(model: Any, object_id: UUID) -> object | None:
    by_id = getattr(model, "by_id", None)
    if callable(by_id):
        return cast(object | None, await _await_maybe(by_id(object_id)))
    rows = await _many(model, id=object_id)
    return rows[0] if rows else None


async def _many(model: Any, **filters: object) -> list[object]:
    many = getattr(model, "many", None)
    if callable(many):
        return list(cast(Iterable[object], await _await_maybe(many(**filters))))
    where = getattr(model, "where", None)
    if not callable(where):
        raise TypeError(f"{model!r} does not expose ontology replica query methods")
    query = where(**filters)
    all_rows = getattr(query, "all", None)
    if not callable(all_rows):
        raise TypeError(f"{model!r} ontology replica query does not expose all()")
    return list(cast(Iterable[object], await _await_maybe(all_rows())))


async def _await_maybe(value: Awaitable[_T] | _T) -> _T:
    if isawaitable(value):
        return await cast(Awaitable[_T], value)
    return cast(_T, value)


def _dedupe_by_id(rows: Iterable[object]) -> list[object]:
    seen: set[UUID] = set()
    deduped: list[object] = []
    for row in rows:
        row_id = _uuid_attr(row, "id")
        if row_id in seen:
            continue
        seen.add(row_id)
        deduped.append(row)
    return deduped


def _filter_by_optional_coin(
    rows: Iterable[object], *, coin_id: UUID | None
) -> list[object]:
    if coin_id is None:
        return list(rows)
    return [row for row in rows if _uuid_attr(row, "coin_id") == coin_id]


def _required_uuid(value: str, *, field_name: str) -> UUID:
    parsed = _optional_uuid(value, field_name=field_name)
    if parsed is None:
        raise ValueError(f"{field_name} is required")
    return parsed


def _optional_uuid(value: str | None, *, field_name: str) -> UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID string") from exc


def _bounded_limit(value: int | None) -> int:
    if value is None:
        return 50
    return max(1, min(_MAX_LIMIT, int(value)))


def _uuid_attr(obj: object, field_name: str) -> UUID:
    value = getattr(obj, field_name)
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _optional_uuid_attr(obj: object, field_name: str) -> UUID | None:
    value = getattr(obj, field_name, None)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    return UUID(raw)


def _uuid_text(value: UUID) -> str:
    return str(value)


def _optional_uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _str_attr(obj: object, field_name: str, *, default: str = "") -> str:
    value = getattr(obj, field_name, default)
    if value is None:
        return default
    return _value_text(value)


def _optional_str_attr(obj: object, field_name: str) -> str | None:
    value = getattr(obj, field_name, None)
    if value is None:
        return None
    text = _value_text(value)
    return text if text else None


def _decimal_attr(obj: object, field_name: str) -> Decimal:
    value = getattr(obj, field_name)
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be materialized as Decimal")
    return value


def _optional_decimal_attr(obj: object, field_name: str) -> Decimal | None:
    value = getattr(obj, field_name, None)
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be materialized as Decimal")
    return value


def _int_attr(obj: object, field_name: str) -> int:
    return int(getattr(obj, field_name))


def _optional_int_attr(obj: object, field_name: str) -> int | None:
    value = getattr(obj, field_name, None)
    return int(value) if value is not None else None


def _status_text(obj: object, field_name: str) -> str:
    return _value_text(getattr(obj, field_name))


def _value_text(value: object) -> str:
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    return str(value)


def _optional_datetime_text(obj: object, field_name: str) -> str | None:
    value = getattr(obj, field_name, None)
    if value is None:
        return None
    if isinstance(value, datetime | date):
        return value.isoformat()
    text = str(value).strip()
    return text if text else None


def _datetime_text(obj: object, field_name: str) -> str:
    value = _optional_datetime_text(obj, field_name)
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _optional_datetime_sort_key(obj: object, field_name: str) -> str:
    return _optional_datetime_text(obj, field_name) or ""


def _json_object_attr(obj: object, field_name: str) -> dict[str, object] | None:
    value = getattr(obj, field_name, None)
    if value is None:
        return None
    if isinstance(value, Mapping):
        return {str(key): cast(object, item) for key, item in value.items()}
    return cast(dict[str, object], value)


def _available_amount(row: object) -> Decimal:
    return _decimal_attr(row, "balance") - _decimal_attr(row, "held_balance")


def _wallet_balance_view_state(
    balance: EconomyWalletCapitalBalanceSummary,
) -> EconomyWalletCapitalBalanceViewStateV1:
    return EconomyWalletCapitalBalanceViewStateV1(
        wallet_balance_id=balance.wallet_balance_id,
        wallet_id=balance.wallet_id,
        wallet_public_id=balance.wallet_public_id,
        finance_entity_id=balance.finance_entity_id,
        coin_id=balance.coin_id,
        balance=balance.balance,
        held_balance=balance.held_balance,
        available_balance=balance.available_balance,
        status="ready",
    )


def _wallet_capital_actions(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    selected_coin_id: str | None,
    can_fund_wallet: bool,
    blockers: list[str],
) -> list[EconomyWalletCapitalActionViewStateV1]:
    funding_disabled_reason = "; ".join(blockers) if blockers else None
    return [
        EconomyWalletCapitalActionViewStateV1(
            action_key="refresh_wallet_capital",
            label="Refresh",
            enabled=bool(frame.wallet_id),
            status="ready" if frame.wallet_id else "blocked",
            disabled_reason=None if frame.wallet_id else "wallet_id is required",
            input_hints={
                "endpoint_ref": (
                    "economy.wallet_capital_frame_resolve."
                    "resolve_wallet_capital_frame"
                ),
                "request_model_ref": (
                    "aware_economy_service_dto.economy.service."
                    "EconomyWalletCapitalFrameResolveRequest"
                ),
                "derived_fields": {
                    "wallet_id": frame.wallet_id,
                    "coin_id": selected_coin_id,
                },
            },
            provenance={"api_view_ref": ECONOMY_WALLET_CAPITAL_API_VIEW_REF},
        ),
        EconomyWalletCapitalActionViewStateV1(
            action_key="fund_wallet",
            label="Fund wallet",
            enabled=can_fund_wallet,
            status="ready" if can_fund_wallet else "blocked",
            disabled_reason=funding_disabled_reason,
            input_hints={
                "endpoint_ref": "economy.wallet_funding_prepare.prepare_wallet_funding",
                "request_model_ref": (
                    "aware_economy_service_dto.economy.service."
                    "EconomyWalletFundingPrepareRequest"
                ),
                "required_fields": [
                    "provider_key",
                    "amount",
                    "funding_intent_key",
                    "idempotency_key",
                ],
                "derived_fields": {
                    "target_wallet_id": frame.wallet_id,
                    "coin_id": selected_coin_id,
                },
            },
            provenance={"api_view_ref": ECONOMY_WALLET_CAPITAL_API_VIEW_REF},
        ),
    ]


def _wallet_capital_blockers(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    selected_coin_id: str | None,
) -> list[str]:
    if frame.info == "economy wallet not found":
        return ["wallet_not_found"]
    blockers: list[str] = []
    if not frame.wallet_public_id:
        blockers.append("wallet_public_id_missing")
    if not frame.finance_entity_id:
        blockers.append("finance_entity_id_missing")
    if not selected_coin_id:
        blockers.append("coin_id_missing")
    if selected_coin_id and not frame.funding_providers:
        blockers.append("external_capital_provider_route_missing")
    return blockers


def _wallet_capital_view_status(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    blockers: list[str],
) -> str:
    if "wallet_not_found" in blockers:
        return "blocked"
    if frame.ready:
        return "ready"
    return "empty"


def _wallet_capital_status_tone(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    blockers: list[str],
) -> str:
    if blockers:
        return "warning"
    if frame.ready:
        return "success"
    return "neutral"


def _wallet_capital_funding_providers(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    default_coin_id: str | None,
) -> list[EconomyWalletCapitalFundingProviderViewStateV1]:
    return [
        EconomyWalletCapitalFundingProviderViewStateV1(
            provider_config_id=provider.provider_config_id,
            provider_route_id=provider.provider_route_id,
            provider_finance_entity_id=provider.provider_finance_entity_id,
            provider_key=provider.provider_key,
            label=provider.label or provider.provider_key,
            status=provider.status,
            route_key=provider.route_key,
            default_coin_id=provider.target_coin_id,
            supported_coin_ids=[provider.target_coin_id],
            external_currency=provider.external_currency,
            external_minor_unit_exponent=provider.external_minor_unit_exponent,
            conversion_mode=provider.conversion_mode,
            min_external_amount_minor=provider.min_external_amount_minor,
            max_external_amount_minor=provider.max_external_amount_minor,
            provenance={
                "source_kind": "external_capital_provider_route",
                "selected_coin_id": default_coin_id,
            },
        )
        for provider in frame.funding_providers
    ]


def _wallet_capital_pending_funding_intents(
    frame: EconomyWalletCapitalFrameResolveResponse,
) -> list[EconomyWalletCapitalFundingIntentViewStateV1]:
    pending: list[EconomyWalletCapitalFundingIntentViewStateV1] = []
    for intent in frame.transaction_intents:
        if intent.status.lower() in _FINAL_FUNDING_INTENT_STATUSES:
            continue
        pending.append(
            EconomyWalletCapitalFundingIntentViewStateV1(
                funding_intent_ref=intent.funding_intent_key,
                transaction_intent_id=intent.transaction_intent_id,
                provider_config_id=intent.provider_config_id,
                provider_key=intent.provider_key,
                coin_id=intent.coin_id,
                amount=intent.amount,
                idempotency_key=intent.idempotency_key,
                status=intent.status,
                created_at=intent.created_at,
                updated_at=intent.updated_at,
                capital_conversion_quote_id=(
                    intent.capital_conversion_quote.capital_conversion_quote_id
                ),
                provider_route_id=intent.capital_conversion_quote.provider_route_id,
                external_amount_minor=(
                    intent.capital_conversion_quote.external_amount_minor
                ),
                external_currency=intent.capital_conversion_quote.external_currency,
                target_amount=intent.capital_conversion_quote.target_amount,
                conversion_mode=intent.capital_conversion_quote.conversion_mode,
                quote_source=intent.capital_conversion_quote.quote_source,
                quote_hash=intent.capital_conversion_quote.quote_hash,
                quote_captured_at=(intent.capital_conversion_quote.quote_captured_at),
                quote_expires_at=intent.capital_conversion_quote.quote_expires_at,
                provenance={
                    "source_kind": "transaction_intent",
                    "capital_truth": "committed_quote",
                },
            )
        )
    return pending


def _wallet_capital_activity(
    frame: EconomyWalletCapitalFrameResolveResponse,
) -> list[EconomyWalletCapitalActivityViewStateV1]:
    activity: list[EconomyWalletCapitalActivityViewStateV1] = []
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"transaction_intent:{intent.transaction_intent_id}",
            activity_kind="wallet_funding_intent",
            status=intent.status,
            amount=intent.amount,
            coin_id=intent.coin_id,
            transaction_intent_id=intent.transaction_intent_id,
            provider_key=intent.provider_key,
            idempotency_key=intent.funding_intent_key,
            description="Wallet funding intent",
            provenance={"source_kind": "transaction_intent"},
        )
        for intent in frame.transaction_intents
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"transaction_external:{external.transaction_external_id}",
            activity_kind="provider_external_receipt",
            status=external.status,
            occurred_at=external.processed_at or external.external_created_at,
            transaction_external_id=external.transaction_external_id,
            transaction_id=external.transaction_id,
            provider_key=_mapping_text(external.metadata_json, "provider_key"),
            idempotency_key=external.idempotency_key,
            description="External provider receipt",
            provenance={
                "source_kind": "transaction_external",
                "provider_event_id": external.provider_event_id,
            },
        )
        for external in frame.transaction_externals
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"transaction:{transaction.transaction_id}",
            activity_kind="wallet_transaction",
            status=transaction.status,
            occurred_at=transaction.confirmed_at,
            amount=transaction.coin_amount,
            coin_id=transaction.coin_id,
            transaction_id=transaction.transaction_id,
            idempotency_key=transaction.idempotency_key,
            description=transaction.description or "Wallet transaction",
            provenance={
                "source_kind": "transaction",
                "transaction_hash": transaction.transaction_hash,
            },
        )
        for transaction in frame.transactions
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"reservation:{reservation.reservation_id}",
            activity_kind="smart_contract_reservation",
            status=reservation.status,
            occurred_at=reservation.deadline,
            amount=reservation.final_cost or reservation.max_cost,
            reservation_id=reservation.reservation_id,
            escrow_id=reservation.escrow_id,
            description="Smart-contract reservation",
            provenance={
                "source_kind": "smart_contract_reservation",
                "smart_contract_permit_id": reservation.smart_contract_permit_id,
                "rate_snapshot_id": reservation.rate_snapshot_id,
            },
        )
        for reservation in frame.reservations
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"escrow:{escrow.escrow_id}",
            activity_kind="escrow",
            status=escrow.status,
            amount=escrow.locked_amount,
            coin_id=escrow.coin_id,
            escrow_id=escrow.escrow_id,
            description=escrow.description or "Escrow",
            provenance={
                "source_kind": "escrow",
                "smart_contract_reservation_id": escrow.smart_contract_reservation_id,
            },
        )
        for escrow in frame.escrows
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=f"settlement:{settlement.settlement_id}",
            activity_kind="smart_contract_settlement",
            status=settlement.status,
            amount=settlement.final_cost,
            coin_id=settlement.coin_id,
            settlement_id=settlement.settlement_id,
            reservation_id=settlement.smart_contract_reservation_id,
            description="Smart-contract settlement",
            provenance={
                "source_kind": "smart_contract_settlement",
                "payer_wallet_public_id": settlement.payer_wallet_public_id,
                "receiver_wallet_public_id": settlement.receiver_wallet_public_id,
            },
        )
        for settlement in frame.settlements
    )
    activity.extend(
        EconomyWalletCapitalActivityViewStateV1(
            activity_ref=(
                "provider_lifecycle:" f"{receipt.provider_lifecycle_receipt_id}"
            ),
            activity_kind="provider_lifecycle",
            status=receipt.status,
            occurred_at=receipt.processed_at or receipt.external_created_at,
            amount=receipt.amount,
            coin_id=receipt.coin_id,
            transaction_id=receipt.transaction_id,
            transaction_external_id=receipt.transaction_external_id,
            provider_lifecycle_receipt_id=receipt.provider_lifecycle_receipt_id,
            provider_key=receipt.provider_key,
            idempotency_key=receipt.idempotency_key,
            description=receipt.event_kind,
            provenance={
                "source_kind": "provider_lifecycle_receipt",
                "provider_event_id": receipt.provider_event_id,
            },
        )
        for receipt in frame.provider_lifecycle_receipts
    )
    return activity


def _mapping_text(value: Mapping[str, object] | None, key: str) -> str | None:
    if not value:
        return None
    raw = value.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text if text else None


__all__ = [
    "ECONOMY_WALLET_CAPITAL_API_VIEW_REF",
    "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF",
    "ECONOMY_WALLET_CAPITAL_VIEW_PROVIDER_REF",
    "DEFAULT_ECONOMY_OPERATOR_REPLICA_READ_MODELS",
    "EconomyOperatorReplicaReadModels",
    "resolve_wallet_capital_frame_from_economy_replica",
    "resolve_wallet_capital_view_state_from_economy_replica",
    "wallet_capital_view_state_from_frame",
]
