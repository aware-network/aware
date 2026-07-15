from __future__ import annotations

# Standard
from typing import Literal

# Third-party
from pydantic import Field

# Network Service Dto
from aware_network_service_dto.comms.models.network_node import (
    NetworkNodeOperationRequest,
    NetworkNodeOperationResponse,
)


class MembershipStatusRequest(NetworkNodeOperationRequest):
    """
    Economy membership operations for the Network Node control-plane (DTO-only).
    These operations are routed via:
    `NetworkOperation(type=NETWORK_NODE) -> NetworkNodeOperation(request/response)`.
    Canonical rules:
    - Secrets never appear in clients (Stripe secret key is node-owned).
    - `actor_id` is taken from the authenticated interface session binding; clients must not spoof it.
    - Membership gating is enforced by the node/runtime, not by the UI.
    Read membership state for the authenticated actor.
    """

    # Discriminator Tag
    operation: Literal["membership_status"] = "membership_status"


class MembershipStatusResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["membership_status"] = "membership_status"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    is_active: bool
    is_bypassed: bool = Field(default=False)
    plan_label: str | None = Field(default=None)
    current_period_end: str | None = Field(default=None)


class MembershipCheckoutSessionCreateRequest(NetworkNodeOperationRequest):
    """
    Create a Stripe-hosted checkout session for membership subscription.
    v0:
    - Node uses its configured Stripe price id(s) and returns a `checkout_url` for redirection.
    - The request may optionally select a plan key; the node must validate it against its allowlist.
    """

    # Discriminator Tag
    operation: Literal["membership_checkout_session_create"] = "membership_checkout_session_create"

    # Attributes
    plan_key: str | None = Field(default=None)
    success_url: str | None = Field(default=None)
    cancel_url: str | None = Field(default=None)


class MembershipCheckoutSessionCreateResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["membership_checkout_session_create"] = "membership_checkout_session_create"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    checkout_url: str | None = Field(default=None)
    checkout_session_id: str | None = Field(default=None)


class MembershipPurchasePrepareRequest(NetworkNodeOperationRequest):
    """
    Prepare a membership purchase flow for the authenticated actor.
    Provider-neutral contract:
    - Desktop/web may return a Stripe `checkout_url`.
    - iOS returns an `apple_product_id` for StoreKit purchase.
    - Android returns a `google_product_id` for Play Billing purchase.
    Canonical: clients must never treat redirects as proof of payment; membership becomes active
    only after server-side verification (webhook/notification or purchase-claim verification).
    """

    # Discriminator Tag
    operation: Literal["membership_purchase_prepare"] = "membership_purchase_prepare"

    # Attributes
    plan_key: str | None = Field(default=None)
    platform: str | None = Field(default=None, description='e.g. "ios" | "android" | "desktop" | "web"')


class MembershipPurchasePrepareResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["membership_purchase_prepare"] = "membership_purchase_prepare"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    provider: str = Field(description='e.g. "stripe" | "apple_iap" | "google_play"')
    plan_label: str | None = Field(default=None)
    checkout_url: str | None = Field(default=None)
    apple_product_id: str | None = Field(default=None)
    google_product_id: str | None = Field(default=None)


class MembershipPurchaseClaimRequest(NetworkNodeOperationRequest):
    """
    Claim/verify a membership purchase.
    This operation exists primarily for store billing (iOS/Android) where the client must initiate
    the purchase locally and then submit proof for server-side verification.
    """

    # Discriminator Tag
    operation: Literal["membership_purchase_claim"] = "membership_purchase_claim"

    # Attributes
    provider: str
    plan_key: str | None = Field(default=None)
    apple_product_id: str | None = Field(default=None)
    apple_receipt: str | None = Field(default=None)
    apple_transaction_id: str | None = Field(default=None)
    google_product_id: str | None = Field(default=None)
    google_purchase_token: str | None = Field(default=None)


class MembershipPurchaseClaimResponse(NetworkNodeOperationResponse):
    # Discriminator Tag
    operation: Literal["membership_purchase_claim"] = "membership_purchase_claim"

    # Attributes
    status: str
    error: str | None = Field(default=None)
    is_active: bool
    plan_label: str | None = Field(default=None)
    current_period_end: str | None = Field(default=None)
