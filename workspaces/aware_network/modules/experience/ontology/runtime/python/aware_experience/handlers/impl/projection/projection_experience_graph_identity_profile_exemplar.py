from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph_identity_profile_exemplar import (
    ProjectionExperienceGraphIdentityProfileExemplar,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_projection_experience_graph_identity_profile_exemplar_id

from aware_meta.runtime.handler_context import current_handler_session

from aware_experience_ontology.projection.projection_experience_graph_identity_profile import (
    ProjectionExperienceGraphIdentityProfile,
)
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience_graph_identity_profile(
    projection_experience_graph_identity_profile_id: UUID,
    key: str,
    label: str | None = None,
    prompt_hint: str | None = None,
    note: str | None = None,
    is_primary: bool = False,
    image_id: UUID | None = None,
) -> ProjectionExperienceGraphIdentityProfileExemplar:
    """
    Construct one exemplar row under a ProjectionExperienceGraphIdentityProfile.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_graph_identity_profile
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfileExemplar.build_via_projection_experience_graph_identity_profile "
            + "requires non-empty key"
        )
    normalized_label = (label or "").strip() or None
    normalized_prompt_hint = (prompt_hint or "").strip() or None
    normalized_note = (note or "").strip() or None

    session = current_handler_session()
    profile = session.imap_get(
        ProjectionExperienceGraphIdentityProfile,
        projection_experience_graph_identity_profile_id,
    )
    if profile is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfileExemplar.build_via_projection_experience_graph_identity_profile "
            + "requires known ProjectionExperienceGraphIdentityProfile: "
            + "projection_experience_graph_identity_profile_id="
            + f"{projection_experience_graph_identity_profile_id}"
        )

    blob = None
    if image_id is not None:
        blob = session.imap_get(StorageBlob, image_id)
        if blob is None:
            raise RuntimeError(
                "ProjectionExperienceGraphIdentityProfileExemplar.build_via_projection_experience_graph_identity_profile "
                + f"requires known StorageBlob: image_id={image_id}"
            )

    exemplar_id = stable_projection_experience_graph_identity_profile_exemplar_id(
        projection_experience_graph_identity_profile_id=projection_experience_graph_identity_profile_id,
        key=normalized_key,
    )
    existing = session.imap_get(
        ProjectionExperienceGraphIdentityProfileExemplar,
        exemplar_id,
    )
    if existing is not None:
        if (
            existing.projection_experience_graph_identity_profile_id != projection_experience_graph_identity_profile_id
            or existing.key != normalized_key
            or existing.label != normalized_label
            or existing.prompt_hint != normalized_prompt_hint
            or existing.note != normalized_note
            or bool(existing.is_primary) != bool(is_primary)
            or existing.image_id != image_id
        ):
            raise RuntimeError(
                "ProjectionExperienceGraphIdentityProfileExemplar.build_via_projection_experience_graph_identity_profile "
                + "payload mismatch for existing exemplar: "
                + f"projection_experience_graph_identity_profile_exemplar_id={exemplar_id}"
            )
        return existing

    return ProjectionExperienceGraphIdentityProfileExemplar(
        id=exemplar_id,
        projection_experience_graph_identity_profile_id=projection_experience_graph_identity_profile_id,
        key=normalized_key,
        label=normalized_label,
        prompt_hint=normalized_prompt_hint,
        note=normalized_note,
        is_primary=is_primary,
        image_id=image_id,
        image=blob,
    )
    # --- AWARE: LOGIC END build_via_projection_experience_graph_identity_profile
