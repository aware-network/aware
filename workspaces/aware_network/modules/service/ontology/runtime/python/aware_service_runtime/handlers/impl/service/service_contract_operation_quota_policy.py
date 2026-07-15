from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationQuotaOverLimitBehavior,
    ServiceContractOperationQuotaUnit,
    ServiceContractOperationQuotaWindow,
)
from aware_service_ontology.service.service_contract_operation_quota_policy import ServiceContractOperationQuotaPolicy

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.stable_ids import (
    stable_service_contract_operation_quota_policy_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_contract_config_operation_grant(
    service_contract_config_operation_grant_id: UUID,
    unit: ServiceContractOperationQuotaUnit = ServiceContractOperationQuotaUnit.operation,
    limit_amount: int | None = None,
    window: ServiceContractOperationQuotaWindow = ServiceContractOperationQuotaWindow.none,
    burst_limit: int | None = None,
    over_limit_behavior: ServiceContractOperationQuotaOverLimitBehavior = ServiceContractOperationQuotaOverLimitBehavior.deny,
    fail_closed: bool = True,
) -> ServiceContractOperationQuotaPolicy:
    """
    Creates the Service-owned quota policy intent for one operation grant.

    Contract:
    - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
    - Quota policy declares usage allowance intent only.
    - Metering, billing, and financial settlement remain downstream runtime/Economy concerns.
    """

    # --- AWARE: LOGIC START build_via_service_contract_config_operation_grant
    policy_id = stable_service_contract_operation_quota_policy_id(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id
    )
    session = current_handler_session()
    _ = session.imap_get(ServiceContractConfigOperationGrant, service_contract_config_operation_grant_id)

    existing = session.imap_get(ServiceContractOperationQuotaPolicy, policy_id)
    if existing is not None:
        if existing.service_contract_config_operation_grant_id != service_contract_config_operation_grant_id:
            raise RuntimeError(
                "ServiceContractOperationQuotaPolicy payload mismatch for existing policy: "
                + f"service_contract_operation_quota_policy_id={policy_id}"
            )
        existing.unit = unit
        existing.limit_amount = limit_amount
        existing.window = window
        existing.burst_limit = burst_limit
        existing.over_limit_behavior = over_limit_behavior
        existing.fail_closed = bool(fail_closed)
        return existing

    created = ServiceContractOperationQuotaPolicy(
        id=policy_id,
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id,
        unit=unit,
        limit_amount=limit_amount,
        window=window,
        burst_limit=burst_limit,
        over_limit_behavior=over_limit_behavior,
        fail_closed=bool(fail_closed),
    )
    session.imap_add(created)
    return created
    # --- AWARE: LOGIC END build_via_service_contract_config_operation_grant
