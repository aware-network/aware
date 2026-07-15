from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from uuid import UUID

import pytest

from aware_economy_providers.stripe.wallet_funding_webhook_app import (
    StripeWalletFundingWebhookConfig,
    StripeWalletFundingWebhookRejected,
    dispatch_stripe_wallet_funding_webhook,
)


TRANSACTION_INTENT_ID = UUID("aaaaaaaa-0000-4000-8000-000000000001")
TRANSACTION_INTENT_COMMIT_ID = UUID("aaaaaaaa-0000-4000-8000-000000000009")
CAPITAL_CONVERSION_QUOTE_ID = UUID("aaaaaaaa-0000-4000-8000-000000000010")
QUOTE_HASH = "b" * 64
ACTOR_ID = UUID("aaaaaaaa-0000-4000-8000-000000000008")


class _RecordingEconomy:
    def __init__(self) -> None:
        self.wallet_funding_calls: list[dict[str, object]] = []
        self.wallet_funding_expiration_calls: list[dict[str, object]] = []
        self.provider_lifecycle_calls: list[dict[str, object]] = []

    async def record_verified_wallet_funding(self, **kwargs: object) -> object:
        self.wallet_funding_calls.append(dict(kwargs))
        return {"operation": "record_verified_wallet_funding", "status": "ok"}

    async def record_wallet_funding_expiration(self, **kwargs: object) -> object:
        self.wallet_funding_expiration_calls.append(dict(kwargs))
        return {"operation": "record_wallet_funding_expiration", "status": "ok"}

    async def record_provider_lifecycle_event(self, **kwargs: object) -> object:
        self.provider_lifecycle_calls.append(dict(kwargs))
        return {"operation": "record_provider_lifecycle_event", "status": "ok"}


def test_dispatch_signed_payment_intent_records_wallet_funding() -> None:
    economy = _RecordingEconomy()
    raw_body, headers = _signed_event(_wallet_funding_event())

    receipt = asyncio.run(
        dispatch_stripe_wallet_funding_webhook(
            raw_body=raw_body,
            headers=headers,
            config=StripeWalletFundingWebhookConfig(
                signing_secret="whsec_test",
                provider_identity_id=ACTOR_ID,
            ),
            economy=economy,
        )
    )

    assert receipt.operation == "record_verified_wallet_funding"
    assert receipt.provider_event_id == "evt_wallet_1"
    assert receipt.provider_public_reference == "pi_wallet_1"
    assert len(economy.wallet_funding_calls) == 1
    assert economy.wallet_funding_expiration_calls == []
    assert economy.provider_lifecycle_calls == []
    call = economy.wallet_funding_calls[0]
    assert set(call) == {
        "transaction_intent_id",
        "transaction_intent_commit_id",
        "provider_key",
        "provider_event_id",
        "idempotency_key",
        "capital_conversion_quote_id",
        "quote_hash",
        "external_amount_minor",
        "external_currency",
        "provider_public_reference",
        "provider_payload_hash",
        "external_created_at",
    }
    assert call["transaction_intent_id"] == TRANSACTION_INTENT_ID
    assert call["transaction_intent_commit_id"] == TRANSACTION_INTENT_COMMIT_ID
    assert call["capital_conversion_quote_id"] == CAPITAL_CONVERSION_QUOTE_ID
    assert call["quote_hash"] == QUOTE_HASH
    assert call["external_amount_minor"] == 2500
    assert call["external_currency"] == "USD"
    assert call["provider_key"] == "stripe"
    assert call["provider_event_id"] == "evt_wallet_1"
    assert call["idempotency_key"] == "stripe:event:evt_wallet_1"
    assert call["provider_public_reference"] == "pi_wallet_1"
    assert call["provider_payload_hash"] == "sha256:" + hashlib.sha256(raw_body).hexdigest()


def test_dispatch_signed_checkout_expiry_cancels_without_wallet_credit() -> None:
    economy = _RecordingEconomy()
    raw_body, headers = _signed_event(_wallet_funding_expired_event())

    receipt = asyncio.run(
        dispatch_stripe_wallet_funding_webhook(
            raw_body=raw_body,
            headers=headers,
            config=StripeWalletFundingWebhookConfig(
                signing_secret="whsec_test",
                provider_identity_id=ACTOR_ID,
            ),
            economy=economy,
        )
    )

    assert receipt.operation == "record_wallet_funding_expiration"
    assert receipt.provider_event_id == "evt_checkout_expired_1"
    assert receipt.provider_public_reference == "cs_test_expired_1"
    assert economy.wallet_funding_calls == []
    assert economy.provider_lifecycle_calls == []
    assert len(economy.wallet_funding_expiration_calls) == 1
    call = economy.wallet_funding_expiration_calls[0]
    assert set(call) == {
        "transaction_intent_id",
        "transaction_intent_commit_id",
        "provider_key",
        "provider_event_id",
        "idempotency_key",
        "capital_conversion_quote_id",
        "quote_hash",
        "provider_public_reference",
        "provider_payload_hash",
        "external_created_at",
    }
    assert call["transaction_intent_id"] == TRANSACTION_INTENT_ID
    assert call["transaction_intent_commit_id"] == TRANSACTION_INTENT_COMMIT_ID
    assert call["capital_conversion_quote_id"] == CAPITAL_CONVERSION_QUOTE_ID
    assert call["idempotency_key"] == "stripe:event:evt_checkout_expired_1"


