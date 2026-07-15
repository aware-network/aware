from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.app_package_experience_package import AppPackageExperiencePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_app_package(
    app_package_id: UUID,
    experience_package_id: UUID,
    experience_package_object_instance_graph_commit_id: UUID | None = None,
    role: str = "experience",
    description: str | None = None,
) -> AppPackageExperiencePackage:
    """
    Create one app package dependency on an ExperiencePackage.

    Contract:
    - Parent AppPackage scope is injected by propagation.
    - Identity is keyed by the attached ExperiencePackage.
    - This is the app front door dependency: app screens resolve Experience
      layout graph bindings, not Environment internals.
    """

    # --- AWARE: LOGIC START build_via_app_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_app_package
