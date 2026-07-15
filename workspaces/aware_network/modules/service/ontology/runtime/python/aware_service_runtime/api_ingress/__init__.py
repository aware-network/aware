from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

_MODULE_EXPORTS: dict[str, tuple[str, ...]] = {
    ".access": (
        "GRANTING_SUBSCRIPTION_STATUSES",
        "ServiceAccessDecisionReason",
        "ServiceAccessEvidence",
        "ServiceContractOperationPermitPolicySummary",
        "ServiceContractOperationPolicySummary",
        "ServiceContractOperationPricePolicySummary",
        "ServiceContractOperationQuotaPolicySummary",
        "build_service_contract_operation_access_evidence",
        "build_service_contract_operation_policy_summary",
        "build_service_subscription_access_evidence",
        "resolve_service_contract_operation_access_evidence",
        "resolve_service_subscription_access_evidence",
    ),
    ".admission_context": (
        "ServiceActorContext",
        "ServiceContractAccessContextRef",
        "ServiceOperationAdmissionContext",
        "ServiceParticipantAdmission",
        "ServiceSessionScope",
        "build_service_participant_admission",
        "normalize_service_operation_admission_context",
        "service_actor_context_payload",
        "service_contract_access_context_ref_payload",
        "service_operation_admission_context_payload",
        "service_participant_admission_blocking_reasons",
        "service_participant_admission_payload",
        "service_session_scope_payload",
    ),
    ".contract_access_context": (
        "ResolvedServiceContractAccessContext",
        "ServiceContractAccessContextBootstrapReadModel",
        "ServiceContractAccessContextResolution",
        "ServiceOperationAccessContext",
        "read_service_contract_access_context_bootstrap",
        "resolve_service_contract_access_context_from_admission",
        "service_contract_access_context_bootstrap_payload",
        "service_contract_access_context_resolution_payload",
    ),
    ".dispatch": (
        "ResolvedServiceApiDispatch",
        "ResolvedServiceApiDispatchCandidate",
        "require_single_service_api_dispatch_candidate",
        "resolve_service_api_dispatch",
    ),
    ".economy_settlement": (
        "ServiceOperationEconomyFinalizationInput",
        "ServiceOperationEconomyReservationInput",
        "ServiceOperationEconomySettlementAdapter",
        "ServiceOperationEconomySettlementCoordinator",
        "build_service_operation_economy_finalization_input",
        "build_service_operation_economy_reservation_input",
        "build_service_operation_economy_settlement_coordinator",
    ),
    ".execution_context": (
        "LegacyCallbackServiceApiExecutionBackend",
        "LegacyServiceApiExecutionCallback",
        "MissingServiceApiExecutionBackend",
        "ServiceApiExecutionBackend",
        "ServiceApiExecutionBackendMode",
        "build_service_api_execution_backend",
    ),
    ".execution": (
        "ServiceActorRoleEvidence",
        "ServiceApiActorRoleEvidence",
        "ServiceApiDispatchPreflightResult",
        "ServiceApiDispatchReceiptPolicy",
        "ServiceOperationAdmissionDenied",
        "ServiceApiOperationAccessContext",
        "ServiceActorRoleRequirementReadModel",
        "ServiceOperationContractAdmissionReadModel",
        "ServiceOperationPreflightResult",
        "read_service_operation_contract_admission",
        "service_operation_admission_blocked_payload",
        "validate_service_api_dispatch_preflight",
        "validate_service_operation_preflight",
    ),
    ".gateway_execution": (
        "GatewayBackedServiceApiExecutionBackend",
        "build_gateway_service_api_execution_backend",
    ),
    ".graph_execution": (
        "ServiceApiGraphExecutionBinding",
        "ServiceApiGraphExecutionPlan",
        "build_service_api_graph_execution_plan",
    ),
    ".fulfillment": (
        "ValidatedServiceApiFulfillmentBinding",
        "ValidatedServiceApiFulfillmentContract",
        "validate_service_api_fulfillment_contract",
    ),
    ".view_fulfillment": (
        "ServiceApiViewFulfillmentCandidate",
        "ServiceApiViewFulfillmentPlan",
        "resolve_service_api_view_fulfillment",
    ),
    ".view_protocol": (
        "ServiceViewProtocolBinding",
        "ServiceViewProtocolFulfillment",
        "build_service_view_protocol_bindings",
        "require_service_view_protocol_binding",
        "resolve_service_view_protocol_fulfillment",
    ),
}

