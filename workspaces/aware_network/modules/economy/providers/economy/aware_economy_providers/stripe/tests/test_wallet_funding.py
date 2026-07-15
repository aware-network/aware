from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import hmac
import json
import time
from uuid import UUID

import pytest

from aware_economy_providers.external_capital import (
    wallet_funding_context_from_economy,
)
from aware_economy_providers.stripe import (
    REQUIRED_WALLET_FUNDING_METADATA_KEYS,
    STRIPE_PROVIDER_KEY,
    StripeWalletFundingError,
    build_wallet_funding_checkout_session_request,
    verified_wallet_funding_evidence_from_webhook,
    verified_wallet_funding_expiration_evidence_from_webhook,
    wallet_funding_evidence_from_event,
    wallet_funding_expiration_evidence_from_event,
)


TRANSACTION_INTENT_ID = UUID("aaaaaaaa-0000-4000-8000-000000000001")
TRANSACTION_INTENT_COMMIT_ID = UUID("aaaaaaaa-0000-4000-8000-000000000002")
CAPITAL_CONVERSION_QUOTE_ID = UUID("aaaaaaaa-0000-4000-8000-000000000003")
QUOTE_HASH = "a" * 64


def _context():
    return wallet_funding_context_from_economy(
        {
            "transaction_intent_id": str(TRANSACTION_INTENT_ID),
            "transaction_intent_commit_id": str(TRANSACTION_INTENT_COMMIT_ID),
            "funding_intent_key": "stripe-wallet-funding-proof",
            "idempotency_key": "prepare-stripe-wallet-funding-proof",
            "provider_key": STRIPE_PROVIDER_KEY,
            "provider_config_id": "aaaaaaaa-0000-4000-8000-000000000004",
            "provider_route_id": "aaaaaaaa-0000-4000-8000-000000000005",
            "provider_finance_entity_id": "aaaaaaaa-0000-4000-8000-000000000006",
            "recipient_finance_entity_id": "aaaaaaaa-0000-4000-8000-000000000007",
            "recipient_wallet_id": "aaaaaaaa-0000-4000-8000-000000000008",
            "recipient_wallet_public_id": "aaaaaaaa-0000-4000-8000-000000000009",
            "coin_id": "aaaaaaaa-0000-4000-8000-000000000010",
            "amount": "25.00",
            "status": "created",
            "capital_conversion_quote_id": str(CAPITAL_CONVERSION_QUOTE_ID),
            "quote_hash": QUOTE_HASH,
            "external_amount_minor": 2500,
            "external_currency": "USD",
            "target_amount": "25",
            "conversion_mode": "direct_denomination",
            "quote_source": "external_capital_provider_route",
            "quote_captured_at": "2026-07-10T08:30:00+00:00",
            "quote_expires_at": "2026-07-10T09:30:00+00:00",
        }
    )


def _checkout_request():
    return build_wallet_funding_checkout_session_request(
        context=_context(),
        success_url="https://node.aware.run/wallet/funding/success",
        cancel_url="https://node.aware.run/wallet/funding/cancel",
        description="Fund an Aware Wallet",
    )


def _payment_intent_event(
    *,
    metadata: dict[str, str],
    amount: int = 2500,
    currency: str = "usd",
) -> dict[str, object]:
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
                "amount": amount,
                "amount_received": amount,
                "currency": currency,
                "metadata": metadata,
            }
        },
    }


def _expired_checkout_event(*, metadata: dict[str, str]) -> dict[str, object]:
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
                "metadata": metadata,
            }
        },
    }


def test_build_checkout_session_request_is_one_time_hosted_wallet_funding() -> None:
    request = _checkout_request()
    fields = request.to_stripe_form_fields()

    assert request.amount == 2500
    assert request.currency == "usd"
    assert request.to_stripe_headers() == {
        "Idempotency-Key": _context().provider_session_idempotency_key
    }
    assert fields["mode"] == "payment"
    assert fields["line_items[0][price_data][unit_amount]"] == "2500"
    assert fields["line_items[0][price_data][currency]"] == "usd"
    assert fields["line_items[0][quantity]"] == "1"
    assert "price" not in fields
    assert "product" not in fields
    assert "client_secret" not in str(fields)
    assert "subscription" not in str(fields)

    metadata = request.metadata
    assert set(metadata) == set(REQUIRED_WALLET_FUNDING_METADATA_KEYS)
    assert metadata["aware_transaction_intent_id"] == str(TRANSACTION_INTENT_ID)
    assert metadata["aware_transaction_intent_commit_id"] == str(
        TRANSACTION_INTENT_COMMIT_ID
    )
    assert metadata["aware_capital_conversion_quote_id"] == str(
        CAPITAL_CONVERSION_QUOTE_ID
    )
    assert metadata["aware_quote_hash"] == QUOTE_HASH
    for key, value in metadata.items():
        assert fields[f"metadata[{key}]"] == value
        assert fields[f"payment_intent_data[metadata][{key}]"] == value


