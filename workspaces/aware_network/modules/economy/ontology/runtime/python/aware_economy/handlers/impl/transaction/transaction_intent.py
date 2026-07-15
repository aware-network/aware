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
from aware_economy_ontology.external_capital.external_capital_enums import ExternalCapitalConversionMode
from aware_economy_ontology.transaction.transaction_intent import TransactionIntent
from aware_economy_ontology.transaction.transaction_intent_external_expiration import (
    TransactionIntentExternalExpiration,
)

# Types
from aware_types import DecimalWire

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from datetime import UTC
from decimal import Decimal
from hashlib import sha256
import json

# Economy Ontology
from aware_economy_ontology.stable_ids import (
    stable_coin_id,
    stable_transaction_intent_id,
    stable_transaction_intent_external_expiration_id,
)
from aware_economy_ontology.transaction.capital_conversion_quote import (
    CapitalConversionQuote,
)
from aware_economy_ontology.transaction.transaction_intent_enums import (
    TransactionIntentStatus,
)

# Economy Runtime
from aware_economy.capital_amount import canonical_amount_text, positive_amount

# Orm
from aware_orm.session.current_session_ctx import current_session

# --- AWARE: USER_IMPORTS END


async def create(
    provider_config_id: UUID,
    recipient_finance_entity_id: UUID,
    recipient_wallet_id: UUID,
    recipient_wallet_public_id: UUID,
    funding_intent_key: str,
    coin_id: UUID,
    amount: Annotated[Decimal, DecimalWire()],
    provider_key: str,
    idempotency_key: str,
    provider_route_id: UUID,
    external_currency: str,
    external_minor_unit_exponent: int,
    conversion_mode: ExternalCapitalConversionMode,
    created_at: datetime,
    quote_expires_at: datetime | None = None,
    metadata_json: JsonObject | None = None,
) -> TransactionIntent:
    """
    Records an Aware-owned wallet funding intent and its accepted capital quote atomically.

    Receipt: TransactionIntent(status=created) with one immutable CapitalConversionQuote.
    """

    # --- AWARE: LOGIC START create
    funding_intent_key = funding_intent_key.strip().casefold()
    if not funding_intent_key:
        raise ValueError("transaction_intent.create requires funding_intent_key")
    provider_key = provider_key.strip().casefold()
    if not provider_key:
        raise ValueError("transaction_intent.create requires provider_key")
    idempotency_key = idempotency_key.strip()
    if not idempotency_key:
        raise ValueError("transaction_intent.create requires idempotency_key")
    if created_at.tzinfo is None or created_at.utcoffset() is None:
        raise ValueError("transaction_intent.create requires timezone-aware created_at")
    if quote_expires_at is not None:
        if quote_expires_at.tzinfo is None or quote_expires_at.utcoffset() is None:
            raise ValueError("transaction_intent.create requires timezone-aware quote_expires_at")
        if quote_expires_at <= created_at:
            raise ValueError("transaction_intent.create requires quote_expires_at after created_at")

    external_currency = external_currency.strip().upper()
    if len(external_currency) != 3 or not external_currency.isascii() or not external_currency.isalpha():
        raise ValueError("transaction_intent.create requires a three-letter ASCII external_currency")
    if external_minor_unit_exponent < 0 or external_minor_unit_exponent > 18:
        raise ValueError("transaction_intent.create requires external_minor_unit_exponent between 0 and 18")
    if conversion_mode != ExternalCapitalConversionMode.direct_denomination:
        raise ValueError("transaction_intent.create supports direct_denomination only")
    if coin_id != stable_coin_id(symbol=external_currency):
        raise ValueError(
            "transaction_intent.create direct denomination requires target Coin to match external_currency"
        )

    amount_decimal = positive_amount(amount, field_name="transaction intent amount")
    amount_text = canonical_amount_text(
        amount_decimal,
        field_name="transaction intent amount",
    )
    external_amount = amount_decimal * (Decimal(10) ** external_minor_unit_exponent)
    if external_amount != external_amount.to_integral_value():
        raise ValueError("transaction_intent.create amount exceeds external currency minor-unit precision")
    external_amount_minor = int(external_amount)

    intent_id = stable_transaction_intent_id(
        provider_config_id=provider_config_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        funding_intent_key=funding_intent_key,
    )
    quote_key = f"transaction-intent:{intent_id}:direct-denomination-v0"
    quote_payload = {
        "contract": "aware.economy.capital_conversion_quote.v0",
        "provider_config_id": str(provider_config_id),
        "provider_key": provider_key,
        "recipient_finance_entity_id": str(recipient_finance_entity_id),
        "recipient_wallet_id": str(recipient_wallet_id),
        "recipient_wallet_public_id": str(recipient_wallet_public_id),
        "funding_intent_key": funding_intent_key,
        "idempotency_key": idempotency_key,
        "provider_route_id": str(provider_route_id),
        "target_coin_id": str(coin_id),
        "target_amount": amount_text,
        "external_amount_minor": external_amount_minor,
        "external_currency": external_currency,
        "external_minor_unit_exponent": external_minor_unit_exponent,
        "conversion_mode": conversion_mode.value,
        "source": "external_capital_provider_route",
        "captured_at": created_at.isoformat(),
        "expires_at": (quote_expires_at.isoformat() if quote_expires_at is not None else None),
    }
    quote_hash = sha256(
        json.dumps(
            quote_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    session = current_session()
    if session is not None:
        for candidate in session.imap_all_objects():
            if not isinstance(candidate, TransactionIntent):
                continue
            if candidate.id == intent_id:
                continue
            if (
                candidate.provider_config_id == provider_config_id
                and candidate.recipient_finance_entity_id == recipient_finance_entity_id
                and candidate.idempotency_key == idempotency_key
            ):
                raise ValueError("transaction_intent.create idempotency_key is already bound to another funding intent")

        existing = session.imap_get(TransactionIntent, intent_id)
        if existing is not None:
            existing_quote = existing.capital_conversion_quote
            if existing_quote is None:
                raise ValueError("transaction_intent.create existing intent is missing its capital conversion quote")
            expected = {
                "coin_id": coin_id,
                "recipient_wallet_id": recipient_wallet_id,
                "recipient_wallet_public_id": recipient_wallet_public_id,
                "amount": amount_decimal,
                "provider_key": provider_key,
                "idempotency_key": idempotency_key,
                "created_at": created_at,
                "provider_route_id": provider_route_id,
                "quote_hash": quote_hash,
            }
            actual = {
                "coin_id": existing.coin_id,
                "recipient_wallet_id": existing.recipient_wallet_id,
                "recipient_wallet_public_id": existing.recipient_wallet_public_id,
                "amount": existing.amount,
                "provider_key": existing.provider_key,
                "idempotency_key": existing.idempotency_key,
                "created_at": existing.created_at,
                "provider_route_id": existing_quote.provider_route_id,
                "quote_hash": existing_quote.quote_hash,
            }
            if actual != expected:
                raise ValueError("transaction_intent.create cannot redefine an existing funding intent")
            return existing

    quote = await CapitalConversionQuote.build(
        provider_route_id=provider_route_id,
        target_coin_id=coin_id,
        quote_key=quote_key,
        quote_hash=quote_hash,
        external_amount_minor=external_amount_minor,
        external_currency=external_currency,
        target_amount=amount_decimal,
        conversion_mode=conversion_mode,
        source="external_capital_provider_route",
        captured_at=created_at,
        expires_at=quote_expires_at,
    )
    intent = TransactionIntent(
        id=intent_id,
        provider_config_id=provider_config_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        recipient_wallet_id=recipient_wallet_id,
        recipient_wallet_public_id=recipient_wallet_public_id,
        coin_id=coin_id,
        capital_conversion_quote_id=quote.id,
        amount=amount_decimal,
        funding_intent_key=funding_intent_key,
        provider_key=provider_key,
        idempotency_key=idempotency_key,
        created_at=created_at,
        updated_at=None,
        metadata_json=metadata_json if metadata_json is not None else JsonObject({}),
        status=TransactionIntentStatus.created,
    )
    intent.capital_conversion_quote = quote
    return intent
    # --- AWARE: LOGIC END create


async def mark_pending(transaction_intent: TransactionIntent, occurred_at: datetime) -> TransactionIntent:
    """
    Marks that the external-capital continuation was created.
    """

    # --- AWARE: LOGIC START mark_pending
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("transaction_intent.mark_pending requires timezone-aware occurred_at")
    if occurred_at < transaction_intent.created_at:
        raise ValueError("transaction_intent.mark_pending cannot predate created_at")
    if transaction_intent.status == TransactionIntentStatus.pending:
        return transaction_intent
    if transaction_intent.status != TransactionIntentStatus.created:
        raise ValueError(f"transaction_intent.mark_pending invalid status transition: {transaction_intent.status}")
    transaction_intent.status = TransactionIntentStatus.pending
    transaction_intent.updated_at = occurred_at
    return transaction_intent
    # --- AWARE: LOGIC END mark_pending


async def confirm(transaction_intent: TransactionIntent, occurred_at: datetime) -> TransactionIntent:
    """
    Confirms the intent after verified external-capital ingress.
    """

    # --- AWARE: LOGIC START confirm
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("transaction_intent.confirm requires timezone-aware occurred_at")
    if occurred_at < transaction_intent.created_at:
        raise ValueError("transaction_intent.confirm cannot predate created_at")
    if transaction_intent.status == TransactionIntentStatus.confirmed:
        return transaction_intent
    if transaction_intent.status not in {
        TransactionIntentStatus.created,
        TransactionIntentStatus.pending,
    }:
        raise ValueError(f"transaction_intent.confirm invalid status transition: {transaction_intent.status}")
    transaction_intent.status = TransactionIntentStatus.confirmed
    transaction_intent.updated_at = occurred_at
    return transaction_intent
    # --- AWARE: LOGIC END confirm


async def cancel(transaction_intent: TransactionIntent, occurred_at: datetime) -> TransactionIntent:
    """
    Cancels the intent after verified terminal no-credit evidence.
    """

    # --- AWARE: LOGIC START cancel
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("transaction_intent.cancel requires timezone-aware occurred_at")
    if occurred_at < transaction_intent.created_at:
        raise ValueError("transaction_intent.cancel cannot predate created_at")
    if transaction_intent.status == TransactionIntentStatus.canceled:
        return transaction_intent
    if transaction_intent.status not in {
        TransactionIntentStatus.created,
        TransactionIntentStatus.pending,
    }:
        raise ValueError(f"transaction_intent.cancel invalid status transition: {transaction_intent.status}")
    transaction_intent.status = TransactionIntentStatus.canceled
    transaction_intent.updated_at = occurred_at
    return transaction_intent
    # --- AWARE: LOGIC END cancel


async def cancel_from_external_evidence(
    transaction_intent: TransactionIntent,
    provider_config_id: UUID,
    capital_conversion_quote_id: UUID,
    provider_key: str,
    provider_event_id: str,
    idempotency_key: str,
    quote_hash: str,
    provider_public_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
) -> TransactionIntentExternalExpiration:
    """
    Records verified provider expiration evidence and cancels this intent atomically.

    Receipt: contained TransactionIntentExternalExpiration; no Transaction
    or Wallet application is created.
    """

    # --- AWARE: LOGIC START cancel_from_external_evidence
    provider_key = provider_key.strip().casefold()
    provider_event_id = provider_event_id.strip()
    idempotency_key = idempotency_key.strip()
    provider_public_reference = provider_public_reference.strip()
    quote_hash = quote_hash.strip().casefold()
    provider_payload_hash = provider_payload_hash.strip().casefold()
    required_text = {
        "provider_key": provider_key,
        "provider_event_id": provider_event_id,
        "idempotency_key": idempotency_key,
        "provider_public_reference": provider_public_reference,
    }
    for field_name, value in required_text.items():
        if not value:
            raise ValueError("transaction_intent.cancel_from_external_evidence requires " f"{field_name}")
    if len(quote_hash) != 64 or any(character not in "0123456789abcdef" for character in quote_hash):
        raise ValueError("transaction_intent.cancel_from_external_evidence requires a SHA-256 quote_hash")
    if not provider_payload_hash.startswith("sha256:"):
        raise ValueError("transaction_intent.cancel_from_external_evidence requires a sha256 provider_payload_hash")
    payload_digest = provider_payload_hash.removeprefix("sha256:")
    if len(payload_digest) != 64 or any(character not in "0123456789abcdef" for character in payload_digest):
        raise ValueError("transaction_intent.cancel_from_external_evidence requires a sha256 provider_payload_hash")
    if external_created_at.tzinfo is None or external_created_at.utcoffset() is None:
        raise ValueError("transaction_intent.cancel_from_external_evidence requires timezone-aware external_created_at")
    if external_created_at < transaction_intent.created_at:
        raise ValueError("transaction_intent.cancel_from_external_evidence cannot predate created_at")
    if transaction_intent.provider_config_id != provider_config_id:
        raise ValueError("transaction_intent.cancel_from_external_evidence provider config mismatch")
    if transaction_intent.provider_key != provider_key:
        raise ValueError("transaction_intent.cancel_from_external_evidence provider key mismatch")
    quote = transaction_intent.capital_conversion_quote
    if quote is None or quote.id != capital_conversion_quote_id:
        raise ValueError("transaction_intent.cancel_from_external_evidence capital quote mismatch")
    if quote.quote_hash != quote_hash:
        raise ValueError("transaction_intent.cancel_from_external_evidence quote hash mismatch")

    existing = next(
        (
            candidate
            for candidate in transaction_intent.external_expirations
            if candidate.provider_config_id == provider_config_id and candidate.provider_event_id == provider_event_id
        ),
        None,
    )
    if existing is not None:
        expected = {
            "capital_conversion_quote_id": capital_conversion_quote_id,
            "provider_key": provider_key,
            "idempotency_key": idempotency_key,
            "quote_hash": quote_hash,
            "provider_public_reference": provider_public_reference,
            "provider_payload_hash": provider_payload_hash,
            "external_created_at": external_created_at,
        }
        actual = {
            "capital_conversion_quote_id": existing.capital_conversion_quote_id,
            "provider_key": existing.provider_key,
            "idempotency_key": existing.idempotency_key,
            "quote_hash": existing.quote_hash,
            "provider_public_reference": existing.provider_public_reference,
            "provider_payload_hash": existing.provider_payload_hash,
            "external_created_at": existing.external_created_at,
        }
        if actual != expected:
            raise ValueError("transaction_intent.cancel_from_external_evidence replay mismatch")
        if transaction_intent.status != TransactionIntentStatus.canceled:
            raise ValueError("transaction_intent.cancel_from_external_evidence replay status mismatch")
        return existing

    if any(candidate.idempotency_key == idempotency_key for candidate in transaction_intent.external_expirations):
        raise ValueError("transaction_intent.cancel_from_external_evidence idempotency key is already bound")
    if transaction_intent.status not in {
        TransactionIntentStatus.created,
        TransactionIntentStatus.pending,
    }:
        raise ValueError(
            "transaction_intent.cancel_from_external_evidence invalid status transition: "
            f"{transaction_intent.status}"
        )

    expiration = TransactionIntentExternalExpiration(
        id=stable_transaction_intent_external_expiration_id(
            provider_config_id=provider_config_id,
            provider_event_id=provider_event_id,
        ),
        transaction_intent_id=transaction_intent.id,
        provider_config_id=provider_config_id,
        capital_conversion_quote_id=capital_conversion_quote_id,
        provider_key=provider_key,
        provider_event_id=provider_event_id,
        idempotency_key=idempotency_key,
        quote_hash=quote_hash,
        provider_public_reference=provider_public_reference,
        provider_payload_hash=provider_payload_hash,
        external_created_at=external_created_at,
        recorded_at=datetime.now(UTC),
    )
    expiration.capital_conversion_quote = quote
    transaction_intent.external_expirations.append(expiration)
    transaction_intent.status = TransactionIntentStatus.canceled
    transaction_intent.updated_at = external_created_at
    return expiration
    # --- AWARE: LOGIC END cancel_from_external_evidence
