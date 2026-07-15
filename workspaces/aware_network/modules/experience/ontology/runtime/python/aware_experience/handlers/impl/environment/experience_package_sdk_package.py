from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.experience_package_sdk_package import ExperiencePackageSdkPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# SDK Ontology
from aware_sdk_ontology.sdk.sdk_package import SdkPackage

# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_sdk_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_package(
    experience_package_id: UUID, sdk_package_id: UUID, description: str | None = None
) -> ExperiencePackageSdkPackage:
    """
    Create one package-level Experience dependency bridge to one SDK package.

    Contract:
    - Parent `ExperiencePackage` scope is injected by propagation.
    - Identity is keyed by the attached `SdkPackage`.
    - This declares SDK operation availability for Experience-owned view invocation actions.
    - SDK operation expansion remains SDK/API-owned; Experience owns the view action contract.
    """

    # --- AWARE: LOGIC START build_via_experience_package
    normalized_description = (description or "").strip() or None
    assoc_id = stable_experience_package_sdk_package_id(
        experience_package_id=experience_package_id,
        sdk_package_id=sdk_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(ExperiencePackageSdkPackage, assoc_id)
        if existing is not None:
            if existing.experience_package_id != experience_package_id:
                raise RuntimeError(
                    "ExperiencePackageSdkPackage.build_via_experience_package "
                    f"experience_package mismatch: assoc_id={assoc_id}"
                )
            if existing.sdk_package_id != sdk_package_id:
                raise RuntimeError(
                    "ExperiencePackageSdkPackage.build_via_experience_package "
                    f"sdk_package mismatch: assoc_id={assoc_id}"
                )
            if normalized_description is not None:
                existing_description = (existing.description or "").strip() or None
                if existing_description is None:
                    existing.description = normalized_description
                elif existing_description != normalized_description:
                    raise RuntimeError(
                        "ExperiencePackageSdkPackage.build_via_experience_package "
                        f"description mismatch: assoc_id={assoc_id}"
                    )
            return existing

        resolved_sdk_package = session.imap_get(SdkPackage, sdk_package_id)
    else:
        resolved_sdk_package = None

    return ExperiencePackageSdkPackage.model_construct(
        id=assoc_id,
        experience_package_id=experience_package_id,
        sdk_package_id=sdk_package_id,
        sdk_package=resolved_sdk_package,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_package
