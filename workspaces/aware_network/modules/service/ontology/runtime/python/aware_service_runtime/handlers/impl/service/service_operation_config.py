from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service_operation_config import ServiceOperationConfig
from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint
from aware_service_ontology.service.service_operation_config_api_view import ServiceOperationConfigApiView
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_view import ApiView
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.stable_ids import (
    stable_service_operation_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create_api_endpoint(
    service_operation_config: ServiceOperationConfig,
    service_config_api_id: UUID,
    api_capability_endpoint_id: UUID,
    description: str | None = None,
) -> ServiceOperationConfigApiEndpoint:
    """
    Creates one config-level endpoint binding under this ServiceOperationConfig.
    """

    # --- AWARE: LOGIC START create_api_endpoint
    session = current_handler_session()

    service_config_api = session.imap_get(ServiceConfigApi, service_config_api_id)
    if (
        service_config_api is not None
        and service_config_api.service_config_id != service_operation_config.service_config_id
    ):
        raise RuntimeError(
            "ServiceOperationConfig.create_api_endpoint service_config_api does not belong to parent ServiceConfig: "
            + f"service_operation_config_id={service_operation_config.id} "
            + f"service_config_api_id={service_config_api_id}"
        )

    api_capability_endpoint = session.imap_get(ApiCapabilityEndpoint, api_capability_endpoint_id)
    if service_config_api is not None and api_capability_endpoint is not None:
        api_capability = session.imap_get(ApiCapability, api_capability_endpoint.api_capability_id)
        if api_capability is not None and api_capability.api_id != service_config_api.api_id:
            raise RuntimeError(
                "ServiceOperationConfig.create_api_endpoint api_capability_endpoint does not belong to "
                + "the ServiceConfigApi Api: "
                + f"service_operation_config_id={service_operation_config.id} "
                + f"api_capability_endpoint_id={api_capability_endpoint_id}"
            )

    created = await ServiceOperationConfigApiEndpoint.build_via_service_operation_config(
        service_operation_config_id=service_operation_config.id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        description=description,
    )
    for existing in service_operation_config.api_endpoints:
        if existing.id == created.id:
            return existing
    service_operation_config.api_endpoints.append(created)
    return created
    # --- AWARE: LOGIC END create_api_endpoint


async def create_api_view(
    service_operation_config: ServiceOperationConfig,
    service_config_api_id: UUID,
    api_view_id: UUID,
    description: str | None = None,
) -> ServiceOperationConfigApiView:
    """
    Creates one config-level API view fulfillment binding under this ServiceOperationConfig.

    Contract:
    - ApiView is the API-owned readable view-state contract.
    - This ServiceOperationConfig declares that this service operation fulfills the ApiView state
    contract.
    - Experience composes above ApiView and is not the Service operation target.
    - Runtime view DTOs must carry provenance and actor/access evidence before protected use.
    """

    # --- AWARE: LOGIC START create_api_view
    session = current_handler_session()

    service_config_api = session.imap_get(ServiceConfigApi, service_config_api_id)
    if (
        service_config_api is not None
        and service_config_api.service_config_id != service_operation_config.service_config_id
    ):
        raise RuntimeError(
            "ServiceOperationConfig.create_api_view service_config_api does not belong to parent ServiceConfig: "
            + f"service_operation_config_id={service_operation_config.id} "
            + f"service_config_api_id={service_config_api_id}"
        )

    api_view = session.imap_get(ApiView, api_view_id)
    if service_config_api is not None and api_view is not None and api_view.api_id != service_config_api.api_id:
        raise RuntimeError(
            "ServiceOperationConfig.create_api_view api_view does not belong to the ServiceConfigApi Api: "
            + f"service_operation_config_id={service_operation_config.id} "
            + f"api_view_id={api_view_id}"
        )

    created = await ServiceOperationConfigApiView.build_via_service_operation_config(
        service_operation_config_id=service_operation_config.id,
        service_config_api_id=service_config_api_id,
        api_view_id=api_view_id,
        description=description,
    )
    for existing in service_operation_config.api_views:
        if existing.id == created.id:
            return existing
    service_operation_config.api_views.append(created)
    return created
    # --- AWARE: LOGIC END create_api_view


async def require_role(
    service_operation_config: ServiceOperationConfig,
    role_config_id: UUID,
    access_scope: str = "operation",
    scope_kind: str = "operation",
    scope_ref: str = "default",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    description: str | None = None,
) -> ServiceOperationConfigRoleRequirement:
    """
    Declares ActorRole evidence required before this ServiceOperationConfig can execute.

    Contract:
    - Service declares the role requirement, Identity materializes and resolves ActorRole.
    - Runtime must fail closed when the required role evidence is missing or invalid.
    """

    # --- AWARE: LOGIC START require_role
    created = await ServiceOperationConfigRoleRequirement.build_via_service_operation_config(
        service_operation_config_id=service_operation_config.id,
        role_config_id=role_config_id,
        access_scope=access_scope,
        scope_kind=scope_kind,
        scope_ref=scope_ref,
        class_instance_identity_required=class_instance_identity_required,
        role_assignment_binding_required=role_assignment_binding_required,
        description=description,
    )
    for existing in service_operation_config.role_requirements:
        if existing.id == created.id:
            return existing
    service_operation_config.role_requirements.append(created)
    return created
    # --- AWARE: LOGIC END require_role


async def build_via_service_config(
    service_config_id: UUID,
    name: str,
    description: str | None = None,
    price_id: UUID | None = None,
    admission_mode: ServiceOperationAdmissionMode = ServiceOperationAdmissionMode.contract_required,
    fulfillment_kind: ServiceOperationFulfillmentKind = ServiceOperationFulfillmentKind.coordination,
    receipt_policy: ServiceOperationReceiptPolicy = ServiceOperationReceiptPolicy.committed,
    settlement_policy: ServiceOperationSettlementPolicy = ServiceOperationSettlementPolicy.none,
) -> ServiceOperationConfig:
    """
    Creates one canonical service operation definition under a ServiceConfig.

    Contract:
    - fulfillment_kind declares the service plane this operation may fulfill.
    - view is read-model state fulfillment.
    - coordination is ontology-plane graph/API coordination.
    - actuation is world-profile side-effect fulfillment.
    - Runtime dispatch must fail closed when the selected operation kind is
      incompatible with the dispatch shape.
    """

    # --- AWARE: LOGIC START build_via_service_config
    resolved_settlement_policy = (
        settlement_policy if settlement_policy is not None else ServiceOperationSettlementPolicy.none
    )
    resolved_receipt_policy = receipt_policy if receipt_policy is not None else ServiceOperationReceiptPolicy.committed
    raw_admission_mode = getattr(admission_mode, "value", admission_mode)
    resolved_admission_mode_value = (
        str(raw_admission_mode or ServiceOperationAdmissionMode.contract_required.value).strip().casefold()
    )
    if resolved_admission_mode_value not in {
        "contract_and_permit_required",
        "contract_required",
        "identity_required",
        "metered_settlement_required",
        "public_read",
    }:
        resolved_admission_mode_value = ServiceOperationAdmissionMode.contract_required.value
    resolved_admission_mode = ServiceOperationAdmissionMode(resolved_admission_mode_value)
    raw_fulfillment_kind = getattr(fulfillment_kind, "value", fulfillment_kind)
    resolved_fulfillment_kind_value = (
        str(raw_fulfillment_kind or ServiceOperationFulfillmentKind.coordination.value).strip().casefold()
    )
    if resolved_fulfillment_kind_value not in {"actuation", "coordination", "view"}:
        resolved_fulfillment_kind_value = ServiceOperationFulfillmentKind.coordination.value
    resolved_fulfillment_kind = ServiceOperationFulfillmentKind(resolved_fulfillment_kind_value)
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServiceOperationConfig.build_via_service_config requires non-empty name")

    service_operation_config_id = stable_service_operation_config_id(
        service_config_id=service_config_id,
        name=normalized_name,
    )
    session = current_handler_session()
    existing = session.imap_get(ServiceOperationConfig, service_operation_config_id)
    if existing is not None:
        if (
            existing.service_config_id != service_config_id
            or (existing.name or "").strip() != normalized_name
            or getattr(existing, "price_id", None) != price_id
            or getattr(existing, "receipt_policy", None) != resolved_receipt_policy
            or getattr(existing, "settlement_policy", None) != resolved_settlement_policy
            or str(
                getattr(
                    getattr(existing, "admission_mode", resolved_admission_mode),
                    "value",
                    getattr(existing, "admission_mode", resolved_admission_mode),
                )
                or ""
            )
            .strip()
            .casefold()
            != resolved_admission_mode.value
            or str(
                getattr(
                    getattr(
                        existing,
                        "fulfillment_kind",
                        ServiceOperationFulfillmentKind.coordination,
                    ),
                    "value",
                    getattr(
                        existing,
                        "fulfillment_kind",
                        ServiceOperationFulfillmentKind.coordination,
                    ),
                )
                or ""
            )
            .strip()
            .casefold()
            != resolved_fulfillment_kind.value
        ):
            raise RuntimeError(
                "ServiceOperationConfig.build_via_service_config payload mismatch for existing config: "
                + f"service_operation_config_id={service_operation_config_id}"
            )
        if not hasattr(existing, "admission_mode"):
            object.__setattr__(existing, "admission_mode", resolved_admission_mode)
        if not hasattr(existing, "fulfillment_kind"):
            object.__setattr__(existing, "fulfillment_kind", resolved_fulfillment_kind)
        return existing

    return ServiceOperationConfig(
        id=service_operation_config_id,
        service_config_id=service_config_id,
        name=normalized_name,
        description=description,
        price_id=price_id,
        admission_mode=resolved_admission_mode,
        fulfillment_kind=resolved_fulfillment_kind,
        receipt_policy=resolved_receipt_policy,
        settlement_policy=resolved_settlement_policy,
    )
    # --- AWARE: LOGIC END build_via_service_config