def test_dispatch_signed_refund_records_provider_lifecycle() -> None:
    economy = _RecordingEconomy()
    raw_body, headers = _signed_event(_refund_event())

    receipt = asyncio.run(
        dispatch_stripe_wallet_funding_webhook(
            raw_body=raw_body,
            headers=headers,
            config=StripeWalletFundingWebhookConfig(
                signing_secret="whsec_test",
                provider_identity_id=ACTOR_ID,
            ),
            economy=economy,
        )
    )

    assert receipt.operation == "record_provider_lifecycle_event"
    assert receipt.provider_event_id == "evt_refund_1"
    assert receipt.provider_public_reference == "pi_wallet_1"
    assert economy.wallet_funding_calls == []
    assert economy.wallet_funding_expiration_calls == []
    assert len(economy.provider_lifecycle_calls) == 1
    call = economy.provider_lifecycle_calls[0]
    assert set(call) == {
        "provider_key",
        "provider_event_id",
        "provider_lifecycle_object_id",
        "provider_lifecycle_effect_key",
        "provider_payment_reference",
        "external_amount_minor",
        "external_currency",
        "event_kind",
        "provider_payload_hash",
        "external_created_at",
        "metadata_json",
    }
    assert call["provider_lifecycle_object_id"] == "re_wallet_1"
    assert call["provider_lifecycle_effect_key"] == "refund"
    assert call["provider_payment_reference"] == "pi_wallet_1"
    assert call["external_amount_minor"] == 2500
    assert call["external_currency"] == "USD"
    assert call["event_kind"] == "refund"
    assert call["provider_key"] == "stripe"


def test_dispatch_pending_refund_acknowledges_without_economy_mutation() -> None:
    economy = _RecordingEconomy()
    raw_body, headers = _signed_event(_refund_event(status="pending"))

    receipt = asyncio.run(
        dispatch_stripe_wallet_funding_webhook(
            raw_body=raw_body,
            headers=headers,
            config=StripeWalletFundingWebhookConfig(
                signing_secret="whsec_test",
                provider_identity_id=ACTOR_ID,
            ),
            economy=economy,
        )
    )

    assert receipt.status == "ignored"
    assert receipt.operation == "ignore_provider_lifecycle_event"
    assert receipt.provider_event_id == "evt_refund_1"
    assert receipt.provider_public_reference == "re_wallet_1"
    assert economy.wallet_funding_calls == []
    assert economy.wallet_funding_expiration_calls == []
    assert economy.provider_lifecycle_calls == []


def test_dispatch_rejects_unsigned_payload_without_economy_call() -> None:
    economy = _RecordingEconomy()
    raw_body = json.dumps(_wallet_funding_event(), sort_keys=True).encode("utf-8")

    with pytest.raises(StripeWalletFundingWebhookRejected, match="Stripe-Signature"):
        asyncio.run(
            dispatch_stripe_wallet_funding_webhook(
                raw_body=raw_body,
                headers={},
                config=StripeWalletFundingWebhookConfig(
                    signing_secret="whsec_test",
                    provider_identity_id=ACTOR_ID,
                ),
                economy=economy,
            )
        )

    assert economy.wallet_funding_calls == []
    assert economy.wallet_funding_expiration_calls == []
    assert economy.provider_lifecycle_calls == []


def _signed_event(event: dict[str, object]) -> tuple[bytes, dict[str, str]]:
    raw_body = json.dumps(event, sort_keys=True).encode("utf-8")
    timestamp = int(time.time())
    signature = hmac.new(
        b"whsec_test",
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    ).hexdigest()
    return raw_body, {"stripe-signature": f"t={timestamp},v1={signature}"}


def _wallet_metadata() -> dict[str, str]:
    return {
        "aware_provider_key": "stripe",
        "aware_transaction_intent_id": str(TRANSACTION_INTENT_ID),
        "aware_transaction_intent_commit_id": str(TRANSACTION_INTENT_COMMIT_ID),
        "aware_capital_conversion_quote_id": str(CAPITAL_CONVERSION_QUOTE_ID),
        "aware_quote_hash": QUOTE_HASH,
        "aware_external_amount_minor": "2500",
        "aware_external_currency": "usd",
    }


def _wallet_funding_event() -> dict[str, object]:
    return {
        "id": "evt_wallet_1",
        "object": "event",
        "type": "payment_intent.succeeded",
        "created": 1_720_000_000,
        "livemode": False,
        "data": {
            "object": {
                "id": "pi_wallet_1",
                "object": "payment_intent",
                "status": "succeeded",
                "amount": 2500,
                "amount_received": 2500,
                "currency": "usd",
                "metadata": _wallet_metadata(),
            }
        },
    }


def _wallet_funding_expired_event() -> dict[str, object]:
    return {
        "id": "evt_checkout_expired_1",
        "object": "event",
        "type": "checkout.session.expired",
        "created": 1_720_000_100,
        "livemode": False,
        "data": {
            "object": {
                "id": "cs_test_expired_1",
                "object": "checkout.session",
                "status": "expired",
                "metadata": _wallet_metadata(),
            }
        },
    }


def _refund_event(*, status: str = "succeeded") -> dict[str, object]:
    return {
        "id": "evt_refund_1",
        "object": "event",
        "type": "refund.created",
        "created": 1_720_000_000,
        "livemode": False,
        "data": {
            "object": {
                "id": "re_wallet_1",
                "object": "refund",
                "payment_intent": "pi_wallet_1",
                "amount": 2500,
                "currency": "usd",
                "status": status,
                "metadata": {"aware_wallet_id": "ignored-provider-metadata"},
            }
        },
    }
