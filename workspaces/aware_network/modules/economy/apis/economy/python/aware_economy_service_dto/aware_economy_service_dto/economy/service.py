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


class EconomyActorStatusRequest(BaseModel):
    """
    Canonical Economy service-host DTOs (transport-layer, graph/ORM agnostic).
    SSOT: `economy-service-dto` generated from `apis/economy/dto`.
    This package sits between caller/API bindings and the Economy service host.
    Runtime-local Python shims may re-export these DTOs for compatibility, but
    public schema ownership remains under `apis/economy/dto`.
    """

    # Attributes
    operation: str = Field(default="economy_actor_status")
    actor_id: str | None = Field(default=None)
    finance_role_key: str = Field(default="primary")


class EconomyActorStatusResponse(BaseModel):
    # Attributes
    operation: str = Field(default="economy_actor_status")
    finance_role_key: str = Field(default="primary")
    finance_entity_ready: bool
    wallet_ready: bool
    next_step: str
    finance_entity_id: str | None = Field(default=None)
    wallet_id: str | None = Field(default=None)
    wallet_public_id: str | None = Field(default=None)


class EconomyEnsureFinanceEntityRequest(BaseModel):
    # Attributes
    operation: str = Field(default="ensure_finance_entity")
    actor_id: str | None = Field(default=None)
    finance_role_key: str = Field(default="primary")


class EconomyEnsureFinanceEntityResponse(BaseModel):
    # Attributes
    operation: str = Field(default="ensure_finance_entity")
    finance_role_key: str = Field(default="primary")
    finance_entity_id: str
    wallet_id: str
    wallet_public_id: str


class EconomyWalletFundingPrepareRequest(BaseModel):
    # Attributes
    operation: str = Field(default="prepare_wallet_funding")
    target_wallet_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    funding_intent_key: str
    idempotency_key: str
    provider_key: str


class EconomyWalletFundingPrepareResponse(BaseModel):
    # Attributes
    operation: str = Field(default="prepare_wallet_funding")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    funding_intent_key: str
    idempotency_key: str
    provider_key: str
    provider_config_id: str
    provider_route_id: str
    provider_finance_entity_id: str
    recipient_finance_entity_id: str
    recipient_wallet_id: str
    recipient_wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    capital_conversion_quote_id: str
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    conversion_mode: str
    quote_captured_at: str
    quote_expires_at: str | None = Field(default=None)
    status: str
    idempotent_replay: bool = Field(default=False)


class EconomyWalletFundingContextResolveRequest(BaseModel):
    # Attributes
    operation: str = Field(default="resolve_wallet_funding_context")
    transaction_intent_id: str
    transaction_intent_commit_id: str


class EconomyWalletFundingContextResolveResponse(BaseModel):
    # Attributes
    operation: str = Field(default="resolve_wallet_funding_context")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    funding_intent_key: str
    idempotency_key: str
    provider_key: str
    provider_config_id: str
    provider_route_id: str
    provider_finance_entity_id: str
    recipient_finance_entity_id: str
    recipient_wallet_id: str
    recipient_wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    status: str
    capital_conversion_quote_id: str
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    target_amount: Annotated[Decimal, DecimalWire()]
    conversion_mode: str
    quote_source: str
    quote_captured_at: str
    quote_expires_at: str | None = Field(default=None)


class EconomyWalletFundingRecordRequest(BaseModel):
    # Attributes
    operation: str = Field(default="record_verified_wallet_funding")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    capital_conversion_quote_id: str
    quote_hash: str
    external_amount_minor: int
    external_currency: str
    provider_public_reference: str
    provider_payload_hash: str
    external_created_at: str


class EconomyWalletFundingRecordResponse(BaseModel):
    # Attributes
    operation: str = Field(default="record_verified_wallet_funding")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    capital_conversion_quote_id: str
    quote_hash: str
    transaction_external_id: str
    transaction_id: str
    transaction_nonce: int
    wallet_external_ingress_application_id: str
    wallet_balance_id: str
    provider_finance_entity_id: str
    recipient_finance_entity_id: str
    recipient_wallet_id: str
    recipient_wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    previous_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    status: str
    idempotent_replay: bool = Field(default=False)