_EXPORT_TO_MODULE: dict[str, str] = {
    export_name: module_name
    for module_name, export_names in _MODULE_EXPORTS.items()
    for export_name in export_names
}

__all__ = [
    "GRANTING_SUBSCRIPTION_STATUSES",
    "ResolvedServiceApiDispatch",
    "ResolvedServiceApiDispatchCandidate",
    "GatewayBackedServiceApiExecutionBackend",
    "LegacyCallbackServiceApiExecutionBackend",
    "LegacyServiceApiExecutionCallback",
    "MissingServiceApiExecutionBackend",
    "ServiceApiExecutionBackend",
    "ServiceApiExecutionBackendMode",
    "ServiceApiGraphExecutionBinding",
    "ServiceApiGraphExecutionPlan",
    "ServiceAccessDecisionReason",
    "ServiceAccessEvidence",
    "ServiceContractOperationPermitPolicySummary",
    "ServiceContractOperationPolicySummary",
    "ServiceContractOperationPricePolicySummary",
    "ServiceContractOperationQuotaPolicySummary",
    "ServiceActorContext",
    "ServiceActorRoleEvidence",
    "ServiceApiActorRoleEvidence",
    "ServiceApiDispatchPreflightResult",
    "ServiceApiDispatchReceiptPolicy",
    "ServiceOperationAdmissionDenied",
    "ServiceOperationAdmissionContext",
    "ServiceApiOperationAccessContext",
    "ServiceActorRoleRequirementReadModel",
    "ServiceOperationContractAdmissionReadModel",
    "ServiceOperationAccessContext",
    "ServiceContractAccessContextBootstrapReadModel",
    "ServiceContractAccessContextResolution",
    "ResolvedServiceContractAccessContext",
    "ServiceOperationPreflightResult",
    "ServiceContractAccessContextRef",
    "ServiceOperationEconomyFinalizationInput",
    "ServiceOperationEconomyReservationInput",
    "ServiceOperationEconomySettlementAdapter",
    "ServiceOperationEconomySettlementCoordinator",
    "ServiceParticipantAdmission",
    "ServiceSessionScope",
    "ServiceViewProtocolBinding",
    "ServiceViewProtocolFulfillment",
    "ValidatedServiceApiFulfillmentBinding",
    "ValidatedServiceApiFulfillmentContract",
    "ServiceApiViewFulfillmentCandidate",
    "ServiceApiViewFulfillmentPlan",
    "build_service_contract_operation_access_evidence",
    "build_service_contract_operation_policy_summary",
    "build_service_operation_economy_finalization_input",
    "build_service_operation_economy_reservation_input",
    "build_service_operation_economy_settlement_coordinator",
    "build_service_api_execution_backend",
    "build_gateway_service_api_execution_backend",
    "build_service_view_protocol_bindings",
    "resolve_service_contract_operation_access_evidence",
    "resolve_service_api_view_fulfillment",
    "resolve_service_view_protocol_fulfillment",
    "build_service_subscription_access_evidence",
    "build_service_participant_admission",
    "build_service_api_graph_execution_plan",
    "normalize_service_operation_admission_context",
    "require_service_view_protocol_binding",
    "resolve_service_subscription_access_evidence",
    "read_service_operation_contract_admission",
    "read_service_contract_access_context_bootstrap",
    "service_actor_context_payload",
    "service_contract_access_context_bootstrap_payload",
    "service_contract_access_context_ref_payload",
    "service_contract_access_context_resolution_payload",
    "service_operation_admission_context_payload",
    "service_operation_admission_blocked_payload",
    "service_participant_admission_blocking_reasons",
    "service_participant_admission_payload",
    "service_session_scope_payload",
    "validate_service_api_fulfillment_contract",
    "validate_service_api_dispatch_preflight",
    "validate_service_operation_preflight",
    "resolve_service_contract_access_context_from_admission",
    "require_single_service_api_dispatch_candidate",
    "resolve_service_api_dispatch",
]

