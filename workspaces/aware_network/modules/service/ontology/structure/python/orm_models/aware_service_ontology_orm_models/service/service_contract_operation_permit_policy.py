from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import (
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
)


class ServiceContractOperationPermitPolicy(ORMModel):
    # Attributes
    fail_closed: bool = Field(default=True)
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = Field(
        default=ServiceContractOperationPermitIdempotencyScope.request_hash
    )
    permit_scope: ServiceContractOperationPermitScope = Field(default=ServiceContractOperationPermitScope.operation)
    requires_active_contract: bool = Field(default=True)
    requires_reservation_before_execute: bool = Field(default=False)
    requires_smart_contract_permit: bool = Field(default=False)

    # Foreign Keys
    service_contract_config_operation_grant_id: UUID | None = Field(
        default=None, description="Foreign key for ServiceContractConfigOperationGrant.permit_policy"
    )
