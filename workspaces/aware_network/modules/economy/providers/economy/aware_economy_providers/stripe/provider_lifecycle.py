from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

from aware_economy_providers.stripe.stripe_verifier import verify_and_construct_event

STRIPE_PROVIDER_KEY = "stripe"

SUPPORTED_PROVIDER_LIFECYCLE_EVENT_TYPES: tuple[str, ...] = (
    "charge.dispute.closed",
    "charge.dispute.created",
    "refund.created",
    "refund.updated",
)


class StripeProviderLifecycleError(ValueError):
    pass


class StripeProviderLifecycleIgnored(StripeProviderLifecycleError):
    def __init__(
        self,
        message: str,
        *,
        provider_event_id: str,
        provider_lifecycle_object_id: str,
    ) -> None:
        super().__init__(message)
        self.provider_event_id = provider_event_id
        self.provider_lifecycle_object_id = provider_lifecycle_object_id


@dataclass(frozen=True, slots=True)
class StripeProviderLifecycleEvidence:
    provider_event_id: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    provider_payment_reference: str
    external_amount_minor: int
    external_currency: str
    event_kind: str
    provider_payload_hash: str
    external_created_at: str
    metadata_json: dict[str, object]
    provider_key: str = STRIPE_PROVIDER_KEY

    def to_economy_record_kwargs(self) -> dict[str, object]:
        return {
            "provider_key": self.provider_key,
            "provider_event_id": self.provider_event_id,
            "provider_lifecycle_object_id": self.provider_lifecycle_object_id,
            "provider_lifecycle_effect_key": self.provider_lifecycle_effect_key,
            "provider_payment_reference": self.provider_payment_reference,
            "external_amount_minor": self.external_amount_minor,
            "external_currency": self.external_currency,
            "event_kind": self.event_kind,
            "provider_payload_hash": self.provider_payload_hash,
            "external_created_at": self.external_created_at,
            "metadata_json": dict(self.metadata_json),
        }


def verified_provider_lifecycle_evidence_from_webhook(
    *,
    raw_body: bytes,
    headers: Mapping[str, str],
    signing_secret: str,
    tolerance_seconds: int | None = 300,
) -> StripeProviderLifecycleEvidence:
    event = verify_and_construct_event(
        raw_body=raw_body,
        headers=dict(headers),
        signing_secret=signing_secret,
        tolerance_seconds=tolerance_seconds,
    )
    return provider_lifecycle_evidence_from_event(
        event,
        provider_payload_hash=_payload_hash(raw_body),
    )


def provider_lifecycle_evidence_from_event(
    event: Mapping[str, Any],
    *,
    provider_payload_hash: str | None = None,
) -> StripeProviderLifecycleEvidence:
    event_type = _require_non_empty_text(event.get("type"), "event.type")
    if event_type not in SUPPORTED_PROVIDER_LIFECYCLE_EVENT_TYPES:
        raise StripeProviderLifecycleError(f"Unsupported Stripe provider lifecycle event type: {event_type}")
    event_id = _require_non_empty_text(event.get("id"), "event.id")
    stripe_object = _stripe_object_from_event(event)
    provider_lifecycle_object_id = _require_non_empty_text(
        stripe_object.get("id"),
        "object.id",
    )
    object_type = _require_non_empty_text(stripe_object.get("object"), "object.object")
    _require_expected_object_type(event_type=event_type, object_type=object_type)

    event_kind = _event_kind(
        event_type=event_type,
        stripe_object=stripe_object,
        provider_event_id=event_id,
        provider_lifecycle_object_id=provider_lifecycle_object_id,
    )
    provider_payment_reference = _provider_payment_reference(stripe_object)
    external_amount_minor = _positive_int(stripe_object.get("amount"), "amount")
    external_currency = _require_currency(stripe_object.get("currency")).upper()
    stripe_status = _optional_text(stripe_object.get("status"))

    return StripeProviderLifecycleEvidence(
        provider_event_id=event_id,
        provider_lifecycle_object_id=provider_lifecycle_object_id,
        provider_lifecycle_effect_key=event_kind,
        provider_payment_reference=provider_payment_reference,
        external_amount_minor=external_amount_minor,
        external_currency=external_currency,
        event_kind=event_kind,
        provider_payload_hash=provider_payload_hash or _event_hash(event),
        external_created_at=_external_created_at(event, stripe_object),
        metadata_json={
            "stripe_event_type": event_type,
            "stripe_event_id": event_id,
            "stripe_livemode": bool(event.get("livemode", False)),
            "stripe_object_type": object_type,
            "stripe_object_id": provider_lifecycle_object_id,
            "stripe_payment_intent_id": provider_payment_reference,
            "stripe_status": stripe_status,
            "stripe_external_amount_minor": external_amount_minor,
            "stripe_external_currency": external_currency.lower(),
        },
    )


