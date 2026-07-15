from __future__ import annotations

from aware_service_runtime.host_contract import (
    ontology_authority_db_requirement,
)
from aware_service_service_dto.host import (
    ServiceHostContractCapabilityKey,
    ServiceHostContractRequest,
    ServiceHostContractResponse,
    ServiceHostContractStatus,
    ServiceHostDbRequirementPlan,
    ServiceHostRuntimeRequirementReceipt,
)


def resolve_service_host_contract(
    request: ServiceHostContractRequest,
) -> ServiceHostContractResponse:
    requirement = ontology_authority_db_requirement(
        request=request,
        provider_key="aware-ontology-service",
    )
    requirements = [] if requirement is None else [requirement]
    return ServiceHostContractResponse(
        request_id=request.request_id,
        status=ServiceHostContractStatus.succeeded,
        capabilities=request.capabilities,
        db_requirement_plan=ServiceHostDbRequirementPlan(requirements=requirements),
        receipts=[
            ServiceHostRuntimeRequirementReceipt(
                capability_key=ServiceHostContractCapabilityKey.db_requirements,
                status=ServiceHostContractStatus.succeeded,
                requirement_kind=requirement.kind if requirement is not None else None,
                requirement_count=len(requirements),
                installed_count=0,
                skipped_count=0,
                evidence={
                    "provider_key": "aware-ontology-service",
                    "authority_package_names": (
                        [] if requirement is None else requirement.package_names
                    ),
                },
            )
        ],
        metadata={"provider_key": "aware-ontology-service"},
    )
