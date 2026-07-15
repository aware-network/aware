from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from aware_economy.capital_amount import non_negative_amount, positive_amount
from aware_economy_ontology.transaction.provider_lifecycle_receipt_enums import (
    ProviderLifecycleEventKind,
)
from aware_economy_ontology_orm_models.transaction.provider_lifecycle_receipt import (
    ProviderLifecycleReceipt,
)
from aware_economy_ontology_orm_models.transaction.transaction_external import (
    TransactionExternal,
)
from aware_economy_ontology_orm_models.transaction.transaction_intent import (
    TransactionIntent,
)
from aware_economy_ontology_orm_models.transaction.transaction_intent_enums import (
    TransactionIntentStatus,
)
from aware_economy_service.wallet_funding_context import (
    ResolvedWalletFundingContext,
    resolve_wallet_funding_context_models,
)


@dataclass(frozen=True, slots=True)
class ResolvedProviderLifecycleContext:
    transaction_external: TransactionExternal
    funding: ResolvedWalletFundingContext
    amount: Decimal


async def resolve_provider_lifecycle_context_models(
    *,
    admitted_provider_actor_id: UUID,
    provider_key: str,
    provider_lifecycle_object_id: str,
    provider_payment_reference: str,
    external_amount_minor: int,
    external_currency: str,
    event_kind: ProviderLifecycleEventKind,
) -> ResolvedProviderLifecycleContext:
    provider_key = _required_text(provider_key, field_name="provider_key").casefold()
    provider_lifecycle_object_id = _required_text(
        provider_lifecycle_object_id,
        field_name="provider_lifecycle_object_id",
    )
    provider_payment_reference = _required_text(
        provider_payment_reference,
        field_name="provider_payment_reference",
    )
    external_currency = _required_text(
        external_currency,
        field_name="external_currency",
    ).upper()
    if external_amount_minor <= 0:
        raise ValueError("provider lifecycle external_amount_minor must be positive")

    external_matches = await TransactionExternal.many(
        provider_key=provider_key,
        provider_public_reference=provider_payment_reference,
    )
    if len(external_matches) != 1:
        raise ValueError(
            "provider lifecycle requires exactly one committed TransactionExternal "
            "for the provider payment reference"
        )
    transaction_external = external_matches[0]
    intent = await TransactionIntent.by_id(transaction_external.transaction_intent_id)
    if intent is None:
        raise ValueError("provider lifecycle TransactionIntent is missing")
    if intent.status != TransactionIntentStatus.confirmed:
        raise ValueError("provider lifecycle requires a confirmed funding intent")

    funding = await resolve_wallet_funding_context_models(
        intent=intent,
        admitted_provider_actor_id=admitted_provider_actor_id,
        require_active_provider_route=False,
    )
    _validate_external_funding_provenance(
        transaction_external=transaction_external,
        funding=funding,
        provider_key=provider_key,
        provider_payment_reference=provider_payment_reference,
        external_currency=external_currency,
    )

    amount = _target_amount_from_external_minor(
        external_amount_minor=external_amount_minor,
        external_minor_unit_exponent=(
            funding.provider_route.external_minor_unit_exponent
        ),
    )
    original_amount = positive_amount(
        funding.intent.amount,
        field_name="provider lifecycle original funding amount",
    )
    if amount > original_amount:
        raise ValueError(
            "provider lifecycle effect exceeds the original funding amount"
        )

    receipts = await ProviderLifecycleReceipt.many(
        transaction_external_id=transaction_external.id,
    )
    _validate_effect_history(
        receipts=receipts,
        provider_lifecycle_object_id=provider_lifecycle_object_id,
        provider_payment_reference=provider_payment_reference,
        event_kind=event_kind,
        amount=amount,
        original_amount=original_amount,
    )
    return ResolvedProviderLifecycleContext(
        transaction_external=transaction_external,
        funding=funding,
        amount=amount,
    )


