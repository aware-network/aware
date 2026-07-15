from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import NAMESPACE_URL, UUID, uuid5


EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY = "fake_external_capital"
WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME = "economy.wallet_funding.intent.prepared"
EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY = (
    "external_capital.create_wallet_funding_session"
)
EXTERNAL_CAPITAL_PROVIDER_CONNECTOR_REF = "economy.external_capital_provider"

_FAKE_EXTERNAL_CAPITAL_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://economy/external-capital/fake-provider/v1",
)


class ExternalCapitalProviderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExternalCapitalWalletFundingContext:
    """Typed committed Economy truth consumed by one provider actuator."""

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
    status: str
    capital_conversion_quote_id: UUID
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    target_amount: Decimal
    conversion_mode: str
    quote_source: str
    quote_captured_at: str
    quote_expires_at: str | None = None

    @property
    def provider_session_idempotency_key(self) -> str:
        return (
            f"{self.provider_key}:wallet-funding:"
            f"{self.transaction_intent_id}:{self.quote_hash}"
        )


@dataclass(frozen=True, slots=True)
class ExternalCapitalWalletFundingSessionReceipt:
    """Provider-neutral hosted continuation returned by the actuator."""

    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    provider_key: str
    provider_public_reference: str
    idempotency_key: str
    continuation_kind: str
    continuation_url: str
    continuation_expires_at: str | None = None

    def to_feedback_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "transaction_intent_id": self.transaction_intent_id,
            "transaction_intent_commit_id": self.transaction_intent_commit_id,
            "provider_key": self.provider_key,
            "provider_public_reference": self.provider_public_reference,
            "idempotency_key": self.idempotency_key,
            "continuation_kind": self.continuation_kind,
            "continuation_url": self.continuation_url,
        }
        if self.continuation_expires_at is not None:
            payload["continuation_expires_at"] = self.continuation_expires_at
        return payload


@dataclass(frozen=True, slots=True)
class ExternalCapitalProviderSensorEvidence:
    """Provider facts accepted by Economy's verified wallet funding sensor."""

    transaction_intent_id: UUID
    transaction_intent_commit_id: UUID
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    capital_conversion_quote_id: UUID
    quote_hash: str
    external_amount_minor: int
    external_currency: str
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
            "external_amount_minor": self.external_amount_minor,
            "external_currency": self.external_currency,
            "provider_public_reference": self.provider_public_reference,
            "provider_payload_hash": self.provider_payload_hash,
            "external_created_at": self.external_created_at,
        }


def wallet_funding_context_from_economy(
    value: Mapping[str, object] | object,
) -> ExternalCapitalWalletFundingContext:
    context = ExternalCapitalWalletFundingContext(
        transaction_intent_id=_uuid_value(value, "transaction_intent_id"),
        transaction_intent_commit_id=_uuid_value(
            value,
            "transaction_intent_commit_id",
        ),
        funding_intent_key=_text_value(value, "funding_intent_key"),
        idempotency_key=_text_value(value, "idempotency_key"),
        provider_key=_text_value(value, "provider_key").casefold(),
        provider_config_id=_uuid_value(value, "provider_config_id"),
        provider_route_id=_uuid_value(value, "provider_route_id"),
        provider_finance_entity_id=_uuid_value(
            value,
            "provider_finance_entity_id",
        ),
        recipient_finance_entity_id=_uuid_value(
            value,
            "recipient_finance_entity_id",
        ),
        recipient_wallet_id=_uuid_value(value, "recipient_wallet_id"),
        recipient_wallet_public_id=_uuid_value(
            value,
            "recipient_wallet_public_id",
        ),
        coin_id=_uuid_value(value, "coin_id"),
        amount=_decimal_value(value, "amount"),
        status=_text_value(value, "status").casefold(),
        capital_conversion_quote_id=_uuid_value(
            value,
            "capital_conversion_quote_id",
        ),
        quote_hash=_sha256_hex_value(value, "quote_hash"),
        external_amount_minor=_positive_int_value(
            value,
            "external_amount_minor",
        ),
        external_currency=_currency_value(value, "external_currency"),
        target_amount=_decimal_value(value, "target_amount"),
        conversion_mode=_text_value(value, "conversion_mode"),
        quote_source=_text_value(value, "quote_source"),
        quote_captured_at=_text_value(value, "quote_captured_at"),
        quote_expires_at=_optional_text_value(value, "quote_expires_at"),
    )
    if context.status not in {"created", "pending"}:
        raise ExternalCapitalProviderError(
            "wallet funding provider context requires an unconfirmed intent"
        )
    if context.amount != context.target_amount:
        raise ExternalCapitalProviderError(
            "wallet funding provider context target amount mismatch"
        )
    if context.conversion_mode != "direct_denomination":
        raise ExternalCapitalProviderError(
            "wallet funding provider context supports direct_denomination only"
        )
    if context.quote_source != "external_capital_provider_route":
        raise ExternalCapitalProviderError(
            "wallet funding provider context quote source mismatch"
        )
    return context


