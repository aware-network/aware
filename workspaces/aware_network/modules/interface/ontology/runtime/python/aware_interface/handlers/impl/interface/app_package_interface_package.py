from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.app_package_interface_package import AppPackageInterfacePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_app_package(
    app_package_id: UUID,
    interface_package_id: UUID,
    interface_package_object_instance_graph_commit_id: UUID | None = None,
    role: str = "interface",
    description: str | None = None,
) -> AppPackageInterfacePackage:
    """
    Create one app package dependency on an InterfacePackage.

    Contract:
    - Parent AppPackage scope is injected by propagation.
    - Identity is keyed by the attached InterfacePackage.
    - InterfacePackage supplies reusable interface composition; AppConfig
      screen selection remains Experience layout-binding oriented.
    """

    # --- AWARE: LOGIC START build_via_app_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_app_package
