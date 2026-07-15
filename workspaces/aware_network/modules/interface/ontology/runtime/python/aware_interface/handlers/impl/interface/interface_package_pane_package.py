from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_package_pane_package import InterfacePackagePanePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Interface Ontology
from aware_interface_ontology.stable_ids import stable_interface_package_pane_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_interface_package(
    interface_package_id: UUID, pane_package_id: UUID, description: str | None = None
) -> InterfacePackagePanePackage:
    """
    Create one package-level Interface bridge to one PanePackage.

    Contract:
    - Parent `InterfacePackage` scope is injected by propagation.
    - Identity is keyed by the attached `PanePackage`.
    - This is the package/import seam for authored Interface pane composition.
    - It does not replace config-level PaneConfig composition inside InterfaceConfig.
    """

    # --- AWARE: LOGIC START build_via_interface_package
    edge_id = stable_interface_package_pane_package_id(
        interface_package_id=interface_package_id,
        pane_package_id=pane_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(InterfacePackagePanePackage, edge_id)
        if existing is not None:
            if existing.pane_package_id not in (None, pane_package_id):
                raise RuntimeError(
                    "InterfacePackagePanePackage existing pane_package_id mismatch: "
                    f"interface_package_pane_package_id={edge_id}"
                )
            if description is not None and existing.description not in (None, description):
                raise RuntimeError(
                    "InterfacePackagePanePackage existing description mismatch: "
                    f"interface_package_pane_package_id={edge_id}"
                )
            if existing.pane_package_id is None:
                existing.pane_package_id = pane_package_id
            if existing.description is None:
                existing.description = description
            return existing

    return InterfacePackagePanePackage.model_construct(
        id=edge_id,
        interface_package_id=interface_package_id,
        pane_package_id=pane_package_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_interface_package
