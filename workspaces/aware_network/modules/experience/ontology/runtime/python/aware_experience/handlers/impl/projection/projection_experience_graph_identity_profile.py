from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph_identity_profile import (
    ProjectionExperienceGraphIdentityProfile,
)
from aware_experience_ontology.projection.projection_experience_graph_identity_profile_exemplar import (
    ProjectionExperienceGraphIdentityProfileExemplar,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Runtime
from aware_experience.stable_ids import (
    stable_projection_experience_graph_identity_profile_id,
)

# Experience Ontology
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_exemplar(
    projection_experience_graph_identity_profile: ProjectionExperienceGraphIdentityProfile,
    key: str,
    label: str | None = None,
    prompt_hint: str | None = None,
    note: str | None = None,
    is_primary: bool = False,
    image_id: UUID | None = None,
) -> ProjectionExperienceGraphIdentityProfileExemplar:
    """
    Attach one exemplar row under this graph-identity profile.

    Contract:
    - Exemplar bytes are uploaded out-of-band; commits reference StorageBlob metadata only.
    - Exemplars improve future matching quality but do not redefine graph identity.
    """

    # --- AWARE: LOGIC START create_exemplar
    profile_id = projection_experience_graph_identity_profile.id
    if profile_id is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfile.create_exemplar requires ProjectionExperienceGraphIdentityProfile.id"
        )

    created = (
        await ProjectionExperienceGraphIdentityProfileExemplar.build_via_projection_experience_graph_identity_profile(
            projection_experience_graph_identity_profile_id=profile_id,
            key=key,
            label=label,
            prompt_hint=prompt_hint,
            note=note,
            is_primary=is_primary,
            image_id=image_id,
        )
    )

    if created.is_primary:
        for existing in projection_experience_graph_identity_profile.exemplars:
            if existing.id == created.id:
                continue
            if bool(existing.is_primary):
                raise RuntimeError(
                    "ProjectionExperienceGraphIdentityProfile.create_exemplar allows a single primary exemplar"
                )

    for existing in projection_experience_graph_identity_profile.exemplars:
        if existing.id == created.id:
            return existing
    projection_experience_graph_identity_profile.exemplars.append(created)
    return created
    # --- AWARE: LOGIC END create_exemplar


async def build_via_projection_experience_graph_identity(
    projection_experience_graph_identity_id: UUID,
    review_label: str,
    resolution_prompts: list[str] = [],
    aliases: list[str] = [],
    summary: str | None = None,
    notes: str | None = None,
) -> ProjectionExperienceGraphIdentityProfile:
    """
    Construct one canonical graph-identity profile under a ProjectionExperienceGraphIdentity.

    Contract:
    - Parent graph identity is the canonical anchor for this profile.
    - `review_label` is the human-facing label used in review/UI rails.
    - `resolution_prompts` are deterministic matcher hints, not identity by themselves.
    - Richer content/location extensions may evolve later without redefining this core surface.
    """

    # --- AWARE: LOGIC START build_via_projection_experience_graph_identity
    normalized_review_label = (review_label or "").strip()
    if not normalized_review_label:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfile.build_via_projection_experience_graph_identity requires non-empty review_label"
        )

    normalized_resolution_prompts: list[str] = []
    resolution_prompt_seen: set[str] = set()
    for value in resolution_prompts:
        trimmed = (value or "").strip()
        if not trimmed or trimmed in resolution_prompt_seen:
            continue
        resolution_prompt_seen.add(trimmed)
        normalized_resolution_prompts.append(trimmed)
    if not normalized_resolution_prompts:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfile.build_via_projection_experience_graph_identity requires non-empty resolution_prompts"
        )

    normalized_aliases: list[str] = []
    alias_seen: set[str] = set()
    for value in aliases:
        trimmed = (value or "").strip()
        if not trimmed or trimmed in alias_seen:
            continue
        alias_seen.add(trimmed)
        normalized_aliases.append(trimmed)

    normalized_summary = (summary or "").strip() or None
    normalized_notes = (notes or "").strip() or None

    session = current_handler_session()
    graph_identity = session.imap_get(ProjectionExperienceGraphIdentity, projection_experience_graph_identity_id)
    if graph_identity is None:
        raise RuntimeError(
            "ProjectionExperienceGraphIdentityProfile.build_via_projection_experience_graph_identity requires known "
            + "ProjectionExperienceGraphIdentity: "
            + f"projection_experience_graph_identity_id={projection_experience_graph_identity_id}"
        )

    profile_id = stable_projection_experience_graph_identity_profile_id(
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
    )
    existing = session.imap_get(
        ProjectionExperienceGraphIdentityProfile,
        profile_id,
    )
    if existing is not None:
        existing_resolution_prompts = [((value or "").strip()) for value in (existing.resolution_prompts or [])]
        existing_resolution_prompts = [value for value in existing_resolution_prompts if value]
        existing_aliases = [((value or "").strip()) for value in (existing.aliases or [])]
        existing_aliases = [value for value in existing_aliases if value]
        existing_summary = (existing.summary or "").strip() or None
        existing_notes = (existing.notes or "").strip() or None
        if (
            existing.projection_experience_graph_identity_id != projection_experience_graph_identity_id
            or existing.review_label != normalized_review_label
            or existing_resolution_prompts != normalized_resolution_prompts
            or existing_aliases != normalized_aliases
            or existing_summary != normalized_summary
            or existing_notes != normalized_notes
        ):
            raise RuntimeError(
                "ProjectionExperienceGraphIdentityProfile.build_via_projection_experience_graph_identity payload mismatch "
                + f"for existing profile: projection_experience_graph_identity_profile_id={profile_id}"
            )
        return existing

    return ProjectionExperienceGraphIdentityProfile(
        id=profile_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        review_label=normalized_review_label,
        resolution_prompts=normalized_resolution_prompts,
        aliases=normalized_aliases,
        summary=normalized_summary,
        notes=normalized_notes,
        exemplars=[],
    )
    # --- AWARE: LOGIC END build_via_projection_experience_graph_identity
