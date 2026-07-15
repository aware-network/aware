from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationPriceSource,
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service_contract_operation_price_policy import ServiceContractOperationPricePolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.pricing_policy import PricingPolicy
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.stable_ids import (
    stable_service_contract_operation_price_policy_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_contract_config_operation_grant(
    service_contract_config_operation_grant_id: UUID,
    price_source: ServiceContractOperationPriceSource = ServiceContractOperationPriceSource.operation_default,
    price_id: UUID | None = None,
    price_ref: str | None = None,
    pricing_policy_id: UUID | None = None,
    pricing_policy_ref: str | None = None,
    settlement_policy_override: ServiceOperationSettlementPolicy | None = None,
    max_cost_required: bool = False,
    quote_ttl_s: int | None = None,
    fail_closed: bool = True,
) -> ServiceContractOperationPricePolicy:
    """
    Creates the Service-owned price selection policy intent for one operation grant.

    Contract:
    - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
    - Price policy selects Economy price truth; it does not compute quotes or settle funds.
    - Economy owns Price, PricingPolicy, PriceSchedule, RateSnapshot, reservation, escrow, and
    settlement receipts.
    """

    # --- AWARE: LOGIC START build_via_service_contract_config_operation_grant
    policy_id = stable_service_contract_operation_price_policy_id(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id
    )
    session = current_handler_session()
    _ = session.imap_get(ServiceContractConfigOperationGrant, service_contract_config_operation_grant_id)
    if price_id is not None:
        _ = session.imap_get(Price, price_id)
    if pricing_policy_id is not None:
        _ = session.imap_get(PricingPolicy, pricing_policy_id)

    existing = session.imap_get(ServiceContractOperationPricePolicy, policy_id)
    if existing is not None:
        if existing.service_contract_config_operation_grant_id != service_contract_config_operation_grant_id:
            raise RuntimeError(
                "ServiceContractOperationPricePolicy payload mismatch for existing policy: "
                + f"service_contract_operation_price_policy_id={policy_id}"
            )
        existing.price_source = price_source
        existing.price_id = price_id
        existing.price_ref = price_ref
        existing.pricing_policy_id = pricing_policy_id
        existing.pricing_policy_ref = pricing_policy_ref
        existing.settlement_policy_override = settlement_policy_override
        existing.max_cost_required = bool(max_cost_required)
        existing.quote_ttl_s = quote_ttl_s
        existing.fail_closed = bool(fail_closed)
        return existing

    created = ServiceContractOperationPricePolicy(
        id=policy_id,
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id,
        price_source=price_source,
        price_id=price_id,
        price_ref=price_ref,
        pricing_policy_id=pricing_policy_id,
        pricing_policy_ref=pricing_policy_ref,
        settlement_policy_override=settlement_policy_override,
        max_cost_required=bool(max_cost_required),
        quote_ttl_s=quote_ttl_s,
        fail_closed=bool(fail_closed),
    )
    session.imap_add(created)
    return created
    # --- AWARE: LOGIC END build_via_service_contract_config_operation_grant