if TYPE_CHECKING:
    from aware_service_runtime.api_ingress.access import (
        GRANTING_SUBSCRIPTION_STATUSES,
        ServiceAccessDecisionReason,
        ServiceAccessEvidence,
        ServiceContractOperationPermitPolicySummary,
        ServiceContractOperationPolicySummary,
        ServiceContractOperationPricePolicySummary,
        ServiceContractOperationQuotaPolicySummary,
        build_service_contract_operation_access_evidence,
        build_service_contract_operation_policy_summary,
        build_service_subscription_access_evidence,
        resolve_service_contract_operation_access_evidence,
        resolve_service_subscription_access_evidence,
    )
    from aware_service_runtime.api_ingress.admission_context import (
        ServiceActorContext,
        ServiceContractAccessContextRef,
        ServiceOperationAdmissionContext,
        ServiceParticipantAdmission,
        ServiceSessionScope,
        build_service_participant_admission,
        normalize_service_operation_admission_context,
        service_actor_context_payload,
        service_contract_access_context_ref_payload,
        service_operation_admission_context_payload,
        service_participant_admission_blocking_reasons,
        service_participant_admission_payload,
        service_session_scope_payload,
    )
    from aware_service_runtime.api_ingress.contract_access_context import (
        ResolvedServiceContractAccessContext,
        ServiceContractAccessContextBootstrapReadModel,
        ServiceContractAccessContextResolution,
        ServiceOperationAccessContext,
        read_service_contract_access_context_bootstrap,
        resolve_service_contract_access_context_from_admission,
        service_contract_access_context_bootstrap_payload,
        service_contract_access_context_resolution_payload,
    )
    from aware_service_runtime.api_ingress.dispatch import (
        ResolvedServiceApiDispatch,
        ResolvedServiceApiDispatchCandidate,
        require_single_service_api_dispatch_candidate,
        resolve_service_api_dispatch,
    )
    from aware_service_runtime.api_ingress.economy_settlement import (
        ServiceOperationEconomyFinalizationInput,
        ServiceOperationEconomyReservationInput,
        ServiceOperationEconomySettlementAdapter,
        ServiceOperationEconomySettlementCoordinator,
        build_service_operation_economy_finalization_input,
        build_service_operation_economy_reservation_input,
        build_service_operation_economy_settlement_coordinator,
    )
    from aware_service_runtime.api_ingress.execution_context import (
        LegacyCallbackServiceApiExecutionBackend,
        LegacyServiceApiExecutionCallback,
        MissingServiceApiExecutionBackend,
        ServiceApiExecutionBackend,
        ServiceApiExecutionBackendMode,
        build_service_api_execution_backend,
    )
    from aware_service_runtime.api_ingress.execution import (
        ServiceActorRoleEvidence,
        ServiceApiActorRoleEvidence,
        ServiceApiDispatchPreflightResult,
        ServiceApiDispatchReceiptPolicy,
        ServiceOperationAdmissionDenied,
        ServiceApiOperationAccessContext,
        ServiceActorRoleRequirementReadModel,
        ServiceOperationContractAdmissionReadModel,
        ServiceOperationPreflightResult,
        read_service_operation_contract_admission,
        service_operation_admission_blocked_payload,
        validate_service_api_dispatch_preflight,
        validate_service_operation_preflight,
    )
    from aware_service_runtime.api_ingress.fulfillment import (
        ValidatedServiceApiFulfillmentBinding,
        ValidatedServiceApiFulfillmentContract,
        validate_service_api_fulfillment_contract,
    )
    from aware_service_runtime.api_ingress.gateway_execution import (
        GatewayBackedServiceApiExecutionBackend,
        build_gateway_service_api_execution_backend,
    )
    from aware_service_runtime.api_ingress.graph_execution import (
        ServiceApiGraphExecutionBinding,
        ServiceApiGraphExecutionPlan,
        build_service_api_graph_execution_plan,
    )
    from aware_service_runtime.api_ingress.view_fulfillment import (
        ServiceApiViewFulfillmentCandidate,
        ServiceApiViewFulfillmentPlan,
        resolve_service_api_view_fulfillment,
    )
    from aware_service_runtime.api_ingress.view_protocol import (
        ServiceViewProtocolBinding,
        ServiceViewProtocolFulfillment,
        build_service_view_protocol_bindings,
        require_service_view_protocol_binding,
        resolve_service_view_protocol_fulfillment,
    )


def __getattr__(name: str) -> object:
    module_name = _EXPORT_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
