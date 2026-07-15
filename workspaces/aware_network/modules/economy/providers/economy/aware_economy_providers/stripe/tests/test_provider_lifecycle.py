from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from aware_economy_providers.stripe import (
    SUPPORTED_PROVIDER_LIFECYCLE_EVENT_TYPES,
    StripeProviderLifecycleError,
    StripeProviderLifecycleIgnored,
    provider_lifecycle_evidence_from_event,
    verified_provider_lifecycle_evidence_from_webhook,
)


def _stripe_event(
    *,
    event_type: str,
    object_id: str,
    object_type: str,
    payment_intent: object = "pi_wallet_1",
    amount: int = 500,
    currency: str = "usd",
    status: str | None = None,
    metadata: dict[str, str] | None = None,
) -> dict[str, object]:
    stripe_object: dict[str, object] = {
        "id": object_id,
        "object": object_type,
        "payment_intent": payment_intent,
        "amount": amount,
        "currency": currency,
        "metadata": metadata or {},
    }
    if status is not None:
        stripe_object["status"] = status
    return {
        "id": "evt_lifecycle_1",
        "object": "event",
        "type": event_type,
        "created": 1_720_000_000,
        "livemode": False,
        "data": {"object": stripe_object},
    }


def test_refund_maps_only_native_provider_facts() -> None:
    event = _stripe_event(
        event_type="refund.created",
        object_id="re_wallet_1",
        object_type="refund",
        status="succeeded",
        metadata={
            "aware_wallet_id": "attacker-selected-wallet",
            "aware_amount": "999999",
        },
    )

    evidence = provider_lifecycle_evidence_from_event(event)
    kwargs = evidence.to_economy_record_kwargs()

    assert SUPPORTED_PROVIDER_LIFECYCLE_EVENT_TYPES == (
        "charge.dispute.closed",
        "charge.dispute.created",
        "refund.created",
        "refund.updated",
    )
    assert evidence.provider_key == "stripe"
    assert evidence.provider_event_id == "evt_lifecycle_1"
    assert evidence.provider_lifecycle_object_id == "re_wallet_1"
    assert evidence.provider_lifecycle_effect_key == "refund"
    assert evidence.provider_payment_reference == "pi_wallet_1"
    assert evidence.external_amount_minor == 500
    assert evidence.external_currency == "USD"
    assert evidence.event_kind == "refund"
    assert evidence.external_created_at == "2024-07-03T09:46:40Z"
    assert set(kwargs) == {
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
    assert not any(
        key in kwargs
        for key in (
            "provider_finance_entity_id",
            "wallet_finance_entity_id",
            "wallet_id",
            "wallet_public_id",
            "coin_id",
            "amount",
        )
    )


@pytest.mark.parametrize(
    ("status", "event_kind"),
    (
        ("won", "dispute_release"),
        ("warning_closed", "dispute_release"),
        ("lost", "chargeback"),
    ),
)
def test_closed_dispute_maps_one_explicit_effect_stage(
    status: str,
    event_kind: str,
) -> None:
    evidence = provider_lifecycle_evidence_from_event(
        _stripe_event(
            event_type="charge.dispute.closed",
            object_id="du_wallet_1",
            object_type="dispute",
            amount=1000,
            status=status,
        )
    )

    assert evidence.event_kind == event_kind
    assert evidence.provider_lifecycle_effect_key == event_kind
    assert evidence.provider_lifecycle_object_id == "du_wallet_1"
    assert evidence.external_amount_minor == 1000


def test_dispute_created_maps_hold_and_accepts_expanded_payment_intent() -> None:
    evidence = provider_lifecycle_evidence_from_event(
        _stripe_event(
            event_type="charge.dispute.created",
            object_id="du_wallet_1",
            object_type="dispute",
            payment_intent={"id": "pi_wallet_1", "object": "payment_intent"},
            amount=1000,
            status="needs_response",
        )
    )

    assert evidence.event_kind == "dispute"
    assert evidence.provider_payment_reference == "pi_wallet_1"


def test_signed_lifecycle_evidence_uses_raw_payload_hash() -> None:
    secret = "whsec_test"
    raw_body = json.dumps(
        _stripe_event(
            event_type="refund.created",
            object_id="re_wallet_1",
            object_type="refund",
            status="succeeded",
        ),
        sort_keys=True,
    ).encode("utf-8")
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + raw_body,
        hashlib.sha256,
    )

    evidence = verified_provider_lifecycle_evidence_from_webhook(
        raw_body=raw_body,
        headers={"Stripe-Signature": f"t={timestamp},v1={signature.hexdigest()}"},
        signing_secret=secret,
    )

    assert evidence.provider_payload_hash == ("sha256:" + hashlib.sha256(raw_body).hexdigest())


@pytest.mark.parametrize("status", ("pending", "requires_action", "failed", "canceled"))
def test_non_terminal_refund_has_no_wallet_effect(status: str) -> None:
    event = _stripe_event(
        event_type="refund.updated",
        object_id="re_wallet_1",
        object_type="refund",
        status=status,
    )

    with pytest.raises(StripeProviderLifecycleIgnored) as captured:
        provider_lifecycle_evidence_from_event(event)

    assert captured.value.provider_event_id == "evt_lifecycle_1"
    assert captured.value.provider_lifecycle_object_id == "re_wallet_1"


@pytest.mark.parametrize(
    ("event_type", "object_type"),
    (
        ("charge.refunded", "charge"),
        ("payout.paid", "payout"),
        ("transfer.reversed", "transfer"),
    ),
)
def test_non_wallet_lifecycle_events_fail_closed(
    event_type: str,
    object_type: str,
) -> None:
    event = _stripe_event(
        event_type=event_type,
        object_id="provider_object_1",
        object_type=object_type,
        status="succeeded",
    )

    with pytest.raises(StripeProviderLifecycleError, match="Unsupported"):
        provider_lifecycle_evidence_from_event(event)


def test_lifecycle_requires_original_payment_reference() -> None:
    event = _stripe_event(
        event_type="refund.created",
        object_id="re_wallet_1",
        object_type="refund",
        payment_intent=None,
        status="succeeded",
    )

    with pytest.raises(StripeProviderLifecycleError, match="payment_intent"):
        provider_lifecycle_evidence_from_event(event)
