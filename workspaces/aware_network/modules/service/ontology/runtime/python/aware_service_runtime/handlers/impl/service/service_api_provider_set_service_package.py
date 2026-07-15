from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_api_provider_set_service_package import ServiceApiProviderSetServicePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.stable_ids import (
    stable_service_api_provider_set_service_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_api_provider_set(
    service_api_provider_set_id: UUID,
    service_package_id: UUID,
    membership_key: str | None = None,
    description: str | None = None,
) -> ServiceApiProviderSetServicePackage:
    """
    Create one provider-set membership bridge to a committed ServicePackage.

    Contract:
    - Parent `ServiceApiProviderSet` scope is injected by propagation.
    - Identity is keyed by the attached `ServicePackage`.
    - The optional `membership_key` is descriptive routing provenance, not identity.
    """

    # --- AWARE: LOGIC START build_via_service_api_provider_set
    membership_id = stable_service_api_provider_set_service_package_id(
        service_api_provider_set_id=service_api_provider_set_id,
        service_package_id=service_package_id,
    )
    normalized_membership_key = (membership_key or "").strip() or None
    normalized_description = (description or "").strip() or None

    session = current_handler_session()
    existing = session.imap_get(ServiceApiProviderSetServicePackage, membership_id)
    if existing is not None:
        if (
            existing.service_api_provider_set_id != service_api_provider_set_id
            or existing.service_package_id != service_package_id
        ):
            raise RuntimeError(
                "ServiceApiProviderSetServicePackage.build_via_service_api_provider_set "
                "payload mismatch for existing membership: "
                f"service_api_provider_set_service_package_id={membership_id}"
            )
        existing.membership_key = normalized_membership_key
        existing.description = normalized_description
        return existing

    return ServiceApiProviderSetServicePackage(
        id=membership_id,
        service_api_provider_set_id=service_api_provider_set_id,
        service_package=session.imap_get(ServicePackage, service_package_id),
        service_package_id=service_package_id,
        membership_key=normalized_membership_key,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_service_api_provider_set
