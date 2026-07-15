from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_package_provided_api_package import ServicePackageProvidedApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.api.api_package_language_package import (
    ApiPackageLanguagePackage,
)
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import (
    stable_service_package_provided_api_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_package(
    service_package_id: UUID,
    api_package_id: UUID,
    service_protocol_package_id: UUID,
    service_protocol_plan_hash_sha256: str,
    api_package_object_instance_graph_commit_id: UUID,
    description: str | None = None,
) -> ServicePackageProvidedApiPackage:
    """
    Create one package-level Service provider bridge to one API package.

    Contract:
    - Parent `ServicePackage` scope is injected by propagation.
    - Identity is keyed by the attached `ApiPackage`.
    - This declares that the Service package provides/hosts this API package.
    - The API package commit, selected API-owned service-protocol language
      package, and normalized protocol-plan digest are materialized
      dependency-lock truth. They are not authored `aware.service.toml` pins.
    - The selected `ApiPackageLanguagePackage` owns the exact generated
      CodePackage commit pin.
    - Commit relationships may remain unresolved in this projection while
      their UUID pins preserve exact cross-graph replay identity.
    - It is the package-level counterpart to config-level `ServiceConfigApi` fulfillment.
    """

    # --- AWARE: LOGIC START build_via_service_package
    normalized_hash = (service_protocol_plan_hash_sha256 or "").strip().lower()
    if len(normalized_hash) != 64 or any(character not in "0123456789abcdef" for character in normalized_hash):
        raise RuntimeError(
            "ServicePackageProvidedApiPackage requires a lowercase " "64-character service_protocol_plan_hash_sha256"
        )

    bridge_id = stable_service_package_provided_api_package_id(
        service_package_id=service_package_id,
        api_package_id=api_package_id,
    )
    session = current_handler_session()
    api_package = session.imap_get(ApiPackage, api_package_id)
    service_protocol_package = session.imap_get(
        ApiPackageLanguagePackage,
        service_protocol_package_id,
    )
    if api_package is None:
        raise RuntimeError(
            "ServicePackageProvidedApiPackage requires the selected ApiPackage "
            f"in the handler session: api_package_id={api_package_id}"
        )
    if service_protocol_package is None:
        raise RuntimeError(
            "ServicePackageProvidedApiPackage requires the selected API language "
            "package in the handler session: "
            f"service_protocol_package_id={service_protocol_package_id}"
        )
    if service_protocol_package.api_package_id != api_package_id:
        raise RuntimeError(
            "ServicePackageProvidedApiPackage service protocol package belongs "
            "to a different ApiPackage: "
            f"expected={api_package_id} "
            f"actual={service_protocol_package.api_package_id}"
        )
    if service_protocol_package.output_key != "python.service_protocol_package":
        raise RuntimeError(
            "ServicePackageProvidedApiPackage requires the canonical API service "
            "protocol output: "
            f"output_key={service_protocol_package.output_key!r}"
        )
    if service_protocol_package.object_instance_graph_commit_id is None:
        raise RuntimeError(
            "ServicePackageProvidedApiPackage selected API service protocol "
            "package has no exact CodePackage commit pin"
        )

    api_package_commit = session.imap_get(
        ObjectInstanceGraphCommit,
        api_package_object_instance_graph_commit_id,
    )
    existing = session.imap_get(ServicePackageProvidedApiPackage, bridge_id)
    if existing is not None:
        if existing.service_package_id != service_package_id or existing.api_package_id != api_package_id:
            raise RuntimeError(
                "ServicePackageProvidedApiPackage.build_via_service_package "
                "payload mismatch for existing bridge: "
                f"service_package_provided_api_package_id={bridge_id}"
            )
        existing.api_package = api_package
        existing.api_package_object_instance_graph_commit = api_package_commit
        existing.api_package_object_instance_graph_commit_id = api_package_object_instance_graph_commit_id
        existing.service_protocol_package = service_protocol_package
        existing.service_protocol_package_id = service_protocol_package_id
        existing.service_protocol_plan_hash_sha256 = normalized_hash
        existing.description = (description or "").strip() or None
        return existing

    return ServicePackageProvidedApiPackage(
        id=bridge_id,
        service_package_id=service_package_id,
        api_package=api_package,
        api_package_id=api_package_id,
        api_package_object_instance_graph_commit=api_package_commit,
        api_package_object_instance_graph_commit_id=(api_package_object_instance_graph_commit_id),
        service_protocol_package=service_protocol_package,
        service_protocol_package_id=service_protocol_package_id,
        service_protocol_plan_hash_sha256=normalized_hash,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_service_package