class EconomyWalletFundingCancelRequest(BaseModel):
    # Attributes
    operation: str = Field(default="record_wallet_funding_expiration")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    provider_key: str
    provider_event_id: str
    idempotency_key: str
    capital_conversion_quote_id: str
    quote_hash: str
    provider_public_reference: str
    provider_payload_hash: str
    external_created_at: str


class EconomyWalletFundingCancelResponse(BaseModel):
    # Attributes
    operation: str = Field(default="record_wallet_funding_expiration")
    transaction_intent_id: str
    transaction_intent_commit_id: str
    transaction_intent_external_expiration_id: str
    provider_config_id: str
    capital_conversion_quote_id: str
    quote_hash: str
    provider_key: str
    provider_event_id: str
    provider_public_reference: str
    status: str
    idempotent_replay: bool = Field(default=False)


class EconomyProviderLifecycleRecordRequest(BaseModel):
    # Attributes
    operation: str = Field(default="record_provider_lifecycle_event")
    provider_key: str
    provider_event_id: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    provider_payment_reference: str
    external_amount_minor: int
    external_currency: str
    event_kind: str
    provider_payload_hash: str
    external_created_at: str
    metadata_json: JsonObject | None = Field(default=None)


class EconomyProviderLifecycleRecordResponse(BaseModel):
    # Attributes
    operation: str = Field(default="record_provider_lifecycle_event")
    provider_lifecycle_receipt_id: str
    wallet_balance_id: str
    provider_finance_entity_id: str
    provider_key: str
    provider_event_id: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    idempotency_key: str
    wallet_finance_entity_id: str
    wallet_id: str
    wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    event_kind: str
    status: str
    previous_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    previous_held_balance: Annotated[Decimal, DecimalWire()]
    new_held_balance: Annotated[Decimal, DecimalWire()]
    previous_available_balance: Annotated[Decimal, DecimalWire()]
    new_available_balance: Annotated[Decimal, DecimalWire()]
    provider_payment_reference: str
    provider_payload_hash: str
    transaction_id: str
    transaction_external_id: str
    idempotent_replay: bool = Field(default=False)


class EconomyWalletBalanceDescribeRequest(BaseModel):
    # Attributes
    operation: str = Field(default="describe_wallet_balance")
    actor_id: str | None = Field(default=None)
    wallet_id: str
    coin_id: str


class EconomyWalletBalanceDescribeResponse(BaseModel):
    # Attributes
    operation: str = Field(default="describe_wallet_balance")
    wallet_balance_id: str
    wallet_id: str
    coin_id: str
    balance: Annotated[Decimal, DecimalWire()]
    held_balance: Annotated[Decimal, DecimalWire()]
    available_balance: Annotated[Decimal, DecimalWire()]
    ready: bool
    last_transaction_id: str | None = Field(default=None)


class EconomyWalletCapitalBalanceSummary(BaseModel):
    # Attributes
    wallet_balance_id: str
    wallet_id: str
    wallet_public_id: str | None = Field(default=None)
    finance_entity_id: str | None = Field(default=None)
    coin_id: str
    balance: Annotated[Decimal, DecimalWire()]
    held_balance: Annotated[Decimal, DecimalWire()]
    available_balance: Annotated[Decimal, DecimalWire()]


class EconomyWalletCapitalFundingProviderSummary(BaseModel):
    # Attributes
    provider_config_id: str
    provider_route_id: str
    provider_finance_entity_id: str
    provider_key: str
    label: str | None = Field(default=None)
    route_key: str
    target_coin_id: str
    external_currency: str
    external_minor_unit_exponent: int
    conversion_mode: str
    min_external_amount_minor: int | None = Field(default=None)
    max_external_amount_minor: int | None = Field(default=None)
    status: str


class EconomyWalletCapitalConversionQuoteSummary(BaseModel):
    # Attributes
    capital_conversion_quote_id: str
    provider_route_id: str
    target_coin_id: str
    external_amount_minor: int
    external_currency: str
    target_amount: Annotated[Decimal, DecimalWire()]
    conversion_mode: str
    quote_source: str
    quote_hash: str
    quote_captured_at: str
    quote_expires_at: str | None = Field(default=None)