def test_build_checkout_session_request_fails_closed_on_boundary_mismatch() -> None:
    context = _context()
    with pytest.raises(StripeWalletFundingError, match="provider_key=stripe"):
        build_wallet_funding_checkout_session_request(
            context=replace(context, provider_key="fake_external_capital"),
            success_url="https://node.aware.run/success",
            cancel_url="https://node.aware.run/cancel",
        )
    with pytest.raises(StripeWalletFundingError, match="HTTPS"):
        build_wallet_funding_checkout_session_request(
            context=context,
            success_url="http://node.aware.run/success",
            cancel_url="https://node.aware.run/cancel",
        )


def test_wallet_funding_evidence_maps_only_exact_provider_facts() -> None:
    event = _payment_intent_event(metadata=_checkout_request().metadata)

    evidence = wallet_funding_evidence_from_event(event)

    assert evidence.transaction_intent_id == TRANSACTION_INTENT_ID
    assert evidence.transaction_intent_commit_id == TRANSACTION_INTENT_COMMIT_ID
    assert evidence.capital_conversion_quote_id == CAPITAL_CONVERSION_QUOTE_ID
    assert evidence.quote_hash == QUOTE_HASH
    assert evidence.external_amount_minor == 2500
    assert evidence.external_currency == "USD"
    assert evidence.provider_public_reference == "pi_wallet_1"
    assert set(evidence.to_economy_record_kwargs()) == {
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


def test_verified_wallet_funding_evidence_uses_signed_raw_payload_hash() -> None:
    secret = "whsec_test"
    raw_body = json.dumps(
        _payment_intent_event(metadata=_checkout_request().metadata),
        sort_keys=True,
    ).encode("utf-8")
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    ).hexdigest()

    evidence = verified_wallet_funding_evidence_from_webhook(
        raw_body=raw_body,
        headers={"Stripe-Signature": f"t={timestamp},v1={signature}"},
        signing_secret=secret,
    )

    assert evidence.provider_payload_hash == (
        "sha256:" + hashlib.sha256(raw_body).hexdigest()
    )
    assert evidence.provider_event_id == "evt_wallet_1"


def test_checkout_expiry_is_correlated_terminal_no_credit_evidence() -> None:
    evidence = wallet_funding_expiration_evidence_from_event(
        _expired_checkout_event(metadata=_checkout_request().metadata)
    )

    assert evidence.transaction_intent_id == TRANSACTION_INTENT_ID
    assert evidence.transaction_intent_commit_id == TRANSACTION_INTENT_COMMIT_ID
    assert evidence.capital_conversion_quote_id == CAPITAL_CONVERSION_QUOTE_ID
    assert evidence.quote_hash == QUOTE_HASH
    assert evidence.provider_public_reference == "cs_test_expired_1"
    assert evidence.idempotency_key == "stripe:event:evt_checkout_expired_1"
    assert set(evidence.to_economy_record_kwargs()) == {
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
    assert not hasattr(evidence, "external_amount_minor")
    assert not hasattr(evidence, "amount")


def test_verified_checkout_expiry_uses_signed_raw_payload_hash() -> None:
    secret = "whsec_test"
    raw_body = json.dumps(
        _expired_checkout_event(metadata=_checkout_request().metadata),
        sort_keys=True,
    ).encode("utf-8")
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    ).hexdigest()

    evidence = verified_wallet_funding_expiration_evidence_from_webhook(
        raw_body=raw_body,
        headers={"Stripe-Signature": f"t={timestamp},v1={signature}"},
        signing_secret=secret,
    )

    assert evidence.provider_payload_hash == (
        "sha256:" + hashlib.sha256(raw_body).hexdigest()
    )


@pytest.mark.parametrize(
    ("event_type", "status"),
    (
        ("payment_intent.created", "succeeded"),
        ("payment_intent.succeeded", "requires_payment_method"),
    ),
)
def test_wallet_funding_evidence_rejects_non_success_events(
    event_type: str,
    status: str,
) -> None:
    event = _payment_intent_event(metadata=_checkout_request().metadata)
    event["type"] = event_type
    event["data"]["object"]["status"] = status  # type: ignore[index]

    with pytest.raises(StripeWalletFundingError):
        wallet_funding_evidence_from_event(event)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    (
        ("amount_received", 2400, "amount"),
        ("currency", "eur", "currency"),
    ),
)
def test_wallet_funding_evidence_rejects_quote_mismatch(
    field: str,
    value: object,
    match: str,
) -> None:
    event = _payment_intent_event(metadata=_checkout_request().metadata)
    event["data"]["object"][field] = value  # type: ignore[index]

    with pytest.raises(StripeWalletFundingError, match=match):
        wallet_funding_evidence_from_event(event)


def test_wallet_funding_metadata_rejects_missing_or_service_contract_fields() -> None:
    missing = _payment_intent_event(metadata=deepcopy(_checkout_request().metadata))
    del missing["data"]["object"]["metadata"]["aware_quote_hash"]  # type: ignore[index]
    with pytest.raises(StripeWalletFundingError, match="aware_quote_hash"):
        wallet_funding_evidence_from_event(missing)

    forbidden = _payment_intent_event(metadata=deepcopy(_checkout_request().metadata))
    forbidden["data"]["object"]["metadata"]["aware_service_contract_id"] = (  # type: ignore[index]
        "service-contract-1"
    )
    with pytest.raises(StripeWalletFundingError, match="service_contract"):
        wallet_funding_evidence_from_event(forbidden)