def _event_kind(
    *,
    event_type: str,
    stripe_object: Mapping[str, Any],
    provider_event_id: str,
    provider_lifecycle_object_id: str,
) -> str:
    if event_type in {"refund.created", "refund.updated"}:
        status = _require_non_empty_text(stripe_object.get("status"), "refund.status")
        if status != "succeeded":
            raise StripeProviderLifecycleIgnored(
                f"Stripe refund has no terminal wallet effect: {status}",
                provider_event_id=provider_event_id,
                provider_lifecycle_object_id=provider_lifecycle_object_id,
            )
        return "refund"
    if event_type == "charge.dispute.created":
        return "dispute"
    status = _require_non_empty_text(stripe_object.get("status"), "dispute.status")
    if status in {"won", "warning_closed"}:
        return "dispute_release"
    if status == "lost":
        return "chargeback"
    raise StripeProviderLifecycleError(f"Unsupported Stripe closed dispute status: {status}")


def _require_expected_object_type(*, event_type: str, object_type: str) -> None:
    expected = "refund" if event_type.startswith("refund.") else "dispute"
    if object_type != expected:
        raise StripeProviderLifecycleError(f"Stripe {event_type} object must be {expected}, got {object_type}")


def _stripe_object_from_event(event: Mapping[str, Any]) -> Mapping[str, Any]:
    data = event.get("data")
    if not isinstance(data, Mapping):
        raise StripeProviderLifecycleError("Stripe event missing data object")
    stripe_object = data.get("object")
    if not isinstance(stripe_object, Mapping):
        raise StripeProviderLifecycleError("Stripe event missing data.object")
    return stripe_object


def _provider_payment_reference(stripe_object: Mapping[str, Any]) -> str:
    payment_intent = stripe_object.get("payment_intent")
    if isinstance(payment_intent, Mapping):
        payment_intent = payment_intent.get("id")
    return _require_non_empty_text(payment_intent, "object.payment_intent")


def _positive_int(value: object, field_name: str) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise StripeProviderLifecycleError(f"Stripe provider lifecycle field must be an integer: {field_name}") from exc
    if parsed <= 0:
        raise StripeProviderLifecycleError(f"Stripe provider lifecycle field must be positive: {field_name}")
    return parsed


def _require_currency(value: object) -> str:
    currency = _require_non_empty_text(value, "currency").lower()
    if len(currency) != 3 or not currency.isalpha():
        raise StripeProviderLifecycleError(f"Invalid Stripe currency for provider lifecycle: {currency}")
    return currency


def _require_non_empty_text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise StripeProviderLifecycleError(f"Missing Stripe provider lifecycle field: {field_name}")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _payload_hash(raw_body: bytes) -> str:
    return "sha256:" + sha256(raw_body).hexdigest()


def _event_hash(event: Mapping[str, Any]) -> str:
    payload = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return _payload_hash(payload)


def _external_created_at(
    event: Mapping[str, Any],
    stripe_object: Mapping[str, Any],
) -> str:
    created = event.get("created", stripe_object.get("created"))
    try:
        created_ts = int(str(created))
    except (TypeError, ValueError) as exc:
        raise StripeProviderLifecycleError("Stripe created timestamp must be an integer") from exc
    return datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")
