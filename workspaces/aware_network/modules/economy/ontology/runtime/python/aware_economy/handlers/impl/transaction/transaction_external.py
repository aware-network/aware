from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.transaction.transaction_external import TransactionExternal

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from string import hexdigits

# Economy Ontology
from aware_economy_ontology.stable_ids import stable_transaction_external_id
from aware_economy_ontology.transaction.transaction_external_enums import (
    TransactionExternalStatus,
)

# Orm
from aware_orm.session.current_session_ctx import current_session

# --- AWARE: USER_IMPORTS END


async def record(
    transaction_id: UUID,
    transaction_intent_id: UUID,
    provider_config_id: UUID,
    capital_conversion_quote_id: UUID,
    provider_finance_entity_id: UUID,
    provider_key: str,
    provider_event_id: str,
    idempotency_key: str,
    quote_hash: str,
    external_amount_minor: int,
    external_currency: str,
    provider_public_reference: str,
    provider_payload_hash: str,
    external_created_at: datetime,
) -> TransactionExternal:
    """
    Records fully correlated external-capital provenance for one ingress transaction.

    Receipt: TransactionExternal(status=processed) linked to the Transaction.
    """

    # --- AWARE: LOGIC START record
    def _required_text(value: str, *, field_name: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError(f"transaction_external.record requires {field_name}")
        return normalized

    def _required_sha256_hex(value: str, *, field_name: str) -> str:
        normalized = _required_text(value, field_name=field_name).lower()
        if len(normalized) != 64 or any(char not in hexdigits for char in normalized):
            raise ValueError(f"transaction_external.record requires {field_name} as 64 hex characters")
        return normalized

    def _required_payload_hash(value: str) -> str:
        normalized = _required_text(
            value,
            field_name="provider_payload_hash",
        ).lower()
        prefix = "sha256:"
        if not normalized.startswith(prefix):
            raise ValueError("transaction_external.record requires provider_payload_hash with sha256: prefix")
        _required_sha256_hex(
            normalized[len(prefix) :],
            field_name="provider_payload_hash digest",
        )
        return normalized

    provider_key = _required_text(provider_key, field_name="provider_key").casefold()
    provider_event_id_norm = _required_text(
        provider_event_id,
        field_name="provider_event_id",
    )
    idempotency_key = _required_text(
        idempotency_key,
        field_name="idempotency_key",
    )
    quote_hash = _required_sha256_hex(quote_hash, field_name="quote_hash")
    if external_amount_minor <= 0:
        raise ValueError("transaction_external.record requires external_amount_minor > 0")
    external_currency = _required_text(
        external_currency,
        field_name="external_currency",
    ).upper()
    if len(external_currency) != 3 or not external_currency.isascii() or not external_currency.isalpha():
        raise ValueError("transaction_external.record requires three-letter external_currency")
    provider_public_reference = _required_text(
        provider_public_reference,
        field_name="provider_public_reference",
    )
    provider_payload_hash = _required_payload_hash(provider_payload_hash)
    if external_created_at.tzinfo is None or external_created_at.utcoffset() is None:
        raise ValueError("transaction_external.record requires timezone-aware external_created_at")
    external_id = stable_transaction_external_id(
        provider_config_id=provider_config_id,
        provider_event_id=provider_event_id_norm,
    )

    session = current_session()
    existing = session.imap_get(TransactionExternal, external_id) if session is not None else None
    if existing is not None:
        expected = (
            transaction_id,
            transaction_intent_id,
            provider_config_id,
            capital_conversion_quote_id,
            provider_finance_entity_id,
            provider_key,
            provider_event_id_norm,
            idempotency_key,
            quote_hash,
            external_amount_minor,
            external_currency,
            provider_public_reference,
            provider_payload_hash,
            external_created_at,
        )
        actual = (
            existing.transaction_id,
            existing.transaction_intent_id,
            existing.provider_config_id,
            existing.capital_conversion_quote_id,
            existing.provider_finance_entity_id,
            existing.provider_key,
            existing.provider_event_id,
            existing.idempotency_key,
            existing.quote_hash,
            existing.external_amount_minor,
            existing.external_currency,
            existing.provider_public_reference,
            existing.provider_payload_hash,
            existing.external_created_at,
        )
        if actual != expected:
            raise ValueError("transaction_external.record cannot redefine correlated external evidence")
        return existing

    return TransactionExternal(
        id=external_id,
        transaction_id=transaction_id,
        transaction_intent_id=transaction_intent_id,
        provider_config_id=provider_config_id,
        capital_conversion_quote_id=capital_conversion_quote_id,
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=provider_key,
        provider_event_id=provider_event_id_norm,
        idempotency_key=idempotency_key,
        quote_hash=quote_hash,
        external_amount_minor=external_amount_minor,
        external_currency=external_currency,
        provider_public_reference=provider_public_reference,
        provider_payload_hash=provider_payload_hash,
        external_created_at=external_created_at,
        status=TransactionExternalStatus.processed,
    )
    # --- AWARE: LOGIC END record