class EconomyWalletCapitalTransactionIntentSummary(BaseModel):
    # Attributes
    transaction_intent_id: str
    provider_config_id: str
    recipient_finance_entity_id: str
    recipient_wallet_id: str
    recipient_wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    funding_intent_key: str
    idempotency_key: str
    provider_key: str
    status: str
    created_at: str
    updated_at: str | None = Field(default=None)
    capital_conversion_quote: EconomyWalletCapitalConversionQuoteSummary


class EconomyWalletCapitalTransactionExternalSummary(BaseModel):
    # Attributes
    transaction_external_id: str
    transaction_id: str
    transaction_intent_id: str
    provider_config_id: str
    capital_conversion_quote_id: str
    provider_finance_entity_id: str
    provider_key: str
    provider_event_id: str
    provider_public_reference: str
    provider_payload_hash: str
    external_amount_minor: int
    external_currency: str
    quote_hash: str
    idempotency_key: str
    status: str
    processed_at: str | None = Field(default=None)
    external_created_at: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default=None)


class EconomyWalletCapitalTransactionSummary(BaseModel):
    # Attributes
    transaction_id: str
    source_wallet_public_id: str
    target_wallet_public_id: str
    coin_id: str
    coin_amount: Annotated[Decimal, DecimalWire()]
    gas_price: Annotated[Decimal, DecimalWire()]
    nonce: int
    status: str
    transaction_hash: str
    idempotency_key: str | None = Field(default=None)
    description: str | None = Field(default=None)
    confirmed_at: str | None = Field(default=None)
    source_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    target_previous_coin_balance: Annotated[Decimal, DecimalWire()] | None = Field(default=None)


class EconomyWalletCapitalReservationSummary(BaseModel):
    # Attributes
    reservation_id: str
    smart_contract_permit_id: str
    escrow_id: str | None = Field(default=None)
    rate_snapshot_id: str
    op_nonce: int
    args_hash: str
    max_cost: Annotated[Decimal, DecimalWire()]
    final_cost: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    status: str
    deadline: str | None = Field(default=None)


class EconomyWalletCapitalEscrowSummary(BaseModel):
    # Attributes
    escrow_id: str
    wallet_public_id: str
    coin_id: str
    locked_amount: Annotated[Decimal, DecimalWire()]
    op_nonce: int
    escrow_hash: str
    smart_contract_reservation_id: str
    status: str
    description: str | None = Field(default=None)


class EconomyWalletCapitalSettlementSummary(BaseModel):
    # Attributes
    settlement_id: str
    smart_contract_reservation_id: str
    payer_finance_entity_id: str
    payer_wallet_public_id: str
    receiver_finance_entity_id: str
    receiver_wallet_public_id: str
    coin_id: str
    final_cost: Annotated[Decimal, DecimalWire()]
    status: str


class EconomyWalletCapitalProviderLifecycleSummary(BaseModel):
    # Attributes
    provider_lifecycle_receipt_id: str
    provider_finance_entity_id: str
    provider_key: str
    provider_event_id: str
    provider_lifecycle_object_id: str
    provider_lifecycle_effect_key: str
    idempotency_key: str
    wallet_finance_entity_id: str
    wallet_id: str
    wallet_public_id: str
    coin_id: str
    amount: Annotated[Decimal, DecimalWire()]
    event_kind: str
    status: str
    previous_balance: Annotated[Decimal, DecimalWire()]
    new_balance: Annotated[Decimal, DecimalWire()]
    previous_held_balance: Annotated[Decimal, DecimalWire()]
    new_held_balance: Annotated[Decimal, DecimalWire()]
    previous_available_balance: Annotated[Decimal, DecimalWire()]
    new_available_balance: Annotated[Decimal, DecimalWire()]
    provider_payment_reference: str
    provider_payload_hash: str
    transaction_id: str
    transaction_external_id: str
    processed_at: str | None = Field(default=None)
    external_created_at: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default=None)


