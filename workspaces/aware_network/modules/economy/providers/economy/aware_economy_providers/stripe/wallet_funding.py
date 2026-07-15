from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from aware_economy_providers.external_capital import (
    ExternalCapitalProviderSensorEvidence,
    ExternalCapitalWalletFundingContext,
)
from aware_economy_providers.stripe.stripe_verifier import (
    verify_and_construct_event,
)


STRIPE_PROVIDER_KEY = "stripe"
WALLET_FUNDING_SUCCEEDED_EVENT_TYPE = "payment_intent.succeeded"
WALLET_FUNDING_EXPIRED_EVENT_TYPE = "checkout.session.expired"

REQUIRED_WALLET_FUNDING_METADATA_KEYS: tuple[str, ...] = (
    "aware_provider_key",
    "aware_transaction_intent_id",
    "aware_transaction_intent_commit_id",
    "aware_capital_conversion_quote_id",
    "aware_quote_hash",
    "aware_external_amount_minor",
    "aware_external_currency",
)

FORBIDDEN_WALLET_FUNDING_METADATA_FRAGMENTS: tuple[str, ...] = (
    "service_contract",
    "subscription",
    "entitlement",
    "membership",
)


class StripeWalletFundingError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StripeWalletFundingCheckoutSessionRequest:
    amount: int
    currency: str
    metadata: dict[str, str]
    idempotency_key: str
    success_url: str
    cancel_url: str
    product_name: str = "Aware wallet funding"
    description: str | None = None

    def to_stripe_form_fields(self) -> dict[str, str]:
        fields = {
            "mode": "payment",
            "success_url": self.success_url,
            "cancel_url": self.cancel_url,
            "line_items[0][price_data][currency]": self.currency,
            "line_items[0][price_data][unit_amount]": str(self.amount),
            "line_items[0][price_data][product_data][name]": self.product_name,
            "line_items[0][quantity]": "1",
        }
        if self.description is not None:
            fields["payment_intent_data[description]"] = self.description
        for key, value in sorted(self.metadata.items()):
            fields[f"metadata[{key}]"] = value
            fields[f"payment_intent_data[metadata][{key}]"] = value
        return fields

    def to_stripe_headers(self) -> dict[str, str]:
        return {"Idempotency-Key": self.idempotency_key}


StripeWalletFundingEvidence = ExternalCapitalProviderSensorEvidence


@dataclass(frozen=True, slots=True)
class StripeWalletFundingExpirationEvidence:
    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    capital_conversion_quote_id: UUID
    quote_hash: str
    provider_public_reference: str
    provider_payload_hash: str
    external_created_at: str

    def to_economy_record_kwargs(self) -> dict[str, object]:
        return {
            "transaction_intent_id": self.transaction_intent_id,
            "transaction_intent_commit_id": self.transaction_intent_commit_id,
            "provider_key": self.provider_key,
            "provider_event_id": self.provider_event_id,
            "idempotency_key": self.idempotency_key,
            "capital_conversion_quote_id": self.capital_conversion_quote_id,
            "quote_hash": self.quote_hash,
            "provider_public_reference": self.provider_public_reference,
            "provider_payload_hash": self.provider_payload_hash,
            "external_created_at": self.external_created_at,
        }


def build_wallet_funding_checkout_session_request(
    *,
    context: ExternalCapitalWalletFundingContext,
    success_url: str,
    cancel_url: str,
    product_name: str = "Aware wallet funding",
    description: str | None = None,
) -> StripeWalletFundingCheckoutSessionRequest:
    if context.provider_key != STRIPE_PROVIDER_KEY:
        raise StripeWalletFundingError(
            "Stripe wallet funding requires provider_key=stripe"
        )
    if context.status not in {"created", "pending"}:
        raise StripeWalletFundingError(
            "Stripe wallet funding requires an unconfirmed intent"
        )
    success_url = _require_https_url(success_url, field_name="success_url")
    cancel_url = _require_https_url(cancel_url, field_name="cancel_url")
    product_name = _require_text(product_name, field_name="product_name")
    metadata = {
        "aware_provider_key": STRIPE_PROVIDER_KEY,
        "aware_transaction_intent_id": str(context.transaction_intent_id),
        "aware_transaction_intent_commit_id": str(context.transaction_intent_commit_id),
        "aware_capital_conversion_quote_id": str(context.capital_conversion_quote_id),
        "aware_quote_hash": context.quote_hash,
        "aware_external_amount_minor": str(context.external_amount_minor),
        "aware_external_currency": context.external_currency.lower(),
    }
    _require_wallet_funding_metadata(metadata)
    return StripeWalletFundingCheckoutSessionRequest(
        amount=context.external_amount_minor,
        currency=context.external_currency.lower(),
        metadata=metadata,
        idempotency_key=context.provider_session_idempotency_key,
        success_url=success_url,
        cancel_url=cancel_url,
        product_name=product_name,
        description=description,
    )


