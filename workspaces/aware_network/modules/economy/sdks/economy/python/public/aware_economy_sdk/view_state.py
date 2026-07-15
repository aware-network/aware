from __future__ import annotations

from collections.abc import Mapping

from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalBalanceSummary,
)
from aware_economy_service_dto.economy.service import (
    EconomyWalletCapitalFrameResolveResponse,
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

ECONOMY_WALLET_CAPITAL_API_VIEW_REF = "economy.wallet_capital"
ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF = "Wallet.home"
ECONOMY_WALLET_CAPITAL_SDK_PROVIDER_REF = (
    "aware_economy_sdk.view_state.wallet_capital_view_state_from_frame"
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


def wallet_capital_view_state_from_frame(
    frame: EconomyWalletCapitalFrameResolveResponse,
    *,
    provenance: Mapping[str, object] | None = None,
) -> EconomyWalletCapitalViewStateV1:
    selected_coin_id = frame.coin_id or (
        frame.balances[0].coin_id if frame.balances else None
    )
    balances = [_balance_view_state(balance) for balance in frame.balances]
    blockers = _funding_blockers(frame=frame, selected_coin_id=selected_coin_id)
    actions = _actions(
        frame=frame,
        selected_coin_id=selected_coin_id,
        can_fund_wallet=not blockers,
        blockers=blockers,
    )
    pending_funding_intents = _pending_funding_intents(frame)
    activity = _activity(frame)
    funding_providers = _funding_providers(
        frame=frame,
        default_coin_id=selected_coin_id,
    )
    return EconomyWalletCapitalViewStateV1(
        view_ref=ECONOMY_WALLET_CAPITAL_API_VIEW_REF,
        root_projection_ref=ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF,
        operation="refresh_wallet_capital",
        status=_status(frame=frame, blockers=blockers),
        status_tone=_status_tone(frame=frame, blockers=blockers),
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
        blockers=blockers,
        provenance={
            "source_kind": "economy_sdk",
            "state_provider_ref": ECONOMY_WALLET_CAPITAL_SDK_PROVIDER_REF,
            "api_view_ref": ECONOMY_WALLET_CAPITAL_API_VIEW_REF,
            "root_projection_ref": ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF,
            "frame_operation": frame.operation,
            "balance_count": len(balances),
            "activity_count": len(activity),
            **dict(provenance or {}),
        },
    )


def _balance_view_state(
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


def _actions(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    selected_coin_id: str | None,
    can_fund_wallet: bool,
    blockers: list[str],
) -> list[EconomyWalletCapitalActionViewStateV1]:
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
                "derived_fields": {
                    "wallet_id": frame.wallet_id,
                    "coin_id": selected_coin_id,
                },
            },
        ),
        EconomyWalletCapitalActionViewStateV1(
            action_key="fund_wallet",
            label="Fund wallet",
            enabled=can_fund_wallet,
            status="ready" if can_fund_wallet else "blocked",
            disabled_reason="; ".join(blockers) if blockers else None,
            input_hints={
                "endpoint_ref": "economy.wallet_funding_prepare.prepare_wallet_funding",
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
        ),
    ]


def _funding_blockers(
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


def _status(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    blockers: list[str],
) -> str:
    if "wallet_not_found" in blockers:
        return "blocked"
    if frame.ready:
        return "ready"
    return "empty"


def _status_tone(
    *,
    frame: EconomyWalletCapitalFrameResolveResponse,
    blockers: list[str],
) -> str:
    if blockers:
        return "warning"
    if frame.ready:
        return "success"
    return "neutral"


def _pending_funding_intents(
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


def _funding_providers(
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


def _activity(
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
        )
        for intent in frame.transaction_intents
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
        )
        for transaction in frame.transactions
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
            provider_lifecycle_receipt_id=receipt.provider_lifecycle_receipt_id,
            provider_key=receipt.provider_key,
            idempotency_key=receipt.idempotency_key,
            description=receipt.event_kind,
        )
        for receipt in frame.provider_lifecycle_receipts
    )
    return activity


__all__ = [
    "ECONOMY_WALLET_CAPITAL_API_VIEW_REF",
    "ECONOMY_WALLET_CAPITAL_ROOT_PROJECTION_REF",
    "ECONOMY_WALLET_CAPITAL_SDK_PROVIDER_REF",
    "wallet_capital_view_state_from_frame",
]
