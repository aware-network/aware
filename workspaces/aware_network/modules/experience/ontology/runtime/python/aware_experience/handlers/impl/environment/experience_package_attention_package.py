from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.experience_package_attention_package import ExperiencePackageAttentionPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Attention Ontology
from aware_attention_ontology.attention.attention_package import AttentionPackage

# Experience Ontology
from aware_experience.stable_ids import stable_experience_package_attention_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_experience_package(
    experience_package_id: UUID, attention_package_id: UUID, description: str | None = None
) -> ExperiencePackageAttentionPackage:
    """
    Create one package-level Experience dependency bridge to one Attention package.

    Contract:
    - Parent `ExperiencePackage` scope is injected by propagation.
    - Identity is keyed by the attached `AttentionPackage`.
    - This declares that Experience-authored views and section-graph bindings may target
      layout/section topology from the attached Attention package.
    - It does not grant direct Attention mutation authority.
    """

    # --- AWARE: LOGIC START build_via_experience_package
    normalized_description = (description or "").strip() or None
    assoc_id = stable_experience_package_attention_package_id(
        experience_package_id=experience_package_id,
        attention_package_id=attention_package_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(ExperiencePackageAttentionPackage, assoc_id)
        if existing is not None:
            if existing.experience_package_id != experience_package_id:
                raise RuntimeError(
                    "ExperiencePackageAttentionPackage.build_via_experience_package "
                    f"experience_package mismatch: assoc_id={assoc_id}"
                )
            if existing.attention_package_id != attention_package_id:
                raise RuntimeError(
                    "ExperiencePackageAttentionPackage.build_via_experience_package "
                    f"attention_package mismatch: assoc_id={assoc_id}"
                )
            if normalized_description is not None:
                existing_description = (existing.description or "").strip() or None
                if existing_description is None:
                    existing.description = normalized_description
                elif existing_description != normalized_description:
                    raise RuntimeError(
                        "ExperiencePackageAttentionPackage.build_via_experience_package "
                        f"description mismatch: assoc_id={assoc_id}"
                    )
            return existing

        resolved_attention_package = session.imap_get(AttentionPackage, attention_package_id)
    else:
        resolved_attention_package = None

    return ExperiencePackageAttentionPackage.model_construct(
        id=assoc_id,
        experience_package_id=experience_package_id,
        attention_package_id=attention_package_id,
        attention_package=resolved_attention_package,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_package
