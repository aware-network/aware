from __future__ import annotations

from aware_service_runtime.host_contract import empty_success_contract_response
from aware_service_service_dto.host import (
    ServiceHostContractRequest,
    ServiceHostContractResponse,
)


def resolve_service_host_contract(
    request: ServiceHostContractRequest,
) -> ServiceHostContractResponse:
    return empty_success_contract_response(
        request=request,
        provider_key="aware-environment-service",
        description=(
            "Environment service does not claim ontology authority DB schema; "
            "it owns routing/session pointer state only."
        ),
    )
