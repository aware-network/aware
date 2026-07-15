from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.experience_package_api_package import ExperiencePackageApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# API Ontology
from aware_api_ontology.api.api_package import ApiPackage

# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_api_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_package(
    experience_package_id: UUID, api_package_id: UUID, description: str | None = None
) -> ExperiencePackageApiPackage:
    """
    Create one package-level Experience dependency bridge to one API package.

    Contract:
    - Parent `ExperiencePackage` scope is injected by propagation.
    - Identity is keyed by the attached `ApiPackage`.
    - This declares API capability availability for Experience-owned view invocation actions.
    - It does not imply that panes own or provide those API contracts.
    """

    # --- AWARE: LOGIC START build_via_experience_package
    normalized_description = (description or "").strip() or None
    assoc_id = stable_experience_package_api_package_id(
        experience_package_id=experience_package_id,
        api_package_id=api_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(ExperiencePackageApiPackage, assoc_id)
        if existing is not None:
            if existing.experience_package_id != experience_package_id:
                raise RuntimeError(
                    "ExperiencePackageApiPackage.build_via_experience_package "
                    f"experience_package mismatch: assoc_id={assoc_id}"
                )
            if existing.api_package_id != api_package_id:
                raise RuntimeError(
                    "ExperiencePackageApiPackage.build_via_experience_package "
                    f"api_package mismatch: assoc_id={assoc_id}"
                )
            if normalized_description is not None:
                existing_description = (existing.description or "").strip() or None
                if existing_description is None:
                    existing.description = normalized_description
                elif existing_description != normalized_description:
                    raise RuntimeError(
                        "ExperiencePackageApiPackage.build_via_experience_package "
                        f"description mismatch: assoc_id={assoc_id}"
                    )
            return existing

        resolved_api_package = session.imap_get(ApiPackage, api_package_id)
    else:
        resolved_api_package = None

    return ExperiencePackageApiPackage.model_construct(
        id=assoc_id,
        experience_package_id=experience_package_id,
        api_package_id=api_package_id,
        api_package=resolved_api_package,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_package
