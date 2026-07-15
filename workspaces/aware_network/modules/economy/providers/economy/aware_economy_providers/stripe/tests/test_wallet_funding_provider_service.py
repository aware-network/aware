from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from aware_utils import secrets

from aware_economy_providers.external_capital import (
    wallet_funding_context_from_economy,
)
from aware_economy_providers.stripe import (
    STRIPE_WALLET_FUNDING_CANCEL_URL_ENV,
    STRIPE_WALLET_FUNDING_SECRET_KEY_ENV,
    STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV,
    HttpxStripeCheckoutSessionTransport,
    StripeCheckoutSessionCreationResult,
    StripeWalletFundingCheckoutSessionRequest,
    StripeWalletFundingProviderService,
    StripeWalletFundingProviderServiceError,
    stripe_wallet_funding_provider_service_from_env,
)
from aware_service_runtime.manifest.spec import AwareServiceTomlRuntimeSpec
from aware_service_runtime.runtime_secrets import configure_service_runtime_secrets


@pytest.fixture(autouse=True)
def isolated_secrets_state() -> None:
    secrets.reset_secrets_state_for_tests()


class _FakeStripeCheckoutSessionTransport:
    def __init__(self, result: StripeCheckoutSessionCreationResult) -> None:
        self.result = result
        self.requests: list[StripeWalletFundingCheckoutSessionRequest] = []

    def create_checkout_session(
        self,
        request: StripeWalletFundingCheckoutSessionRequest,
    ) -> StripeCheckoutSessionCreationResult:
        self.requests.append(request)
        return self.result


def _context():
    return wallet_funding_context_from_economy(
        {
            "transaction_intent_id": str(uuid4()),
            "transaction_intent_commit_id": str(uuid4()),
            "funding_intent_key": "stripe-provider-service-proof",
            "idempotency_key": "prepare-stripe-provider-service-proof",
            "provider_key": "stripe",
            "provider_config_id": str(uuid4()),
            "provider_route_id": str(uuid4()),
            "provider_finance_entity_id": str(uuid4()),
            "recipient_finance_entity_id": str(uuid4()),
            "recipient_wallet_id": str(uuid4()),
            "recipient_wallet_public_id": str(uuid4()),
            "coin_id": str(uuid4()),
            "amount": "25.00",
            "status": "created",
            "capital_conversion_quote_id": str(uuid4()),
            "quote_hash": "b" * 64,
            "external_amount_minor": 2500,
            "external_currency": "USD",
            "target_amount": "25",
            "conversion_mode": "direct_denomination",
            "quote_source": "external_capital_provider_route",
            "quote_captured_at": "2026-07-10T08:30:00+00:00",
            "quote_expires_at": "2026-07-10T09:30:00+00:00",
        }
    )


def _creation_result(*, livemode: bool = False):
    return StripeCheckoutSessionCreationResult(
        checkout_session_id="cs_test_wallet_funding_1",
        url="https://checkout.stripe.com/c/pay/cs_test_wallet_funding_1",
        status="open",
        livemode=livemode,
        expires_at=1_789_999_999,
        request_id="req_wallet_funding_1",
    )


def test_stripe_provider_service_returns_provider_neutral_hosted_continuation() -> None:
    transport = _FakeStripeCheckoutSessionTransport(_creation_result())
    context = _context()
    service = StripeWalletFundingProviderService(
        transport=transport,
        success_url="https://node.aware.run/wallet/funding/success",
        cancel_url="https://node.aware.run/wallet/funding/cancel",
    )

    receipt = service.create_wallet_funding_session(context)

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.amount == 2500
    assert request.currency == "usd"
    assert request.idempotency_key == context.provider_session_idempotency_key
    assert receipt.transaction_intent_id == context.transaction_intent_id
    assert receipt.transaction_intent_commit_id == context.transaction_intent_commit_id
    assert receipt.provider_public_reference == "cs_test_wallet_funding_1"
    assert receipt.continuation_kind == "open_external_url"
    assert receipt.continuation_url.startswith("https://checkout.stripe.com/")
    assert receipt.continuation_expires_at is not None
    assert "client_secret" not in str(receipt.to_feedback_payload())