def _validate_external_funding_provenance(
    *,
    transaction_external: TransactionExternal,
    funding: ResolvedWalletFundingContext,
    provider_key: str,
    provider_payment_reference: str,
    external_currency: str,
) -> None:
    if transaction_external.provider_key != provider_key:
        raise ValueError("provider lifecycle TransactionExternal provider mismatch")
    if transaction_external.provider_public_reference != provider_payment_reference:
        raise ValueError(
            "provider lifecycle TransactionExternal payment reference mismatch"
        )
    if transaction_external.provider_config_id != funding.provider_config.id:
        raise ValueError("provider lifecycle TransactionExternal config mismatch")
    if (
        transaction_external.provider_finance_entity_id
        != funding.provider_finance_entity.id
    ):
        raise ValueError(
            "provider lifecycle TransactionExternal FinanceEntity mismatch"
        )
    if transaction_external.capital_conversion_quote_id != funding.quote.id:
        raise ValueError("provider lifecycle TransactionExternal quote mismatch")
    if transaction_external.quote_hash != funding.quote.quote_hash:
        raise ValueError("provider lifecycle TransactionExternal quote hash mismatch")
    if (
        transaction_external.external_amount_minor
        != funding.quote.external_amount_minor
    ):
        raise ValueError("provider lifecycle TransactionExternal amount mismatch")
    if transaction_external.external_currency != external_currency:
        raise ValueError("provider lifecycle external currency mismatch")


def _target_amount_from_external_minor(
    *,
    external_amount_minor: int,
    external_minor_unit_exponent: int,
) -> Decimal:
    if external_minor_unit_exponent < 0 or external_minor_unit_exponent > 8:
        raise ValueError("provider lifecycle minor-unit exponent is invalid")
    return positive_amount(
        Decimal(external_amount_minor) / (Decimal(10) ** external_minor_unit_exponent),
        field_name="provider lifecycle amount",
    )


def _validate_effect_history(
    *,
    receipts: list[ProviderLifecycleReceipt],
    provider_lifecycle_object_id: str,
    provider_payment_reference: str,
    event_kind: ProviderLifecycleEventKind,
    amount: Decimal,
    original_amount: Decimal,
) -> None:
    event_kind_value = event_kind.value
    current_matches = [
        receipt
        for receipt in receipts
        if receipt.provider_lifecycle_object_id == provider_lifecycle_object_id
        and _enum_value(receipt.event_kind) == event_kind_value
    ]
    if len(current_matches) > 1:
        raise ValueError("provider lifecycle effect history is ambiguous")
    if current_matches:
        current = current_matches[0]
        if current.provider_payment_reference != provider_payment_reference:
            raise ValueError("provider lifecycle replay payment reference mismatch")
        if (
            non_negative_amount(
                current.amount,
                field_name="provider lifecycle replay amount",
            )
            != amount
        ):
            raise ValueError("provider lifecycle replay amount mismatch")

    if event_kind_value in {
        ProviderLifecycleEventKind.dispute_release.value,
        ProviderLifecycleEventKind.chargeback.value,
    }:
        opening = [
            receipt
            for receipt in receipts
            if receipt.provider_lifecycle_object_id == provider_lifecycle_object_id
            and _enum_value(receipt.event_kind)
            == ProviderLifecycleEventKind.dispute.value
        ]
        if len(opening) != 1:
            raise ValueError(
                "provider lifecycle dispute close requires one committed opening receipt"
            )
        if (
            positive_amount(
                opening[0].amount,
                field_name="provider lifecycle dispute opening amount",
            )
            != amount
        ):
            raise ValueError("provider lifecycle dispute close amount mismatch")

    irreversible_total = sum(
        (
            positive_amount(
                receipt.amount,
                field_name="provider lifecycle committed debit amount",
            )
            for receipt in receipts
            if _enum_value(receipt.event_kind)
            in {
                ProviderLifecycleEventKind.refund.value,
                ProviderLifecycleEventKind.chargeback.value,
            }
        ),
        start=Decimal(0),
    )
    if (
        event_kind_value
        in {
            ProviderLifecycleEventKind.refund.value,
            ProviderLifecycleEventKind.chargeback.value,
        }
        and not current_matches
    ):
        irreversible_total += amount
    if irreversible_total > original_amount:
        raise ValueError(
            "provider lifecycle cumulative debits exceed the original funding amount"
        )


def _required_text(value: str, *, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


__all__ = [
    "ResolvedProviderLifecycleContext",
    "resolve_provider_lifecycle_context_models",
]
