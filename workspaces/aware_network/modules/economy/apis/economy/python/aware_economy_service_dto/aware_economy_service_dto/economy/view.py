from __future__ import annotations

# Standard
from decimal import Decimal
from typing import Annotated

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import (
    DecimalWire,
    JsonObject,
)


class EconomyWalletCapitalBalanceViewStateV1(BaseModel):
    """
    API-owned view-state contracts for Economy panes.
    Public API view key: economy.wallet_capital
    """

    # Attributes
    wallet_balance_id: str | None = Field(default=None)
    wallet_id: str | None = Field(default=None)
    wallet_public_id: str | None = Field(default=None)
    finance_entity_id: str | None = Field(default=None)
    coin_id: str | None = Field(default=None)
    balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    held_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    available_balance: Annotated[Decimal, DecimalWire()] = Field(default=Decimal("0"))
    status: str = Field(default="unknown")


class EconomyWalletCapitalActivityViewStateV1(BaseModel):
    # Attributes
    activity_ref: str
    activity_kind: str
    status: str | None = Field(default=None)
    occurred_at: str | None = Field(default=None)
    amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    coin_id: str | None = Field(default=None)
    transaction_intent_id: str | None = Field(default=None)
    transaction_external_id: str | None = Field(default=None)
    transaction_id: str | None = Field(default=None)
    reservation_id: str | None = Field(default=None)
    escrow_id: str | None = Field(default=None)
    settlement_id: str | None = Field(default=None)
    provider_lifecycle_receipt_id: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    description: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class EconomyWalletCapitalActionViewStateV1(BaseModel):
    # Attributes
    action_key: str
    label: str | None = Field(default=None)
    enabled: bool = Field(default=False)
    status: str = Field(default="unavailable")
    disabled_reason: str | None = Field(default=None)
    input_hints: JsonObject = Field(default_factory=JsonObject)
    provenance: JsonObject = Field(default_factory=JsonObject)


class EconomyWalletCapitalFundingProviderViewStateV1(BaseModel):
    # Attributes
    provider_config_id: str
    provider_route_id: str
    provider_finance_entity_id: str
    provider_key: str
    label: str | None = Field(default=None)
    status: str = Field(default="available")
    route_key: str
    default_coin_id: str | None = Field(default=None)
    supported_coin_ids: list[str] = Field(default_factory=list)
    external_currency: str
    external_minor_unit_exponent: int
    conversion_mode: str
    min_external_amount_minor: int | None = Field(default=None)
    max_external_amount_minor: int | None = Field(default=None)
    disabled_reason: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class EconomyWalletCapitalFundingIntentViewStateV1(BaseModel):
    # Attributes
    funding_intent_ref: str
    transaction_intent_id: str | None = Field(default=None)
    provider_config_id: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    coin_id: str | None = Field(default=None)
    amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    status: str = Field(default="pending")
    created_at: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    capital_conversion_quote_id: str | None = Field(default=None)
    provider_route_id: str | None = Field(default=None)
    external_amount_minor: int | None = Field(default=None)
    external_currency: str | None = Field(default=None)
    target_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    conversion_mode: str | None = Field(default=None)
    quote_source: str | None = Field(default=None)
    quote_hash: str | None = Field(default=None)
    quote_captured_at: str | None = Field(default=None)
    quote_expires_at: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)


class EconomyWalletCapitalViewStateV1(BaseModel):
    # Attributes
    view_ref: str = Field(default="economy.wallet_capital")
    root_projection_ref: str = Field(default="Wallet.home")
    operation: str = Field(default="refresh_wallet_capital")
    status: str = Field(default="waiting")
    status_tone: str = Field(default="neutral")
    wallet_id: str | None = Field(default=None)
    wallet_public_id: str | None = Field(default=None)
    finance_entity_id: str | None = Field(default=None)
    coin_id: str | None = Field(default=None)
    ready: bool = Field(default=False)
    refresh_action_key: str = Field(default="refresh_wallet_capital")
    funding_action_key: str = Field(default="fund_wallet")
    action_keys: list[str] = Field(default_factory=list)
    actions: list[EconomyWalletCapitalActionViewStateV1] = Field(default_factory=list)
    action_count: int = Field(default=0)
    can_fund_wallet: bool = Field(default=False)
    funding_status: str = Field(default="unavailable")
    funding_disabled_reason: str | None = Field(default=None)
    funding_providers: list[EconomyWalletCapitalFundingProviderViewStateV1] = Field(default_factory=list)
    funding_provider_count: int = Field(default=0)
    pending_funding_intents: list[EconomyWalletCapitalFundingIntentViewStateV1] = Field(default_factory=list)
    pending_funding_intent_count: int = Field(default=0)
    balances: list[EconomyWalletCapitalBalanceViewStateV1] = Field(default_factory=list)
    activity: list[EconomyWalletCapitalActivityViewStateV1] = Field(default_factory=list)
    activity_count: int = Field(default=0)
    transaction_intent_count: int = Field(default=0)
    transaction_external_count: int = Field(default=0)
    transaction_count: int = Field(default=0)
    reservation_count: int = Field(default=0)
    escrow_count: int = Field(default=0)
    settlement_count: int = Field(default=0)
    provider_lifecycle_receipt_count: int = Field(default=0)
    info: str | None = Field(default=None)
    empty_message: str = Field(default="No wallet capital activity yet.")
    blockers: list[str] = Field(default_factory=list)
    provenance: JsonObject = Field(default_factory=JsonObject)
