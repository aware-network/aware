from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.pane_package_experience_package import PanePackageExperiencePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.environment.experience_package import ExperiencePackage

# Interface Ontology
from aware_interface_ontology.stable_ids import stable_pane_package_experience_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_pane_package(
    pane_package_id: UUID, experience_package_id: UUID, description: str | None = None
) -> PanePackageExperiencePackage:
    """
    Create one package-level Pane bridge to one ExperiencePackage.

    Contract:
    - Parent `PanePackage` scope is injected by propagation.
    - Identity is keyed by the attached `ExperiencePackage`.
    - This is the pane-local import seam for resolving the PaneConfig
      ProjectionExperienceView key.
    - Interface packages consume the resolved PanePackage; they do not
      declare Experience packages to resolve pane views.
    """

    # --- AWARE: LOGIC START build_via_pane_package
    edge_id = stable_pane_package_experience_package_id(
        pane_package_id=pane_package_id,
        experience_package_id=experience_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_experience_package = (
        session.imap_get(ExperiencePackage, experience_package_id) if session is not None else None
    )
    if session is not None:
        existing = session.imap_get(PanePackageExperiencePackage, edge_id)
        if existing is not None:
            if existing.experience_package_id not in (None, experience_package_id):
                raise RuntimeError(
                    "PanePackageExperiencePackage existing experience_package_id mismatch: "
                    f"pane_package_experience_package_id={edge_id}"
                )
            if description is not None and existing.description not in (None, description):
                raise RuntimeError(
                    "PanePackageExperiencePackage existing description mismatch: "
                    f"pane_package_experience_package_id={edge_id}"
                )
            if existing.experience_package is None and resolved_experience_package is not None:
                existing.experience_package = resolved_experience_package
            if existing.experience_package_id is None:
                existing.experience_package_id = experience_package_id
            if existing.description is None:
                existing.description = description
            return existing

    return PanePackageExperiencePackage.model_construct(
        id=edge_id,
        pane_package_id=pane_package_id,
        experience_package=resolved_experience_package,
        experience_package_id=experience_package_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_pane_package
