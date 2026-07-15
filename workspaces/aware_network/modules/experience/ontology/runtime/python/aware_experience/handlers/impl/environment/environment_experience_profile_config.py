from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_actor import EnvironmentExperienceActorConfig
from aware_experience_ontology.environment.environment_experience_event import EnvironmentExperienceEvent
from aware_experience_ontology.environment.environment_experience_process_config import (
    EnvironmentExperienceProcessConfig,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_experience_projection import EnvironmentExperienceProjection
from aware_experience_ontology.environment.environment_experience_view_event_transition import (
    EnvironmentExperienceViewEventTransition,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_environment_experience_profile_config_id
from aware_meta.runtime.handler_context import current_handler_session
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def add_process_config(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig,
    process_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentExperienceProcessConfig:
    """
    Attach one Experience config bridge for an Environment ProcessConfig.

    Contract:
    - `process_config_id` references Environment-owned topology config.
    - This function never constructs ProcessConfig.
    - Mutates only this profile config's Experience bridge membership.
    """

    # --- AWARE: LOGIC START add_process_config
    if not key.strip():
        raise RuntimeError("EnvironmentExperienceProfileConfig.add_process_config requires non-empty key")
    profile_config_id = environment_experience_profile_config.id
    if profile_config_id is None:
        raise RuntimeError("EnvironmentExperienceProfileConfig.add_process_config requires profile config id")

    normalized_key = key.strip()
    created = await EnvironmentExperienceProcessConfig.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        process_config_id=process_config_id,
        key=normalized_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )

    for existing in environment_experience_profile_config.process_configs:
        if existing.id == created.id:
            if (
                existing.process_config_id != process_config_id
                or existing.key != normalized_key
                or existing.title != title
                or existing.description != description
                or existing.position != position
                or existing.narrative != narrative
                or existing.intent != intent
            ):
                raise RuntimeError(
                    "EnvironmentExperienceProfileConfig.add_process_config payload mismatch "
                    + f"for existing bridge: environment_experience_process_config_id={existing.id}"
                )
            return existing
        if existing.process_config_id == process_config_id and existing.key == normalized_key:
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.add_process_config duplicate process bridge "
                + f"for process_config_id={process_config_id} key={normalized_key!r}"
            )

    environment_experience_profile_config.process_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_process_config


async def add_actor_config(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig, actor_config_id: UUID
) -> EnvironmentExperienceActorConfig:
    """
    Attach one ActorConfig association edge under this EnvironmentExperienceProfileConfig.
    """

    # --- AWARE: LOGIC START add_actor_config
    profile_config_id = environment_experience_profile_config.id
    if profile_config_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProfileConfig.add_actor_config requires EnvironmentExperienceProfileConfig.id"
        )

    created = await EnvironmentExperienceActorConfig.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        actor_config_id=actor_config_id,
    )

    for existing in environment_experience_profile_config.actors:
        if existing.id == created.id:
            if existing.actor_config_id != actor_config_id:
                raise RuntimeError(
                    "EnvironmentExperienceProfileConfig.add_actor_config actor_config_id mismatch "
                    + f"for existing association: environment_experience_actor_config_id={existing.id}"
                )
            return existing
        if existing.actor_config_id == actor_config_id:
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.add_actor_config detected duplicate actor binding "
                + f"for actor_config_id={actor_config_id}"
            )

    environment_experience_profile_config.actors.append(created)
    return created
    # --- AWARE: LOGIC END add_actor_config


async def add_projection_experience(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig, projection_experience_id: UUID
) -> EnvironmentExperienceProjection:
    """
    Attach one ProjectionExperience association edge under this EnvironmentExperienceProfileConfig.
    """

    # --- AWARE: LOGIC START add_projection_experience
    profile_config_id = environment_experience_profile_config.id
    if profile_config_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProfileConfig.add_projection_experience requires EnvironmentExperienceProfileConfig.id"
        )

    created = await EnvironmentExperienceProjection.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        projection_experience_id=projection_experience_id,
    )

    for existing in environment_experience_profile_config.experiences:
        if existing.id == created.id:
            if existing.projection_experience_id != projection_experience_id:
                raise RuntimeError(
                    "EnvironmentExperienceProfileConfig.add_projection_experience projection_experience_id mismatch "
                    + f"for existing association: environment_experience_projection_id={existing.id}"
                )
            return existing
        if existing.projection_experience_id == projection_experience_id:
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.add_projection_experience detected duplicate projection binding "
                + f"for projection_experience_id={projection_experience_id}"
            )

    environment_experience_profile_config.experiences.append(created)
    return created
    # --- AWARE: LOGIC END add_projection_experience


