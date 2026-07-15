from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Node Ontology
from aware_node_ontology.node.node_config_ontology_target import NodeConfigOntologyTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_node.ontology_package_identity import ontology_package_id_for_name
from aware_node_ontology.stable_ids import stable_node_config_ontology_target_id
from aware_ontology_ontology.ontology.ontology_package import OntologyPackage
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_node_config(node_config_id: UUID, package_name: str) -> NodeConfigOntologyTarget:
    """
    Create one Node-owned ontology target by canonical ontology package name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Identity is keyed by `(node_config_id, package_name)`.
    - The target `OntologyPackage` portal is resolved from `package_name`
      without storing raw graph/package refs as Node source truth.
    - Ontology targets select semantic package authority; runtime service
      exposure is a later host concern and must not be encoded as a raw
      Service target workaround.
    """

    # --- AWARE: LOGIC START build_via_node_config
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("NodeConfigOntologyTarget.build_via_node_config requires non-empty package_name")

    target_id = ontology_package_id_for_name(normalized_package_name)
    association_id = stable_node_config_ontology_target_id(
        node_config_id=node_config_id,
        package_name=normalized_package_name,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_ontology_package = session.imap_get(OntologyPackage, target_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(NodeConfigOntologyTarget, association_id)
        if existing is not None:
            if existing.node_config_id != node_config_id:
                raise RuntimeError(
                    "NodeConfigOntologyTarget.build_via_node_config payload mismatch for existing target: "
                    f"node_config_ontology_target_id={association_id}"
                )
            if existing.ontology_package_id != target_id:
                raise RuntimeError(
                    "NodeConfigOntologyTarget.build_via_node_config ontology_package_id mismatch for existing target: "
                    f"node_config_ontology_target_id={association_id}"
                )
            if (existing.package_name or "").strip() != normalized_package_name:
                raise RuntimeError(
                    "NodeConfigOntologyTarget.build_via_node_config package_name mismatch for existing target: "
                    f"node_config_ontology_target_id={association_id}"
                )
            if existing.ontology_package is None and resolved_ontology_package is not None:
                existing.ontology_package = resolved_ontology_package
            return existing

    return NodeConfigOntologyTarget.model_construct(
        id=association_id,
        node_config_id=node_config_id,
        ontology_package=resolved_ontology_package,
        ontology_package_id=target_id,
        package_name=normalized_package_name,
    )
    # --- AWARE: LOGIC END build_via_node_config