def verified_wallet_funding_evidence_from_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, str],
    signing_secret: str,
    tolerance_seconds: int | None = 300,
) -> StripeWalletFundingEvidence:
    event = verify_and_construct_event(
        raw_body=raw_body,
        headers=dict(headers),
        signing_secret=signing_secret,
        tolerance_seconds=tolerance_seconds,
    )
    return wallet_funding_evidence_from_event(
        event,
        provider_payload_hash=_payload_hash(raw_body),
    )


def verified_wallet_funding_expiration_evidence_from_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, str],
    signing_secret: str,
    tolerance_seconds: int | None = 300,
) -> StripeWalletFundingExpirationEvidence:
    event = verify_and_construct_event(
        raw_body=raw_body,
        headers=dict(headers),
        signing_secret=signing_secret,
        tolerance_seconds=tolerance_seconds,
    )
    return wallet_funding_expiration_evidence_from_event(
        event,
        provider_payload_hash=_payload_hash(raw_body),
    )


def wallet_funding_evidence_from_event(
    event: Mapping[str, Any],
    *,
    provider_payload_hash: str | None = None,
) -> StripeWalletFundingEvidence:
    event_type = _require_text(event.get("type"), field_name="event.type")
    if event_type != WALLET_FUNDING_SUCCEEDED_EVENT_TYPE:
        raise StripeWalletFundingError(
            f"Unsupported Stripe wallet funding event type: {event_type}"
        )
    event_id = _require_text(event.get("id"), field_name="event.id")
    payment_intent = _event_object(event, expected_object="payment_intent")
    payment_intent_id = _require_text(
        payment_intent.get("id"),
        field_name="payment_intent.id",
    )
    status = _require_text(
        payment_intent.get("status"),
        field_name="payment_intent.status",
    )
    if status != "succeeded":
        raise StripeWalletFundingError(
            f"Stripe PaymentIntent is not succeeded: {status}"
        )
    metadata = _object_metadata(payment_intent)
    _require_wallet_funding_metadata(metadata)
    amount_minor = _positive_int(
        payment_intent.get("amount_received", payment_intent.get("amount")),
        field_name="payment_intent.amount_received",
    )
    metadata_amount_minor = _positive_int(
        metadata["aware_external_amount_minor"],
        field_name="aware_external_amount_minor",
    )
    if amount_minor != metadata_amount_minor:
        raise StripeWalletFundingError(
            "Stripe amount does not match committed capital quote metadata"
        )
    currency = _currency(
        payment_intent.get("currency"),
        field_name="payment_intent.currency",
    )
    metadata_currency = _currency(
        metadata["aware_external_currency"],
        field_name="aware_external_currency",
    )
    if currency != metadata_currency:
        raise StripeWalletFundingError(
            "Stripe currency does not match committed capital quote metadata"
        )
    return ExternalCapitalProviderSensorEvidence(
        transaction_intent_id=_metadata_uuid(
            metadata,
            "aware_transaction_intent_id",
        ),
        transaction_intent_commit_id=_metadata_uuid(
            metadata,
            "aware_transaction_intent_commit_id",
        ),
        provider_key=STRIPE_PROVIDER_KEY,
        provider_event_id=event_id,
        idempotency_key=f"stripe:event:{event_id}",
        capital_conversion_quote_id=_metadata_uuid(
            metadata,
            "aware_capital_conversion_quote_id",
        ),
        quote_hash=_sha256_hex(
            metadata["aware_quote_hash"],
            field_name="aware_quote_hash",
        ),
        external_amount_minor=amount_minor,
        external_currency=currency.upper(),
        provider_public_reference=payment_intent_id,
        provider_payload_hash=provider_payload_hash or _event_hash(event),
        external_created_at=_external_created_at(event, payment_intent),
    )


def wallet_funding_expiration_evidence_from_event(
    event: Mapping[str, Any],
    *,
    provider_payload_hash: str | None = None,
) -> StripeWalletFundingExpirationEvidence:
    event_type = _require_text(event.get("type"), field_name="event.type")
    if event_type != WALLET_FUNDING_EXPIRED_EVENT_TYPE:
        raise StripeWalletFundingError(
            f"Unsupported Stripe wallet funding expiry event type: {event_type}"
        )
    event_id = _require_text(event.get("id"), field_name="event.id")
    checkout_session = _event_object(
        event,
        expected_object="checkout.session",
    )
    session_id = _require_text(
        checkout_session.get("id"),
        field_name="checkout_session.id",
    )
    metadata = _object_metadata(checkout_session)
    _require_wallet_funding_metadata(metadata)
    return StripeWalletFundingExpirationEvidence(
        transaction_intent_id=_metadata_uuid(
            metadata,
            "aware_transaction_intent_id",
        ),
        transaction_intent_commit_id=_metadata_uuid(
            metadata,
            "aware_transaction_intent_commit_id",
        ),
        provider_key=STRIPE_PROVIDER_KEY,
        provider_event_id=event_id,
        idempotency_key=f"stripe:event:{event_id}",
        capital_conversion_quote_id=_metadata_uuid(
            metadata,
            "aware_capital_conversion_quote_id",
        ),
        quote_hash=_sha256_hex(
            metadata["aware_quote_hash"],
            field_name="aware_quote_hash",
        ),
        provider_public_reference=session_id,
        provider_payload_hash=provider_payload_hash or _event_hash(event),
        external_created_at=_external_created_at(event, checkout_session),
    )


