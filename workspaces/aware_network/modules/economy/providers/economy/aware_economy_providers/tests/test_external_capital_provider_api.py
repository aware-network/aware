from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from aware_utils import secrets

from aware_economy_providers.external_capital import (
    EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY,
    wallet_funding_context_from_economy,
)
from aware_economy_providers.external_capital_provider_api import (
    ExternalCapitalProviderApi,
    ExternalCapitalProviderApiError,
    external_capital_provider_api_from_env,
)
from aware_economy_providers.stripe import (
    STRIPE_PROVIDER_KEY,
    STRIPE_WALLET_FUNDING_CANCEL_URL_ENV,
    STRIPE_WALLET_FUNDING_SECRET_KEY_ENV,
    STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV,
    StripeCheckoutSessionCreationResult,
    StripeWalletFundingCheckoutSessionRequest,
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


def _context_payload(*, provider_key: str) -> dict[str, object]:
    return {
        "transaction_intent_id": str(uuid4()),
        "transaction_intent_commit_id": str(uuid4()),
        "funding_intent_key": "provider-api-proof",
        "idempotency_key": "prepare-provider-api-proof",
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
        "target_amount": "42.50",
        "conversion_mode": "direct_denomination",
        "quote_source": "external_capital_provider_route",
        "quote_captured_at": "2026-07-10T08:30:00+00:00",
        "quote_expires_at": "2026-07-10T09:30:00+00:00",
    }


def test_external_capital_provider_api_dispatches_fake_provider() -> None:
    context = wallet_funding_context_from_economy(_context_payload(provider_key=EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY))

    receipt = ExternalCapitalProviderApi().create_wallet_funding_session(context)

    assert receipt.transaction_intent_id == context.transaction_intent_id
    assert receipt.transaction_intent_commit_id == context.transaction_intent_commit_id
    assert receipt.provider_key == EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY
    assert receipt.continuation_kind == "open_external_url"
    assert receipt.continuation_url.startswith("https://provider.example/fund/")


def test_external_capital_provider_api_dispatches_stripe_hosted_checkout() -> None:
    transport = _FakeStripeCheckoutSessionTransport(
        StripeCheckoutSessionCreationResult(
            checkout_session_id="cs_test_provider_api_1",
            url="https://checkout.stripe.com/c/pay/cs_test_provider_api_1",
            status="open",
            livemode=False,
            expires_at=1_789_999_999,
            request_id="req_provider_api_1",
        )
    )
    context = wallet_funding_context_from_economy(_context_payload(provider_key=STRIPE_PROVIDER_KEY))
    provider_api = ExternalCapitalProviderApi(
        stripe_transport=transport,
        stripe_success_url="https://node.aware.run/wallet/funding/success",
        stripe_cancel_url="https://node.aware.run/wallet/funding/cancel",
    )

    receipt = provider_api.create_wallet_funding_session(context)

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.amount == 4250
    assert request.currency == "usd"
    assert request.metadata["aware_transaction_intent_id"] == str(context.transaction_intent_id)
    assert receipt.provider_public_reference == "cs_test_provider_api_1"
    assert receipt.continuation_kind == "open_external_url"
    assert receipt.continuation_url.startswith("https://checkout.stripe.com/")


def test_external_capital_provider_api_fails_closed_for_unwired_provider() -> None:
    stripe_context = wallet_funding_context_from_economy(_context_payload(provider_key=STRIPE_PROVIDER_KEY))
    unknown_context = wallet_funding_context_from_economy(_context_payload(provider_key="wallet-provider-x"))

    with pytest.raises(ExternalCapitalProviderApiError, match="transport"):
        ExternalCapitalProviderApi().create_wallet_funding_session(stripe_context)
    with pytest.raises(ExternalCapitalProviderApiError, match="Unsupported"):
        ExternalCapitalProviderApi().create_wallet_funding_session(unknown_context)


def test_provider_api_from_env_keeps_fake_available_without_stripe_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_STRIPE_WALLET_FUNDING_SECRET_KEY", raising=False)
    context = wallet_funding_context_from_economy(_context_payload(provider_key=EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY))

    receipt = external_capital_provider_api_from_env().create_wallet_funding_session(context)

    assert receipt.provider_key == EXTERNAL_CAPITAL_FAKE_PROVIDER_KEY


def test_provider_api_detects_stripe_configuration_from_service_values_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    values_dir = tmp_path / "provider-values"
    values_dir.mkdir()
    values = {
        STRIPE_WALLET_FUNDING_SECRET_KEY_ENV: "sk_test_provider_api_file",
        STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV: ("https://node.aware.run/wallet/funding/success"),
        STRIPE_WALLET_FUNDING_CANCEL_URL_ENV: ("https://node.aware.run/wallet/funding/cancel"),
    }
    for name, value in values.items():
        (values_dir / name).write_text(value + "\n", encoding="utf-8")
        monkeypatch.delenv(name, raising=False)
    configure_service_runtime_secrets(
        AwareServiceTomlRuntimeSpec(
            canonical_secrets_dir=values_dir.as_posix(),
        )
    )

    provider_api = external_capital_provider_api_from_env()

    assert provider_api.stripe_transport is not None
    assert provider_api.stripe_success_url == values[STRIPE_WALLET_FUNDING_SUCCESS_URL_ENV]
    assert provider_api.stripe_cancel_url == values[STRIPE_WALLET_FUNDING_CANCEL_URL_ENV]