class EconomyWalletCapitalFrameResolveRequest(BaseModel):
    # Attributes
    operation: str = Field(default="resolve_wallet_capital_frame")
    actor_id: str | None = Field(default=None)
    wallet_id: str
    coin_id: str | None = Field(default=None)
    limit: int = Field(default=50)
    include_transaction_intents: bool = Field(default=True)
    include_funding_providers: bool = Field(default=True)
    include_transaction_externals: bool = Field(default=True)
    include_transactions: bool = Field(default=True)
    include_reservations: bool = Field(default=True)
    include_escrows: bool = Field(default=True)
    include_settlements: bool = Field(default=True)
    include_provider_lifecycle: bool = Field(default=True)


class EconomyWalletCapitalFrameResolveResponse(BaseModel):
    # Attributes
    operation: str = Field(default="resolve_wallet_capital_frame")
    wallet_id: str
    wallet_public_id: str | None = Field(default=None)
    finance_entity_id: str | None = Field(default=None)
    coin_id: str | None = Field(default=None)
    ready: bool = Field(default=False)
    balances: list[EconomyWalletCapitalBalanceSummary] = Field(default_factory=list)
    funding_providers: list[EconomyWalletCapitalFundingProviderSummary] = Field(default_factory=list)
    transaction_intents: list[EconomyWalletCapitalTransactionIntentSummary] = Field(default_factory=list)
    transaction_externals: list[EconomyWalletCapitalTransactionExternalSummary] = Field(default_factory=list)
    transactions: list[EconomyWalletCapitalTransactionSummary] = Field(default_factory=list)
    reservations: list[EconomyWalletCapitalReservationSummary] = Field(default_factory=list)
    escrows: list[EconomyWalletCapitalEscrowSummary] = Field(default_factory=list)
    settlements: list[EconomyWalletCapitalSettlementSummary] = Field(default_factory=list)
    provider_lifecycle_receipts: list[EconomyWalletCapitalProviderLifecycleSummary] = Field(default_factory=list)
    activity_count: int = Field(default=0)
    info: str | None = Field(default=None)


class EconomyWalletCapitalViewStateResolveRequest(BaseModel):
    # Attributes
    operation: str = Field(default="resolve_wallet_capital_view_state")
    actor_id: str | None = Field(default=None)
    wallet_id: str
    coin_id: str | None = Field(default=None)
    limit: int = Field(default=50)
    include_transaction_intents: bool = Field(default=True)
    include_transaction_externals: bool = Field(default=True)
    include_transactions: bool = Field(default=True)
    include_reservations: bool = Field(default=True)
    include_escrows: bool = Field(default=True)
    include_settlements: bool = Field(default=True)
    include_provider_lifecycle: bool = Field(default=True)


class EconomyPriceReservationReserveRequest(BaseModel):
    # Attributes
    operation: str = Field(default="price_reservation_reserve")
    actor_id: str | None = Field(default=None)
    price_id: str
    request_hash: str
    operation_key: str
    pricing_policy_id: str | None = Field(default=None)
    upper_bound_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    cost_basis_coin_id: str | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)


class EconomyPriceReservationReserveResponse(BaseModel):
    # Attributes
    operation: str = Field(default="price_reservation_reserve")
    price_id: str
    price_schedule_id: str
    rate_snapshot_id: str
    price_reservation_id: str
    quoted_amount: Annotated[Decimal, DecimalWire()]
    cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_percentage: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)
    status: str


class EconomyPriceReservationFinalizeRequest(BaseModel):
    # Attributes
    operation: str = Field(default="price_reservation_finalize")
    actor_id: str | None = Field(default=None)
    price_reservation_id: str
    status: str
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    cost_basis_coin_id: str | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)


class EconomyPriceReservationFinalizeResponse(BaseModel):
    # Attributes
    operation: str = Field(default="price_reservation_finalize")
    price_reservation_id: str
    status: str
    final_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_cost_basis_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    actual_markup_amount: Annotated[Decimal, DecimalWire()] | None = Field(default=None)
    meter_evidence_ref: str | None = Field(default=None)


class EconomyServiceOperationPermitEnsureRequest(BaseModel):
    # Attributes
    operation: str = Field(default="ensure_service_operation_permit")
    actor_id: str | None = Field(default=None)
    finance_role_key: str = Field(default="primary")
    smart_contract_id: str
    price_schedule_id: str
    coin_id: str
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: str