def _event_object(
    event: Mapping[str, Any],
    *,
    expected_object: str,
) -> Mapping[str, Any]:
    data = event.get("data")
    if not isinstance(data, Mapping):
        raise StripeWalletFundingError("Stripe event missing data object")
    event_object = data.get("object")
    if not isinstance(event_object, Mapping):
        raise StripeWalletFundingError("Stripe event missing data.object")
    object_type = event_object.get("object")
    if object_type not in (None, expected_object):
        raise StripeWalletFundingError(
            f"Stripe event object is not {expected_object}: {object_type}"
        )
    return event_object


def _object_metadata(value: Mapping[str, Any]) -> dict[str, str]:
    raw_metadata = value.get("metadata")
    if not isinstance(raw_metadata, Mapping):
        raise StripeWalletFundingError("Stripe object missing metadata")
    return {str(key): str(item) for key, item in raw_metadata.items()}


def _require_wallet_funding_metadata(metadata: Mapping[str, str]) -> None:
    _reject_forbidden_metadata_keys(metadata)
    missing = [
        key
        for key in REQUIRED_WALLET_FUNDING_METADATA_KEYS
        if not str(metadata.get(key) or "").strip()
    ]
    if missing:
        raise StripeWalletFundingError(
            "Missing Stripe wallet funding metadata keys: " + ", ".join(missing)
        )
    if metadata["aware_provider_key"].strip().casefold() != STRIPE_PROVIDER_KEY:
        raise StripeWalletFundingError(
            "Stripe wallet funding metadata provider key mismatch"
        )
    _sha256_hex(metadata["aware_quote_hash"], field_name="aware_quote_hash")


def _reject_forbidden_metadata_keys(metadata: Mapping[str, object]) -> None:
    for key in metadata:
        normalized_key = str(key).casefold()
        if any(
            fragment in normalized_key
            for fragment in FORBIDDEN_WALLET_FUNDING_METADATA_FRAGMENTS
        ):
            raise StripeWalletFundingError(
                f"Forbidden Stripe wallet funding metadata key: {key}"
            )


def _metadata_uuid(metadata: Mapping[str, str], key: str) -> UUID:
    try:
        return UUID(_require_text(metadata.get(key), field_name=key))
    except ValueError as exc:
        raise StripeWalletFundingError(
            f"Invalid UUID in Stripe wallet funding metadata: {key}"
        ) from exc


def _require_text(value: object, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise StripeWalletFundingError(
            f"Missing Stripe wallet funding field: {field_name}"
        )
    return text


def _positive_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool):
        raise StripeWalletFundingError(f"{field_name} must be a positive integer")
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise StripeWalletFundingError(
            f"{field_name} must be a positive integer"
        ) from exc
    if parsed <= 0:
        raise StripeWalletFundingError(f"{field_name} must be a positive integer")
    return parsed


def _currency(value: object, *, field_name: str) -> str:
    currency = _require_text(value, field_name=field_name).lower()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise StripeWalletFundingError(f"Invalid Stripe currency: {currency}")
    return currency


def _sha256_hex(value: object, *, field_name: str) -> str:
    digest = _require_text(value, field_name=field_name).lower()
    if len(digest) != 64:
        raise StripeWalletFundingError(f"{field_name} must be SHA-256 hex")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise StripeWalletFundingError(f"{field_name} must be SHA-256 hex") from exc
    return digest


def _require_https_url(value: object, *, field_name: str) -> str:
    url = _require_text(value, field_name=field_name)
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise StripeWalletFundingError(f"{field_name} must be an HTTPS URL")
    return url


def _payload_hash(raw_body: bytes) -> str:
    return "sha256:" + sha256(raw_body).hexdigest()


def _event_hash(event: Mapping[str, Any]) -> str:
    payload = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return _payload_hash(payload)


def _external_created_at(
    event: Mapping[str, Any],
    event_object: Mapping[str, Any],
) -> str:
    created = event.get("created", event_object.get("created"))
    if created is None:
        raise StripeWalletFundingError("Stripe event created timestamp is required")
    try:
        created_ts = int(str(created))
    except (TypeError, ValueError) as exc:
        raise StripeWalletFundingError(
            "Stripe event created timestamp must be an integer"
        ) from exc
    return datetime.fromtimestamp(created_ts, tz=UTC).isoformat()


__all__ = [
    "build_wallet_funding_checkout_session_request",
    "REQUIRED_WALLET_FUNDING_METADATA_KEYS",
    "STRIPE_PROVIDER_KEY",
    "StripeWalletFundingCheckoutSessionRequest",
    "StripeWalletFundingError",
    "StripeWalletFundingEvidence",
    "StripeWalletFundingExpirationEvidence",
    "verified_wallet_funding_evidence_from_webhook",
    "wallet_funding_evidence_from_event",
    "wallet_funding_expiration_evidence_from_event",
    "WALLET_FUNDING_EXPIRED_EVENT_TYPE",
    "WALLET_FUNDING_SUCCEEDED_EVENT_TYPE",
]
