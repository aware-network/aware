from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Node Ontology
from aware_node_ontology.node.node_package_included_node_package import NodePackageIncludedNodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.stable_ids import (
    stable_node_package_id,
    stable_node_package_included_node_package_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_node_package(
    node_package_id: UUID, included_package_name: str, include_key: str | None = None, description: str | None = None
) -> NodePackageIncludedNodePackage:
    """
    Create one package-level Node composition include bridge.

    Contract:
    - Parent `NodePackage` scope is injected by propagation.
    - Identity is keyed by authored semantic package name, not a raw UUID.
    - `included_node_package` stores the canonical relational target derived from that name.
    - The bridge does not flatten included targets into the authoring package; deployment
      derives effective composition from committed package closure.
    """

    # --- AWARE: LOGIC START build_via_node_package
    normalized_included_package_name = (included_package_name or "").strip()
    if not normalized_included_package_name:
        raise RuntimeError(
            "NodePackageIncludedNodePackage.build_via_node_package requires non-empty included_package_name"
        )
    normalized_include_key = (include_key or "").strip() or normalized_included_package_name
    normalized_description = (description or "").strip() or None

    included_node_package_id = stable_node_package_id(name=normalized_included_package_name)
    if included_node_package_id == node_package_id:
        raise RuntimeError(
            "NodePackageIncludedNodePackage.build_via_node_package cannot include the owning NodePackage: "
            f"node_package_id={node_package_id}"
        )
    bridge_id = stable_node_package_included_node_package_id(
        node_package_id=node_package_id,
        included_package_name=normalized_included_package_name,
    )
    session = current_handler_session()
    included_node_package = session.imap_get(NodePackage, included_node_package_id)
    existing = session.imap_get(NodePackageIncludedNodePackage, bridge_id)
    if existing is not None:
        if existing.node_package_id != node_package_id:
            raise RuntimeError(
                "NodePackageIncludedNodePackage.build_via_node_package payload mismatch for existing bridge: "
                f"node_package_included_node_package_id={bridge_id}"
            )
        if (existing.included_package_name or "").strip() != normalized_included_package_name:
            raise RuntimeError(
                "NodePackageIncludedNodePackage.build_via_node_package included_package_name mismatch: "
                f"node_package_included_node_package_id={bridge_id}"
            )
        if existing.included_node_package_id != included_node_package_id:
            raise RuntimeError(
                "NodePackageIncludedNodePackage.build_via_node_package included_node_package_id mismatch: "
                f"node_package_included_node_package_id={bridge_id}"
            )
        if existing.included_node_package is None and included_node_package is not None:
            existing.included_node_package = included_node_package
        existing.include_key = normalized_include_key
        existing.description = normalized_description
        return existing

    return NodePackageIncludedNodePackage.model_construct(
        id=bridge_id,
        node_package_id=node_package_id,
        included_node_package=included_node_package,
        included_node_package_id=included_node_package_id,
        included_package_name=normalized_included_package_name,
        include_key=normalized_include_key,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_node_package
