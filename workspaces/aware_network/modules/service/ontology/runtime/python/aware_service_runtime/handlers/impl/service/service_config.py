from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_enums import (
    ServiceConfigCodePackageConfigCardinality,
    ServiceContractKind,
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_config_code_package_config import ServiceConfigCodePackageConfig
from aware_service_ontology.service.service_config_experience import ServiceConfigExperience
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_operation_config import ServiceOperationConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> ServiceConfig:
    """
    Creates one canonical service capability definition.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServiceConfig.build requires non-empty name")

    service_config_id = stable_service_config_id(name=normalized_name)
    session = current_handler_session()
    existing = session.imap_get(ServiceConfig, service_config_id)
    if existing is not None:
        existing_name = getattr(existing, "name", None)
        if existing_name is not None and existing_name.strip() != normalized_name:
            raise RuntimeError(
                "ServiceConfig.build payload mismatch for existing service_config: "
                + f"service_config_id={service_config_id}"
            )
        existing.name = normalized_name
        existing.description = description
        return existing

    return ServiceConfig(
        id=service_config_id,
        name=normalized_name,
        description=description,
    )
    # --- AWARE: LOGIC END build


async def create_service_operation_config(
    service_config: ServiceConfig,
    name: str,
    description: str | None = None,
    price_id: UUID | None = None,
    admission_mode: ServiceOperationAdmissionMode = ServiceOperationAdmissionMode.contract_required,
    fulfillment_kind: ServiceOperationFulfillmentKind = ServiceOperationFulfillmentKind.coordination,
    receipt_policy: ServiceOperationReceiptPolicy = ServiceOperationReceiptPolicy.committed,
    settlement_policy: ServiceOperationSettlementPolicy = ServiceOperationSettlementPolicy.none,
) -> ServiceOperationConfig:
    """
    Creates one operation definition under this ServiceConfig.
    """

    # --- AWARE: LOGIC START create_service_operation_config
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
    build_annotations = getattr(
        ServiceOperationConfig.build_via_service_config,
        "__annotations__",
        {},
    )
    build_kwargs = {
        "service_config_id": service_config.id,
        "name": name,
        "description": description,
        "price_id": price_id,
        "receipt_policy": resolved_receipt_policy,
        "settlement_policy": resolved_settlement_policy,
    }
    if "admission_mode" in build_annotations:
        build_kwargs["admission_mode"] = resolved_admission_mode
    if "fulfillment_kind" in build_annotations:
        build_kwargs["fulfillment_kind"] = resolved_fulfillment_kind
    created = await ServiceOperationConfig.build_via_service_config(**build_kwargs)
    if not hasattr(created, "admission_mode"):
        object.__setattr__(created, "admission_mode", resolved_admission_mode)
    if not hasattr(created, "fulfillment_kind"):
        object.__setattr__(created, "fulfillment_kind", resolved_fulfillment_kind)
    for existing in service_config.service_operation_configs:
        if existing.id == created.id:
            if not hasattr(existing, "admission_mode"):
                object.__setattr__(existing, "admission_mode", resolved_admission_mode)
            if not hasattr(existing, "fulfillment_kind"):
                object.__setattr__(existing, "fulfillment_kind", resolved_fulfillment_kind)
            return existing
    service_config.service_operation_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_service_operation_config


async def create_service(service_config: ServiceConfig, name: str, description: str | None = None) -> Service:
    """
    Creates one Service instance under this ServiceConfig.
    """

    # --- AWARE: LOGIC START create_service
    created = await Service.build_via_service_config(
        service_config_id=service_config.id,
        name=name,
        description=description,
    )
    for existing in service_config.services:
        if existing.id == created.id:
            return existing
    service_config.services.append(created)
    return created
    # --- AWARE: LOGIC END create_service


async def create_contract_config(
    service_config: ServiceConfig,
    name: str,
    default_kind: ServiceContractKind = ServiceContractKind.subscription,
    projection_experience_id: UUID | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> ServiceContractConfig:
    """
    Creates one reusable contract configuration under this ServiceConfig.

    Contract:
    - ServiceContractConfig declares which operations and roles a kind of contract can grant.
    - Concrete ServiceContract receipts reference this config when activated for a consumer.
    - Commercial profile, subscription, and smart-contract receipts do not own reusable grant semantics.
    """

    # --- AWARE: LOGIC START create_contract_config
    resolved_default_kind = default_kind if default_kind is not None else ServiceContractKind.subscription
    created = await ServiceContractConfig.build_via_service_config(
        service_config_id=service_config.id,
        name=name,
        default_kind=resolved_default_kind,
        projection_experience_id=projection_experience_id,
        description=description,
        metadata_json=metadata_json,
    )
    for existing in service_config.contract_configs:
        if existing.id == created.id:
            return existing
    service_config.contract_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_contract_config


async def create_api(service_config: ServiceConfig, api_id: UUID, description: str | None = None) -> ServiceConfigApi:
    """
    Creates one shared-API discovery bridge under this ServiceConfig.
    """

    # --- AWARE: LOGIC START create_api
    created = await ServiceConfigApi.build_via_service_config(
        service_config_id=service_config.id,
        api_id=api_id,
        description=description,
    )
    for existing in service_config.apis:
        if existing.id == created.id:
            return existing
    service_config.apis.append(created)
    return created
    # --- AWARE: LOGIC END create_api


async def create_experience(
    service_config: ServiceConfig, projection_experience_id: UUID, description: str | None = None
) -> ServiceConfigExperience:
    """
    Creates one shared-Experience discovery bridge under this ServiceConfig.
    """

    # --- AWARE: LOGIC START create_experience
    created = await ServiceConfigExperience.build_via_service_config(
        service_config_id=service_config.id,
        projection_experience_id=projection_experience_id,
        description=description,
    )
    for existing in service_config.experiences:
        if existing.id == created.id:
            return existing
    service_config.experiences.append(created)
    return created
    # --- AWARE: LOGIC END create_experience


async def declare_code_package_config(
    service_config: ServiceConfig,
    slot_key: str,
    code_package_config_id: UUID,
    cardinality: ServiceConfigCodePackageConfigCardinality = ServiceConfigCodePackageConfigCardinality.many,
    required: bool = False,
    description: str | None = None,
) -> ServiceConfigCodePackageConfig:
    """
    Declare one CodePackageConfig slot this ServiceConfig can activate.

    Contract:
    - This is service capability truth, not deployment selection.
    - `slot_key` is service-local vocabulary such as `experience`.
    - CodePackageConfig owns package kind, manifest, materialization, and runtime context truth.
    - Node/deployment profiles later bind concrete CodePackage instances to this slot.
    """

    # --- AWARE: LOGIC START declare_code_package_config
    service_config_id = service_config.id
    if service_config_id is None:
        raise RuntimeError("ServiceConfig.declare_code_package_config requires ServiceConfig.id")
    normalized_slot_key = (slot_key or "").strip()
    if not normalized_slot_key:
        raise RuntimeError("ServiceConfig.declare_code_package_config requires non-empty slot_key")
    raw_cardinality = getattr(cardinality, "value", cardinality)
    resolved_cardinality_value = str(raw_cardinality or ServiceConfigCodePackageConfigCardinality.many.value).strip()
    resolved_cardinality = ServiceConfigCodePackageConfigCardinality(resolved_cardinality_value.casefold())

    created = await ServiceConfigCodePackageConfig.build_via_service_config(
        service_config_id=service_config_id,
        slot_key=normalized_slot_key,
        code_package_config_id=code_package_config_id,
        cardinality=resolved_cardinality,
        required=bool(required),
        description=description,
    )
    for existing in service_config.code_package_configs:
        if existing.id == created.id:
            return existing
    service_config.code_package_configs.append(created)
    return created
    # --- AWARE: LOGIC END declare_code_package_config