def create_fake_wallet_funding_session(
    context: ExternalCapitalWalletFundingContext,
) -> ExternalCapitalWalletFundingSessionReceipt:
    if context.provider_key != EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY:
        raise ExternalCapitalProviderError(
            "fake external-capital provider requires "
            f"provider_key={EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY}"
        )
    session_id = uuid5(
        _FAKE_EXTERNAL_CAPITAL_NAMESPACE,
        f"{context.transaction_intent_id}:{context.quote_hash}",
    )
    return ExternalCapitalWalletFundingSessionReceipt(
        transaction_intent_id=context.transaction_intent_id,
        transaction_intent_commit_id=context.transaction_intent_commit_id,
        provider_key=context.provider_key,
        provider_public_reference=f"fake_session_{session_id.hex}",
        idempotency_key=context.provider_session_idempotency_key,
        continuation_kind="open_external_url",
        continuation_url=f"https://provider.example/fund/{session_id}",
        continuation_expires_at=context.quote_expires_at,
    )


def fake_wallet_funding_sensor_evidence(
    receipt: ExternalCapitalWalletFundingSessionReceipt,
    *,
    context: ExternalCapitalWalletFundingContext,
    external_created_at: str,
) -> ExternalCapitalProviderSensorEvidence:
    if receipt.transaction_intent_id != context.transaction_intent_id:
        raise ExternalCapitalProviderError(
            "fake provider receipt TransactionIntent mismatch"
        )
    provider_event_id = f"fake_event_{receipt.provider_public_reference}"
    payload = {
        "provider_event_id": provider_event_id,
        "provider_public_reference": receipt.provider_public_reference,
        "transaction_intent_id": str(context.transaction_intent_id),
        "transaction_intent_commit_id": str(context.transaction_intent_commit_id),
        "capital_conversion_quote_id": str(context.capital_conversion_quote_id),
        "quote_hash": context.quote_hash,
        "external_amount_minor": context.external_amount_minor,
        "external_currency": context.external_currency,
        "external_created_at": external_created_at,
    }
    payload_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ExternalCapitalProviderSensorEvidence(
        transaction_intent_id=context.transaction_intent_id,
        transaction_intent_commit_id=context.transaction_intent_commit_id,
        provider_key=context.provider_key,
        provider_event_id=provider_event_id,
        idempotency_key=f"fake:event:{provider_event_id}",
        capital_conversion_quote_id=context.capital_conversion_quote_id,
        quote_hash=context.quote_hash,
        external_amount_minor=context.external_amount_minor,
        external_currency=context.external_currency,
        provider_public_reference=receipt.provider_public_reference,
        provider_payload_hash=f"sha256:{payload_hash}",
        external_created_at=external_created_at,
    )


def _raw_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> object | None:
    if isinstance(value, Mapping):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _text_value(value: Mapping[str, object] | object, field_name: str) -> str:
    text = str(_raw_value(value, field_name) or "").strip()
    if not text:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires {field_name}"
        )
    return text


def _optional_text_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> str | None:
    text = str(_raw_value(value, field_name) or "").strip()
    return text or None


def _uuid_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> UUID:
    try:
        return UUID(_text_value(value, field_name))
    except ValueError as exc:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires UUID {field_name}"
        ) from exc


def _decimal_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> Decimal:
    raw = _raw_value(value, field_name)
    if isinstance(raw, bool) or isinstance(raw, float):
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires exact decimal {field_name}"
        )
    try:
        parsed = Decimal(str(raw))
    except InvalidOperation as exc:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires decimal {field_name}"
        ) from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires positive {field_name}"
        )
    return parsed


def _positive_int_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> int:
    raw = _raw_value(value, field_name)
    if isinstance(raw, bool):
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires integer {field_name}"
        )
    try:
        parsed = int(str(raw))
    except (TypeError, ValueError) as exc:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires integer {field_name}"
        ) from exc
    if parsed <= 0:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires positive {field_name}"
        )
    return parsed


def _currency_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> str:
    currency = _text_value(value, field_name).upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires ISO currency {field_name}"
        )
    return currency


def _sha256_hex_value(
    value: Mapping[str, object] | object,
    field_name: str,
) -> str:
    digest = _text_value(value, field_name).lower()
    if len(digest) != 64:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires SHA-256 {field_name}"
        )
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ExternalCapitalProviderError(
            f"wallet funding provider context requires SHA-256 {field_name}"
        ) from exc
    return digest


__all__ = [
    "create_fake_wallet_funding_session",
    "EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY",
    "EXTERNAL_CAPITAL_PROVIDER_CONNECTOR_REF",
    "EXTERNAL_CAPITAL_WALLET_FUNDING_ACTION_KEY",
    "ExternalCapitalProviderError",
    "ExternalCapitalProviderSensorEvidence",
    "ExternalCapitalWalletFundingContext",
    "ExternalCapitalWalletFundingSessionReceipt",
    "fake_wallet_funding_sensor_evidence",
    "wallet_funding_context_from_economy",
    "WALLET_FUNDING_INTENT_PREPARED_EVENT_NAME",
]
