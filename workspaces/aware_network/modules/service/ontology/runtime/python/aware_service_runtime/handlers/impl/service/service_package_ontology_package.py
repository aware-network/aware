from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_package_ontology_package import ServicePackageOntologyPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import (
    stable_service_package_ontology_package_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_service_package(
    service_package_id: UUID,
    ontology_package_id: UUID,
    package_name: str,
    fqn_prefix: str,
    role: str = "replica",
    requirement_mode: str = "required",
    ontology_package_object_instance_graph_commit_id: UUID | None = None,
    expected_hash_sha256: str | None = None,
    description: str | None = None,
) -> ServicePackageOntologyPackage:
    """
    Attach one ontology package required by this ServicePackage replica rail.

    Contract:
    - Parent `ServicePackage` scope is injected by propagation.
    - Identity is keyed by the required `OntologyPackage`.
    - `role = "replica"` means the Service consumes ontology truth through a
      local read-only projection advanced from Environment fanout.
    - `requirement_mode = "required"` means ServiceHost readiness must fail
      before handler dispatch when the replica requirement is unavailable.
    - The optional OIG commit pin lets WorkspaceRevision/Hub consumers replay
      exact ontology package truth without reopening local source manifests.
    """

    # --- AWARE: LOGIC START build_via_service_package
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("ServicePackageOntologyPackage.build_via_service_package requires " "non-empty package_name")
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_fqn_prefix:
        raise RuntimeError("ServicePackageOntologyPackage.build_via_service_package requires " "non-empty fqn_prefix")

    normalized_role = (role or "").strip() or "replica"
    if normalized_role != "replica":
        raise RuntimeError("ServicePackageOntologyPackage.build_via_service_package only " "supports role='replica'")
    normalized_requirement_mode = (requirement_mode or "").strip() or "required"
    if normalized_requirement_mode != "required":
        raise RuntimeError(
            "ServicePackageOntologyPackage.build_via_service_package only " "supports requirement_mode='required'"
        )

    normalized_expected_hash = (expected_hash_sha256 or "").strip().lower() or None
    if normalized_expected_hash is not None and (
        len(normalized_expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_expected_hash)
    ):
        raise RuntimeError(
            "ServicePackageOntologyPackage.expected_hash_sha256 must be a " "lowercase 64-character SHA-256 hex digest"
        )

    bridge_id = stable_service_package_ontology_package_id(
        service_package_id=service_package_id,
        ontology_package_id=ontology_package_id,
    )
    session = current_handler_session()
    resolved_ontology_package = session.imap_get(OntologyPackage, ontology_package_id)
    resolved_oig_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            ontology_package_object_instance_graph_commit_id,
        )
        if ontology_package_object_instance_graph_commit_id is not None
        else None
    )

    existing = session.imap_get(ServicePackageOntologyPackage, bridge_id)
    if existing is not None:
        if existing.service_package_id != service_package_id or existing.ontology_package_id != ontology_package_id:
            raise RuntimeError(
                "ServicePackageOntologyPackage.build_via_service_package "
                "payload mismatch for existing bridge: "
                f"service_package_ontology_package_id={bridge_id}"
            )
        existing.ontology_package = resolved_ontology_package
        existing.ontology_package_object_instance_graph_commit = resolved_oig_commit
        existing.ontology_package_object_instance_graph_commit_id = ontology_package_object_instance_graph_commit_id
        existing.role = normalized_role
        existing.requirement_mode = normalized_requirement_mode
        existing.package_name = normalized_package_name
        existing.fqn_prefix = normalized_fqn_prefix
        existing.expected_hash_sha256 = normalized_expected_hash
        existing.description = (description or "").strip() or None
        return existing

    return ServicePackageOntologyPackage(
        id=bridge_id,
        service_package_id=service_package_id,
        ontology_package=resolved_ontology_package,
        ontology_package_id=ontology_package_id,
        ontology_package_object_instance_graph_commit=resolved_oig_commit,
        ontology_package_object_instance_graph_commit_id=(ontology_package_object_instance_graph_commit_id),
        role=normalized_role,
        requirement_mode=normalized_requirement_mode,
        package_name=normalized_package_name,
        fqn_prefix=normalized_fqn_prefix,
        expected_hash_sha256=normalized_expected_hash,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_service_package