def test_stripe_provider_service_rejects_live_or_wrong_provider_context() -> None:
    context = _context()
    live_service = StripeWalletFundingProviderService(
        transport=_FakeStripeCheckoutSessionTransport(_creation_result(livemode=True)),
        success_url="https://node.aware.run/success",
        cancel_url="https://node.aware.run/cancel",
    )

    with pytest.raises(StripeWalletFundingProviderServiceError, match="test-mode"):
        live_service.create_wallet_funding_session(context)
    with pytest.raises(
        StripeWalletFundingProviderServiceError,
        match="provider_key=stripe",
    ):
        live_service.create_wallet_funding_session(replace(context, provider_key="fake_external_capital"))


def test_httpx_transport_and_env_factory_require_test_mode_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(StripeWalletFundingProviderServiceError, match="test-mode"):
        HttpxStripeCheckoutSessionTransport(secret_key="sk_live_bad")

    transport = HttpxStripeCheckoutSessionTransport(secret_key="sk_test_good")
    assert transport.secret_key == "sk_test_good"

    monkeypatch.setenv(STRIPE_WALLET_FUNDING_SECRET_KEY_ENV, "sk_test_from_env")
    monkeypatch.delenv(STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV, raising=False)
    monkeypatch.delenv(STRIPE_WALLET_FUNDING_CANCEL_URL_ENV, raising=False)
    with pytest.raises(StripeWalletFundingProviderServiceError, match="SUCCESS_URL"):
        stripe_wallet_funding_provider_service_from_env()

    monkeypatch.setenv(
        STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV,
        "https://node.aware.run/wallet/funding/success",
    )
    monkeypatch.setenv(
        STRIPE_WALLET_FUNDING_CANCEL_URL_ENV,
        "https://node.aware.run/wallet/funding/cancel",
    )
    service = stripe_wallet_funding_provider_service_from_env()
    assert isinstance(service.transport, HttpxStripeCheckoutSessionTransport)
    assert service.success_url.endswith("/success")
    assert service.cancel_url.endswith("/cancel")


def test_env_factory_resolves_test_key_from_service_secret_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    secrets_dir = tmp_path / "provider-secrets"
    secrets_dir.mkdir()
    (secrets_dir / STRIPE_WALLET_FUNDING_SECRET_KEY_ENV).write_text(
        "sk_test_from_service_secret_file\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(STRIPE_WALLET_FUNDING_SECRET_KEY_ENV, raising=False)
    monkeypatch.setenv(
        STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV,
        "https://node.aware.run/wallet/funding/success",
    )
    monkeypatch.setenv(
        STRIPE_WALLET_FUNDING_CANCEL_URL_ENV,
        "https://node.aware.run/wallet/funding/cancel",
    )
    configure_service_runtime_secrets(
        AwareServiceTomlRuntimeSpec(
            canonical_secrets_dir=secrets_dir.as_posix(),
        )
    )

    service = stripe_wallet_funding_provider_service_from_env()

    assert isinstance(service.transport, HttpxStripeCheckoutSessionTransport)
    assert service.transport.secret_key == "sk_test_from_service_secret_file"


def test_checkout_session_creation_result_rejects_invalid_stripe_response() -> None:
    with pytest.raises(
        StripeWalletFundingProviderServiceError,
        match="Checkout Session",
    ):
        StripeCheckoutSessionCreationResult.from_stripe_payload({"object": "payment_intent"})

    with pytest.raises(StripeWalletFundingProviderServiceError, match="must be open"):
        StripeCheckoutSessionCreationResult.from_stripe_payload(
            {
                "id": "cs_test_closed",
                "object": "checkout.session",
                "status": "complete",
                "url": "https://checkout.stripe.com/c/pay/cs_test_closed",
                "expires_at": 1_789_999_999,
            }
        )

    with pytest.raises(StripeWalletFundingProviderServiceError, match="HTTPS URL"):
        StripeCheckoutSessionCreationResult.from_stripe_payload(
            {
                "id": "cs_test_bad_url",
                "object": "checkout.session",
                "status": "open",
                "url": "http://checkout.stripe.com/c/pay/cs_test_bad_url",
                "expires_at": 1_789_999_999,
            }
        )