class EconomyServiceOperationPermitEnsureResponse(BaseModel):
    # Attributes
    operation: str = Field(default="ensure_service_operation_permit")
    actor_id: str
    finance_role_key: str
    smart_contract_id: str
    permit_id: str
    parent_permit_id: str | None = Field(default=None)
    permit_nonce: int
    finance_entity_id: str
    wallet_id: str
    wallet_public_id: str
    price_schedule_id: str
    coin_id: str
    cap_amount: Annotated[Decimal, DecimalWire()]
    expires_at: str
    status: str
    refreshed: bool = Field(default=False)
    idempotent_replay: bool = Field(default=False)


class EconomySmartContractReservationPrepareRequest(BaseModel):
    # Attributes
    operation: str = Field(default="prepare_smart_contract_reservation")
    actor_id: str | None = Field(default=None)
    smart_contract_id: str
    permit_id: str
    permit_nonce: int
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    args_hash: str
    max_cost: Annotated[Decimal, DecimalWire()]
    rate_snapshot_id: str
    deadline: str
    coin_id: str


class EconomySmartContractReservationPrepareResponse(BaseModel):
    # Attributes
    operation: str = Field(default="prepare_smart_contract_reservation")
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    escrow_id: str
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    op_nonce: int
    coin_id: str
    max_cost: Annotated[Decimal, DecimalWire()]
    payer_balance: Annotated[Decimal, DecimalWire()]
    payer_held_balance: Annotated[Decimal, DecimalWire()]
    payer_available_balance: Annotated[Decimal, DecimalWire()]
    status: str
    idempotent_replay: bool = Field(default=False)


class EconomySmartContractReservationReleaseRequest(BaseModel):
    # Attributes
    operation: str = Field(default="release_smart_contract_reservation")
    actor_id: str | None = Field(default=None)
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    coin_id: str
    status: str


class EconomySmartContractReservationReleaseResponse(BaseModel):
    # Attributes
    operation: str = Field(default="release_smart_contract_reservation")
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    escrow_id: str
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    payer_wallet_balance_id: str
    coin_id: str
    released_amount: Annotated[Decimal, DecimalWire()]
    payer_balance: Annotated[Decimal, DecimalWire()]
    payer_previous_held_balance: Annotated[Decimal, DecimalWire()]
    payer_new_held_balance: Annotated[Decimal, DecimalWire()]
    payer_previous_available_balance: Annotated[Decimal, DecimalWire()]
    payer_new_available_balance: Annotated[Decimal, DecimalWire()]
    status: str
    idempotent_replay: bool = Field(default=False)


class EconomySmartContractSettlementFinalizeRequest(BaseModel):
    # Attributes
    operation: str = Field(default="finalize_smart_contract_settlement")
    actor_id: str | None = Field(default=None)
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    receiver_finance_entity_id: str
    receiver_wallet_id: str
    receiver_wallet_public_id: str
    coin_id: str
    final_cost: Annotated[Decimal, DecimalWire()]


class EconomySmartContractSettlementFinalizeResponse(BaseModel):
    # Attributes
    operation: str = Field(default="finalize_smart_contract_settlement")
    smart_contract_id: str
    permit_id: str
    reservation_id: str
    settlement_id: str
    transaction_id: str | None = Field(default=None)
    payer_finance_entity_id: str
    payer_wallet_id: str
    payer_wallet_public_id: str
    payer_wallet_balance_id: str
    payer_previous_balance: Annotated[Decimal, DecimalWire()]
    payer_new_balance: Annotated[Decimal, DecimalWire()]
    payer_previous_held_balance: Annotated[Decimal, DecimalWire()]
    payer_new_held_balance: Annotated[Decimal, DecimalWire()]
    payer_previous_available_balance: Annotated[Decimal, DecimalWire()]
    payer_new_available_balance: Annotated[Decimal, DecimalWire()]
    receiver_finance_entity_id: str
    receiver_wallet_id: str
    receiver_wallet_public_id: str
    receiver_wallet_balance_id: str
    receiver_previous_balance: Annotated[Decimal, DecimalWire()]
    receiver_new_balance: Annotated[Decimal, DecimalWire()]
    coin_id: str
    final_cost: Annotated[Decimal, DecimalWire()]
    status: str
    idempotent_replay: bool = Field(default=False)
