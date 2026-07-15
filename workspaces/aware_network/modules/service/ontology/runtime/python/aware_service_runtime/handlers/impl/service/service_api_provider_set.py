from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_api_provider_set import ServiceApiProviderSet
from aware_service_ontology.service.service_api_provider_set_service_package import ServiceApiProviderSetServicePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import (
    current_handler_session,
)
from aware_service_ontology.stable_ids import (
    stable_service_api_provider_set_id,
    stable_service_api_provider_set_service_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build(
    key: str, title: str | None = None, description: str | None = None, version_number: int = 1
) -> ServiceApiProviderSet:
    """
    Create one Service-owned API provider set.

    Contract:
    - Identity is keyed by a stable provider-set key, for example `kernel.global_services.v1`.
    - A provider set groups committed ServicePackage roots that may fulfill API calls remotely.
    - Deployment artifacts may project this object into runtime provider refs, but the semantic
      truth is the committed provider-set object and its ServicePackage memberships.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ServiceApiProviderSet.build requires non-empty key")
    provider_set_id = stable_service_api_provider_set_id(key=normalized_key)
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(ServiceApiProviderSet, provider_set_id)
        if existing is not None:
            if (existing.key or "").strip() != normalized_key:
                raise RuntimeError(
                    "ServiceApiProviderSet.build payload mismatch for existing provider set: "
                    f"service_api_provider_set_id={provider_set_id}"
                )
            existing.title = normalized_title
            existing.description = normalized_description
            existing.version_number = version_number
            return existing

    return ServiceApiProviderSet.model_construct(
        id=provider_set_id,
        key=normalized_key,
        title=normalized_title,
        description=normalized_description,
        version_number=version_number,
        service_packages=[],
    )
    # --- AWARE: LOGIC END build


async def attach_service_package(
    service_api_provider_set: ServiceApiProviderSet,
    service_package_id: UUID,
    membership_key: str | None = None,
    description: str | None = None,
) -> ServiceApiProviderSetServicePackage:
    """
    Attach one committed ServicePackage to this API provider set.

    Contract:
    - Parent `ServiceApiProviderSet` scope is injected by propagation.
    - Identity is keyed by the attached `ServicePackage`.
    - This declares provider-set membership only; API fulfillment still comes from the
      ServicePackage provided-api bridges.
    """

    # --- AWARE: LOGIC START attach_service_package
    if service_api_provider_set.id is None:
        raise RuntimeError("ServiceApiProviderSet.attach_service_package requires ServiceApiProviderSet.id")

    membership_id = stable_service_api_provider_set_service_package_id(
        service_api_provider_set_id=service_api_provider_set.id,
        service_package_id=service_package_id,
    )

    existing_bridge: ServiceApiProviderSetServicePackage | None = None
    for existing in service_api_provider_set.service_packages:
        if existing.id == membership_id or existing.service_package_id == service_package_id:
            existing_bridge = existing
            break

    created = await ServiceApiProviderSetServicePackage.build_via_service_api_provider_set(
        service_api_provider_set_id=service_api_provider_set.id,
        service_package_id=service_package_id,
        membership_key=membership_key,
        description=description,
    )
    if existing_bridge is None:
        service_api_provider_set.service_packages.append(created)
    return created
    # --- AWARE: LOGIC END attach_service_package
