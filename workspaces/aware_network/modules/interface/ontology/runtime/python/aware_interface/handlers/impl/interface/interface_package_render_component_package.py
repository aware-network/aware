from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_package_render_component_package import (
    InterfacePackageRenderComponentPackage,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_interface_package(
    interface_package_id: UUID, render_component_package_id: UUID, description: str | None = None
) -> InterfacePackageRenderComponentPackage:
    """
    Create one package-level Interface bridge to one RenderComponentPackage.

    Contract:
    - Parent `InterfacePackage` scope is injected by propagation.
    - Identity is keyed by the attached `RenderComponentPackage`.
    - This is the package/import seam for renderer component registries available to an
      Interface package.
    - It does not replace pane-level render specs or view/action/state bindings.
    """

    # --- AWARE: LOGIC START build_via_interface_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_interface_package
