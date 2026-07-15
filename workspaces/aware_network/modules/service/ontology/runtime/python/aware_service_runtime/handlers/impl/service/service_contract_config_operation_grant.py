from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
    ServiceContractOperationPriceSource,
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service_contract_config_operation_grant import ServiceContractConfigOperationGrant
from aware_service_ontology.service.service_contract_operation_permit_policy import ServiceContractOperationPermitPolicy
from aware_service_ontology.service.service_contract_operation_price_policy import ServiceContractOperationPricePolicy
from aware_service_ontology.service.service_contract_operation_quota_policy import ServiceContractOperationQuotaPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.stable_ids import (
    stable_service_contract_config_operation_grant_id,
)

# --- AWARE: USER_IMPORTS END


async def configure_quota_policy(
    service_contract_config_operation_grant: ServiceContractConfigOperationGrant,
    unit: ServiceContractOperationQuotaUnit = ServiceContractOperationQuotaUnit.operation,
    limit_amount: int | None = None,
    window: ServiceContractOperationQuotaWindow = ServiceContractOperationQuotaWindow.none,
    burst_limit: int | None = None,
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = ServiceContractOperationQuotaOverLimitBehavior.deny,
    fail_closed: bool = True,
) -> ServiceContractOperationQuotaPolicy:
    """
    Declares typed quota policy intent for this operation grant.

    Contract:
    - This controls allowance semantics only.
    - Runtime metering/billing may consume this policy, but Economy owns financial receipts.
    """

    # --- AWARE: LOGIC START configure_quota_policy
    created = await ServiceContractOperationQuotaPolicy.build_via_service_contract_config_operation_grant(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant.id,
        unit=unit,
        limit_amount=limit_amount,
        window=window,
        burst_limit=burst_limit,
        over_limit_behavior=over_limit_behavior,
        fail_closed=fail_closed,
    )
    service_contract_config_operation_grant.quota_policy = created
    return created
    # --- AWARE: LOGIC END configure_quota_policy


async def configure_permit_policy(
    service_contract_config_operation_grant: ServiceContractConfigOperationGrant,
    requires_active_contract: bool = True,
    requires_smart_contract_permit: bool = False,
    requires_reservation_before_execute: bool = False,
    permit_scope: ServiceContractOperationPermitScope = ServiceContractOperationPermitScope.operation,
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = ServiceContractOperationPermitIdempotencyScope.request_hash,
    fail_closed: bool = True,
) -> ServiceContractOperationPermitPolicy:
    """
    Declares typed permit policy intent for this operation grant.

    Contract:
    - This controls pre-execution proof requirements.
    - Identity role evidence and Economy smart-contract receipts remain owned by their source domains.
    """

    # --- AWARE: LOGIC START configure_permit_policy
    created = await ServiceContractOperationPermitPolicy.build_via_service_contract_config_operation_grant(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant.id,
        requires_active_contract=requires_active_contract,
        requires_smart_contract_permit=requires_smart_contract_permit,
        requires_reservation_before_execute=requires_reservation_before_execute,
        permit_scope=permit_scope,
        idempotency_scope=idempotency_scope,
        fail_closed=fail_closed,
    )
    service_contract_config_operation_grant.permit_policy = created
    return created
    # --- AWARE: LOGIC END configure_permit_policy


async def configure_price_policy(
    service_contract_config_operation_grant: ServiceContractConfigOperationGrant,
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
    Declares typed price selection policy intent for this operation grant.

    Contract:
    - This selects or overrides Economy price truth for the granted operation.
    - Quotes, reservations, escrow, and settlement remain Economy-owned receipts.
    """

    # --- AWARE: LOGIC START configure_price_policy
    created = await ServiceContractOperationPricePolicy.build_via_service_contract_config_operation_grant(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant.id,
        price_source=price_source,
        price_id=price_id,
        price_ref=price_ref,
        pricing_policy_id=pricing_policy_id,
        pricing_policy_ref=pricing_policy_ref,
        settlement_policy_override=settlement_policy_override,
        max_cost_required=max_cost_required,
        quote_ttl_s=quote_ttl_s,
        fail_closed=fail_closed,
    )
    service_contract_config_operation_grant.price_policy = created
    return created
    # --- AWARE: LOGIC END configure_price_policy


async def build_via_service_contract_config(
    service_contract_config_id: UUID,
    service_operation_config_id: UUID,
    access_scope: str = "operation",
    quota_policy_json: JsonObject | None = JsonObject(),
    permit_policy_json: JsonObject | None = JsonObject(),
    price_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ServiceContractConfigOperationGrant:
    """
    Creates one reusable operation grant under a ServiceContractConfig.

    Contract:
    - Parent ServiceContractConfig scope is propagated by constructor lowering.
    - Stable identity is one grant per ServiceOperationConfig under a ServiceContractConfig.
    - Quota, permit, and price policies are Service-side config snapshots; Economy owns execution
    receipts.
    - JSON policy attributes are compatibility mirrors; typed child policy objects are canonical.
    """

    # --- AWARE: LOGIC START build_via_service_contract_config
    access_scope_norm = (access_scope or "").strip() or "operation"
    quota_policy = cast(JsonObject, dict(quota_policy_json or {}))
    permit_policy = cast(JsonObject, dict(permit_policy_json or {}))
    price_policy = cast(JsonObject, dict(price_policy_json or {}))
    grant_id = stable_service_contract_config_operation_grant_id(
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
    )
    session = current_handler_session()

    service_contract_config = session.imap_get(ServiceContractConfig, service_contract_config_id)
    service_operation_config = session.imap_get(ServiceOperationConfig, service_operation_config_id)
    if (
        service_contract_config is not None
        and service_operation_config is not None
        and service_contract_config.service_config_id != service_operation_config.service_config_id
    ):
        raise RuntimeError(
            "ServiceContractConfigOperationGrant service_operation_config does not belong to "
            + "the ServiceContractConfig parent ServiceConfig: "
            + f"service_contract_config_id={service_contract_config_id} "
            + f"service_operation_config_id={service_operation_config_id}"
        )

    existing = session.imap_get(ServiceContractConfigOperationGrant, grant_id)
    if existing is not None:
        if (
            existing.service_contract_config_id != service_contract_config_id
            or existing.service_operation_config_id != service_operation_config_id
        ):
            raise RuntimeError(
                "ServiceContractConfigOperationGrant payload mismatch for existing grant: " + f"grant_id={grant_id}"
            )
        existing.access_scope = access_scope_norm
        existing.quota_policy_json = quota_policy
        existing.permit_policy_json = permit_policy
        existing.price_policy_json = price_policy
        existing.description = description
        return existing

    return ServiceContractConfigOperationGrant(
        id=grant_id,
        service_contract_config_id=service_contract_config_id,
        service_operation_config_id=service_operation_config_id,
        access_scope=access_scope_norm,
        quota_policy_json=quota_policy,
        permit_policy_json=permit_policy,
        price_policy_json=price_policy,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_contract_config
