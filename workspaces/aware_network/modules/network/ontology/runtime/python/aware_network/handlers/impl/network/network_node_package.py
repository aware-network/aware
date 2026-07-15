from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Network Ontology
from aware_network_ontology.network.network_node_package import NetworkNodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_network_ontology.network.network_node_config import NetworkNodeConfig
from aware_network_ontology.stable_ids import stable_network_node_package_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(
    name: str, network_node_config_id: UUID, source_code_package_id: UUID | None = None
) -> NetworkNodePackage:
    """
    Create the canonical Network-owned package root over an existing `NetworkNodeConfig`.

    Contract:
    - Identity is keyed by Network node package `name`.
    - `NetworkNodePackage` is the package/public root over an existing canonical
      `NetworkNodeConfig`.
    - `network_node_config_id` must point at the canonical NetworkNodeConfig stable id for
      this package root.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic
      leaf package.
    - Workspace will later mount `NetworkNodePackage`, not raw `NetworkNodeConfig`.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NetworkNodePackage.build requires non-empty name")

    package_id = stable_network_node_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_network_node_config = (
        session.imap_get(NetworkNodeConfig, network_node_config_id) if session is not None else None
    )
    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(NetworkNodePackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "NetworkNodePackage.build payload mismatch for existing package: "
                    f"network_node_package_id={package_id}"
                )
            if existing.network_node_config_id != network_node_config_id:
                raise RuntimeError(
                    "NetworkNodePackage.build network_node_config_id mismatch for existing package: "
                    f"network_node_package_id={package_id} "
                    f"existing={existing.network_node_config_id} provided={network_node_config_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "NetworkNodePackage.build source_code_package_id mismatch for existing package: "
                        f"network_node_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            return existing

    return NetworkNodePackage.model_construct(
        id=package_id,
        name=normalized_name,
        network_node_config=resolved_network_node_config,
        network_node_config_id=network_node_config_id,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
    )
    # --- AWARE: LOGIC END build
