from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import (
    ServiceContractOperationPermitIdempotencyScope,
    ServiceContractOperationPermitScope,
)


class ServiceContractOperationPermitPolicy(BaseModel):
    # Attributes
    fail_closed: bool = Field(default=True)
    idempotency_scope: ServiceContractOperationPermitIdempotencyScope = Field(
        default=ServiceContractOperationPermitIdempotencyScope.request_hash
    )
    permit_scope: ServiceContractOperationPermitScope = Field(default=ServiceContractOperationPermitScope.operation)
    requires_active_contract: bool = Field(default=True)
    requires_reservation_before_execute: bool = Field(default=False)
    requires_smart_contract_permit: bool = Field(default=False)
