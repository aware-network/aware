from __future__ import annotations

import importlib.util

import aware_economy_providers.stripe as stripe
from aware_economy_providers.stripe import StripeSignatureError
from aware_economy_providers.stripe import StripeProviderLifecycleError
from aware_economy_providers.stripe import StripeWalletFundingError
from aware_economy_providers.stripe import (
    build_wallet_funding_checkout_session_request,
)
from aware_economy_providers.stripe import provider_lifecycle_evidence_from_event
from aware_economy_providers.stripe import (
    verified_provider_lifecycle_evidence_from_webhook,
)
from aware_economy_providers.stripe import verify_and_construct_event


def test_stripe_package_exports_hosted_wallet_funding_and_verification() -> None:
    assert StripeSignatureError.__name__ == "StripeSignatureError"
    assert StripeProviderLifecycleError.__name__ == "StripeProviderLifecycleError"
    assert StripeWalletFundingError.__name__ == "StripeWalletFundingError"
    assert callable(verify_and_construct_event)
    assert callable(build_wallet_funding_checkout_session_request)
    assert callable(provider_lifecycle_evidence_from_event)
    assert callable(verified_provider_lifecycle_evidence_from_webhook)
    assert not hasattr(stripe, "build_wallet_funding_payment_intent_request")


def test_stripe_public_exports_are_wallet_funding_or_lifecycle_only() -> None:
    forbidden_fragments = (
        "service_contract",
        "subscription",
        "payment_link",
        "membership",
        "entitlement",
    )
    exported_names = tuple(str(name).lower() for name in stripe.__all__)

    assert exported_names
    assert not any(
        fragment in exported_name
        for exported_name in exported_names
        for fragment in forbidden_fragments
    )


def test_service_contract_direct_modules_are_not_active() -> None:
    removed_modules = (
        "aware_economy_providers.stripe.service_contract_activation",
        "aware_economy_providers.stripe.service_contract_checkout",
        "aware_economy_providers.stripe.payment_link_reconciliation",
    )
    for module_name in removed_modules:
        assert importlib.util.find_spec(module_name) is None
