from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceConfigCodePackageConfigCardinality
from aware_service_ontology.service.service_config_code_package_config import ServiceConfigCodePackageConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import (
    stable_service_config_code_package_config_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_config(
    service_config_id: UUID,
    slot_key: str,
    code_package_config_id: UUID,
    cardinality: ServiceConfigCodePackageConfigCardinality = ServiceConfigCodePackageConfigCardinality.many,
    required: bool = False,
    description: str | None = None,
) -> ServiceConfigCodePackageConfig:
    """
    Create one config-level bridge between a ServiceConfig and one hostable CodePackageConfig.

    Contract:
    - Parent ServiceConfig scope is injected by propagation.
    - The bridge declares service capability only.
    - Concrete CodePackage activation is Node/deployment-specific and must not be inferred here.
    """

    # --- AWARE: LOGIC START build_via_service_config
    normalized_slot_key = (slot_key or "").strip()
    if not normalized_slot_key:
        raise RuntimeError("ServiceConfigCodePackageConfig.build_via_service_config requires non-empty slot_key")
    raw_cardinality = getattr(cardinality, "value", cardinality)
    resolved_cardinality_value = str(raw_cardinality or ServiceConfigCodePackageConfigCardinality.many.value).strip()
    resolved_cardinality = ServiceConfigCodePackageConfigCardinality(resolved_cardinality_value.casefold())

    service_config_code_package_config_id = stable_service_config_code_package_config_id(
        service_config_id=service_config_id,
        code_package_config_id=code_package_config_id,
        slot_key=normalized_slot_key,
    )
    session = current_handler_session()
    existing = session.imap_get(
        ServiceConfigCodePackageConfig,
        service_config_code_package_config_id,
    )
    if existing is not None:
        existing_slot_key = (existing.slot_key or "").strip().casefold()
        if (
            existing.service_config_id != service_config_id
            or existing.code_package_config_id != code_package_config_id
            or existing_slot_key != normalized_slot_key.casefold()
        ):
            raise RuntimeError(
                "ServiceConfigCodePackageConfig.build_via_service_config payload mismatch for existing bridge: "
                + f"service_config_code_package_config_id={service_config_code_package_config_id}"
            )
        existing.slot_key = normalized_slot_key
        existing.cardinality = resolved_cardinality
        existing.required = bool(required)
        existing.description = description
        return existing

    return ServiceConfigCodePackageConfig(
        id=service_config_code_package_config_id,
        service_config_id=service_config_id,
        slot_key=normalized_slot_key,
        code_package_config_id=code_package_config_id,
        cardinality=resolved_cardinality,
        required=bool(required),
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_config
