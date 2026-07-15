from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_package_required_api_package import ServicePackageRequiredApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_package import ApiPackage
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import (
    stable_service_package_required_api_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_package(
    service_package_id: UUID, api_package_id: UUID, description: str | None = None
) -> ServicePackageRequiredApiPackage:
    """
    Create one package-level Service consumer bridge to one API package.

    Contract:
    - Parent `ServicePackage` scope is injected by propagation.
    - Identity is keyed by the attached `ApiPackage`.
    - This declares that the Service package requires/invokes this API package.
    - It does not imply this Service package provides or hosts the API.
    """

    # --- AWARE: LOGIC START build_via_service_package
    bridge_id = stable_service_package_required_api_package_id(
        service_package_id=service_package_id,
        api_package_id=api_package_id,
    )
    session = current_handler_session()
    existing = session.imap_get(ServicePackageRequiredApiPackage, bridge_id)
    if existing is not None:
        if existing.service_package_id != service_package_id or existing.api_package_id != api_package_id:
            raise RuntimeError(
                "ServicePackageRequiredApiPackage.build_via_service_package "
                "payload mismatch for existing bridge: "
                f"service_package_required_api_package_id={bridge_id}"
            )
        return existing

    return ServicePackageRequiredApiPackage(
        id=bridge_id,
        service_package_id=service_package_id,
        api_package=session.imap_get(ApiPackage, api_package_id),
        api_package_id=api_package_id,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_service_package