async def add_event(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig, event_config_id: UUID
) -> EnvironmentExperienceEvent:
    """
    Attach one EventConfig association edge under this EnvironmentExperienceProfileConfig.
    """

    # --- AWARE: LOGIC START add_event
    profile_config_id = environment_experience_profile_config.id
    if profile_config_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProfileConfig.add_event requires EnvironmentExperienceProfileConfig.id"
        )

    created = await EnvironmentExperienceEvent.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        event_config_id=event_config_id,
    )

    for existing in environment_experience_profile_config.events:
        if existing.id == created.id:
            if existing.event_config_id != event_config_id:
                raise RuntimeError(
                    "EnvironmentExperienceProfileConfig.add_event event_config_id mismatch "
                    + f"for existing association: environment_experience_event_id={existing.id}"
                )
            return existing
        if existing.event_config_id == event_config_id:
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.add_event detected duplicate event_config_id "
                + f"for profile_config_id={profile_config_id} event_config_id={event_config_id}"
            )

    environment_experience_profile_config.events.append(created)
    return created
    # --- AWARE: LOGIC END add_event


async def add_view_event_transition(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig,
    source_view_id: UUID,
    trigger_event_id: UUID,
    target_section_graph_binding_id: UUID,
    transition_key: str,
    name: str | None = None,
    rationale: str | None = None,
    idempotency_policy: str | None = None,
) -> EnvironmentExperienceViewEventTransition:
    """
    Attach one Experience-owned View -> Event -> View transition policy.

    Contract:
    - `source_view_id` is the currently focused ProjectionExperienceView.
    - `trigger_event_id` is the profile-config-owned EnvironmentExperienceEvent emitted by Reactivity.
    - `target_section_graph_binding_id` points to the target view/graph/layout section contract.
    - This contract does not talk to Attention directly; runtime focus activation goes through
      ProjectionExperienceSectionGraphBinding.
    """

    # --- AWARE: LOGIC START add_view_event_transition
    profile_config_id = environment_experience_profile_config.id
    if profile_config_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProfileConfig.add_view_event_transition requires EnvironmentExperienceProfileConfig.id"
        )
    normalized_transition_key = (transition_key or "").strip()
    if not normalized_transition_key:
        raise RuntimeError(
            "EnvironmentExperienceProfileConfig.add_view_event_transition requires non-empty transition_key"
        )

    created = await EnvironmentExperienceViewEventTransition.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=normalized_transition_key,
        name=name,
        rationale=rationale,
        idempotency_policy=idempotency_policy,
    )

    for existing in environment_experience_profile_config.view_event_transitions:
        if existing.id == created.id:
            if (
                existing.source_view_id != source_view_id
                or existing.trigger_event_id != trigger_event_id
                or existing.target_section_graph_binding_id != target_section_graph_binding_id
                or existing.transition_key != normalized_transition_key
            ):
                raise RuntimeError(
                    "EnvironmentExperienceProfileConfig.add_view_event_transition payload mismatch "
                    + f"for existing transition: transition_id={existing.id}"
                )
            return existing
        if (
            existing.source_view_id == source_view_id
            and existing.trigger_event_id == trigger_event_id
            and existing.transition_key == normalized_transition_key
        ):
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.add_view_event_transition detected duplicate source/event/key "
                + f"binding for source_view_id={source_view_id} trigger_event_id={trigger_event_id} "
                + f"transition_key={normalized_transition_key}"
            )

    environment_experience_profile_config.view_event_transitions.append(created)
    return created
    # --- AWARE: LOGIC END add_view_event_transition


