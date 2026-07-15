from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
)
from aware_service_ontology.service.service_contract_operation_permit_policy import ServiceContractOperationPermitPolicy

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
    stable_service_contract_operation_permit_policy_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_contract_config_operation_grant(
    service_contract_config_operation_grant_id: UUID,
    requires_active_contract: bool = True,
    requires_smart_contract_permit: bool = False,
    requires_reservation_before_execute: bool = False,
    permit_scope: ServiceContractOperationPermitScope = ServiceContractOperationPermitScope.operation,
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = ServiceContractOperationPermitIdempotencyScope.request_hash,
    fail_closed: bool = True,
) -> ServiceContractOperationPermitPolicy:
    """
    Creates the Service-owned permit policy intent for one operation grant.

    Contract:
    - Parent ServiceContractConfigOperationGrant scope is propagated by constructor lowering.
    - Permit policy declares required execution proofs before an operation may run.
    - Identity still owns ActorRole evidence; Economy still owns smart-contract permits and
    reservations.
    """

    # --- AWARE: LOGIC START build_via_service_contract_config_operation_grant
    policy_id = stable_service_contract_operation_permit_policy_id(
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id
    )
    session = current_handler_session()
    _ = session.imap_get(ServiceContractConfigOperationGrant, service_contract_config_operation_grant_id)

    existing = session.imap_get(ServiceContractOperationPermitPolicy, policy_id)
    if existing is not None:
        if existing.service_contract_config_operation_grant_id != service_contract_config_operation_grant_id:
            raise RuntimeError(
                "ServiceContractOperationPermitPolicy payload mismatch for existing policy: "
                + f"service_contract_operation_permit_policy_id={policy_id}"
            )
        existing.requires_active_contract = bool(requires_active_contract)
        existing.requires_smart_contract_permit = bool(requires_smart_contract_permit)
        existing.requires_reservation_before_execute = bool(requires_reservation_before_execute)
        existing.permit_scope = permit_scope
        existing.idempotency_scope = idempotency_scope
        existing.fail_closed = bool(fail_closed)
        return existing

    created = ServiceContractOperationPermitPolicy(
        id=policy_id,
        service_contract_config_operation_grant_id=service_contract_config_operation_grant_id,
        requires_active_contract=bool(requires_active_contract),
        requires_smart_contract_permit=bool(requires_smart_contract_permit),
        requires_reservation_before_execute=bool(requires_reservation_before_execute),
        permit_scope=permit_scope,
        idempotency_scope=idempotency_scope,
        fail_closed=bool(fail_closed),
    )
    session.imap_add(created)
    return created
    # --- AWARE: LOGIC END build_via_service_contract_config_operation_grant
