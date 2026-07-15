from __future__ import annotations

from uuid import uuid4

import pytest

from aware_economy_providers.external_capital import (
    EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY,
    ExternalCapitalProviderError,
    create_fake_wallet_funding_session,
    fake_wallet_funding_sensor_evidence,
    wallet_funding_context_from_economy,
)


def _resolved_context(*, provider_key: str = EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY):
    return {
        "transaction_intent_id": str(uuid4()),
        "transaction_intent_commit_id": str(uuid4()),
        "funding_intent_key": "fund-wallet-1",
        "idempotency_key": "prepare-fund-wallet-1",
        "provider_key": provider_key,
        "provider_config_id": str(uuid4()),
        "provider_route_id": str(uuid4()),
        "provider_finance_entity_id": str(uuid4()),
        "recipient_finance_entity_id": str(uuid4()),
        "recipient_wallet_id": str(uuid4()),
        "recipient_wallet_public_id": str(uuid4()),
        "coin_id": str(uuid4()),
        "amount": "42.50",
        "status": "created",
        "capital_conversion_quote_id": str(uuid4()),
        "quote_hash": "a" * 64,
        "external_amount_minor": 4250,
        "external_currency": "USD",
        "target_amount": "42.5",
        "conversion_mode": "direct_denomination",
        "quote_source": "external_capital_provider_route",
        "quote_captured_at": "2026-07-10T08:30:00+00:00",
        "quote_expires_at": "2026-07-10T09:30:00+00:00",
    }


def test_provider_context_is_strict_typed_economy_truth() -> None:
    context = wallet_funding_context_from_economy(_resolved_context())

    assert context.external_amount_minor == 4250
    assert context.external_currency == "USD"
    assert context.amount == context.target_amount
    assert context.provider_session_idempotency_key.endswith(context.quote_hash)


def test_provider_context_rejects_copied_quote_mismatch() -> None:
    payload = _resolved_context()
    payload["target_amount"] = "43"

    with pytest.raises(ExternalCapitalProviderError, match="target amount mismatch"):
        wallet_funding_context_from_economy(payload)


def test_fake_provider_returns_hosted_url_and_exact_sensor_evidence() -> None:
    context = wallet_funding_context_from_economy(_resolved_context())
    receipt = create_fake_wallet_funding_session(context)
    evidence = fake_wallet_funding_sensor_evidence(
        receipt,
        context=context,
        external_created_at="2026-07-10T08:31:00+00:00",
    )

    assert receipt.continuation_kind == "open_external_url"
    assert receipt.continuation_url.startswith("https://provider.example/fund/")
    assert evidence.transaction_intent_commit_id == context.transaction_intent_commit_id
    assert evidence.capital_conversion_quote_id == context.capital_conversion_quote_id
    assert evidence.provider_payload_hash.startswith("sha256:")
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


def test_fake_provider_rejects_non_fake_context() -> None:
    context = wallet_funding_context_from_economy(
        _resolved_context(provider_key="stripe")
    )

    with pytest.raises(ExternalCapitalProviderError, match="requires provider_key"):
        create_fake_wallet_funding_session(context)
