from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Skill Ontology
from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# API Ontology
from aware_api_ontology.api.api_package import ApiPackage

# Skill Ontology
from aware_skill_ontology.stable_ids import stable_skill_package_api_package_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_skill_package(
    skill_package_id: UUID, api_package_id: UUID, description: str | None = None
) -> SkillPackageApiPackage:
    """
    Create one package-level Skill bridge to one API package.

    Contract:
    - Parent `SkillPackage` scope is injected by propagation.
    - Identity is keyed by the attached `ApiPackage`.
    - This is the package/import seam for authored Skill source resolution.
    - It does not replace config-level semantic API or endpoint resolution.
    """

    # --- AWARE: LOGIC START build_via_skill_package
    edge_id = stable_skill_package_api_package_id(
        skill_package_id=skill_package_id,
        api_package_id=api_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_api_package = session.imap_get(ApiPackage, api_package_id) if session is not None else None
    if session is not None:
        existing = session.imap_get(SkillPackageApiPackage, edge_id)
        if existing is not None:
            if existing.api_package_id not in (None, api_package_id):
                raise RuntimeError(
                    "SkillPackageApiPackage existing api_package_id mismatch: "
                    f"skill_package_api_package_id={edge_id}"
                )
            if description is not None and existing.description not in (None, description):
                raise RuntimeError(
                    "SkillPackageApiPackage existing description mismatch: " f"skill_package_api_package_id={edge_id}"
                )
            if existing.api_package is None and resolved_api_package is not None:
                existing.api_package = resolved_api_package
            if existing.api_package_id is None:
                existing.api_package_id = api_package_id
            if existing.description is None:
                existing.description = description
            return existing

    return SkillPackageApiPackage.model_construct(
        id=edge_id,
        skill_package_id=skill_package_id,
        api_package=resolved_api_package,
        api_package_id=api_package_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_skill_package