async def update_title(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig, title: str | None = None
) -> None:
    """
    Replace or clear the title of this Experience profile config.

    Contract:
    - Mutates only the invoked EnvironmentExperienceProfileConfig.
    - `null` explicitly clears the title.
    - Description, narrative, identity, and relationship fields are preserved.
    """

    # --- AWARE: LOGIC START update_title
    environment_experience_profile_config.title = title
    # --- AWARE: LOGIC END update_title


async def update_picture(
    environment_experience_profile_config: EnvironmentExperienceProfileConfig,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the experience profile config image.

    Contract:
    - Raw bytes are uploaded out-of-band via HTTP file operations.
    - Commits must reference commit-backed StorageBlob metadata only.
    - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.

    Parameters:
        image_id: Optional uploaded blob id to assert against image_sha-derived stable id.
        image_sha: SHA-256 hex digest of uploaded bytes.
        image_mime_type: MIME type of uploaded bytes.
        image_size_bytes: Size of uploaded bytes.
    Returns: None.
    """

    # --- AWARE: LOGIC START update_picture
    has_any_meta = any(
        (
            image_sha is not None,
            image_mime_type is not None,
            image_size_bytes is not None,
        )
    )

    if image_id is None and not has_any_meta:
        environment_experience_profile_config.image_id = None
        environment_experience_profile_config.image = None
        return

    if not has_any_meta:
        raise ValueError("image_sha, image_mime_type, and image_size_bytes are required when setting a picture")
    if image_sha is None or image_mime_type is None or image_size_bytes is None:
        raise ValueError("image_sha, image_mime_type, and image_size_bytes must be set together")

    blob = await StorageBlob.create(
        sha=image_sha,
        mime_type=image_mime_type,
        size_bytes=image_size_bytes,
    )
    if image_id is not None and image_id != blob.id:
        raise ValueError(
            "image_id does not match StorageBlob.id derived from image_sha " f"(image_id={image_id} blob_id={blob.id})"
        )

    environment_experience_profile_config.image = blob
    environment_experience_profile_config.image_id = blob.id
    # --- AWARE: LOGIC END update_picture


async def build_via_environment_experience(
    environment_experience_id: UUID,
    environment_profile_config_id: UUID,
    key: str,
    environment_provider_grant_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
) -> EnvironmentExperienceProfileConfig:
    """
    Construct one canonical EnvironmentExperienceProfileConfig under EnvironmentExperience.

    Contract:
    - Identity is derived from parent path plus `(environment_profile_config_id, key)`.
    - The target EnvironmentProfileConfig is Environment-owned reusable topology truth.
    - `environment_provider_grant_id` records the approved Environment provider
      grant when present; it does not make Environment depend on Experience.
    """

    # --- AWARE: LOGIC START build_via_environment_experience
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceProfileConfig.build_via_environment requires non-empty key")

    session = current_handler_session()
    profile_config_id = stable_environment_experience_profile_config_id(
        environment_experience_id=environment_experience_id,
        environment_profile_config_id=environment_profile_config_id,
        key=normalized_key,
    )
    existing = session.imap_get(EnvironmentExperienceProfileConfig, profile_config_id)
    if existing is not None:
        if (
            existing.environment_experience_id != environment_experience_id
            or existing.environment_profile_config_id != environment_profile_config_id
            or existing.environment_provider_grant_id != environment_provider_grant_id
            or existing.key != normalized_key
            or existing.title != title
            or existing.description != description
            or existing.narrative != narrative
        ):
            raise RuntimeError(
                "EnvironmentExperienceProfileConfig.build_via_environment payload mismatch "
                f"for existing profile config: profile_config_id={profile_config_id}"
            )
        return existing

    return EnvironmentExperienceProfileConfig(
        id=profile_config_id,
        environment_experience_id=environment_experience_id,
        environment_profile_config_id=environment_profile_config_id,
        environment_provider_grant_id=environment_provider_grant_id,
        key=normalized_key,
        title=title,
        description=description,
        narrative=narrative,
    )
    # --- AWARE: LOGIC END build_via_environment_experience
