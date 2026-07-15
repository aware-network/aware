from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_process_config import (
    EnvironmentExperienceProcessConfig,
)
from aware_experience_ontology.environment.environment_experience_thread_config import EnvironmentExperienceThreadConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_environment_experience_process_config_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_thread_config(
    environment_experience_process_config: EnvironmentExperienceProcessConfig,
    thread_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentExperienceThreadConfig:
    """
    Attach one Experience config bridge for an Environment ThreadConfig.

    Contract:
    - `thread_config_id` references Environment-owned topology.
    - This function never constructs ThreadConfig.
    - Program and action semantics are attached under the thread config bridge.
    """

    # --- AWARE: LOGIC START add_thread_config
    process_bridge_id = environment_experience_process_config.id
    if process_bridge_id is None:
        raise RuntimeError(
            "EnvironmentExperienceProcessConfig.add_thread_config requires " "EnvironmentExperienceProcessConfig.id"
        )
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceProcessConfig.add_thread_config requires non-empty key")

    created = await EnvironmentExperienceThreadConfig.build_via_environment_experience_process_config(
        environment_experience_process_config_id=process_bridge_id,
        thread_config_id=thread_config_id,
        key=normalized_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )

    for existing in environment_experience_process_config.thread_configs:
        if existing.id == created.id:
            if existing.thread_config_id != thread_config_id or existing.key != normalized_key:
                raise RuntimeError(
                    "EnvironmentExperienceProcessConfig.add_thread_config payload mismatch "
                    f"for existing bridge: environment_experience_thread_config_id={existing.id}"
                )
            return existing
        if existing.thread_config_id == thread_config_id and existing.key == normalized_key:
            raise RuntimeError(
                "EnvironmentExperienceProcessConfig.add_thread_config duplicate thread bridge "
                f"for thread_config_id={thread_config_id} key={normalized_key!r}"
            )

    environment_experience_process_config.thread_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_thread_config


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID,
    process_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> EnvironmentExperienceProcessConfig:
    """
    Construct one Experience process config bridge.

    Contract:
    - Identity is derived from parent profile plus `(process_config_id, key)`.
    - `process_config_id` references Environment ProcessConfig topology truth.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("EnvironmentExperienceProcessConfig.build requires non-empty key")
    if position is not None and position < 0:
        raise RuntimeError("EnvironmentExperienceProcessConfig.build requires position >= 0")

    process_bridge_id = stable_environment_experience_process_config_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceProcessConfig, process_bridge_id)
    if existing is not None:
        if (
            existing.environment_experience_profile_config_id != environment_experience_profile_config_id
            or existing.process_config_id != process_config_id
            or existing.key != normalized_key
            or existing.title != title
            or existing.description != description
            or existing.position != position
            or existing.narrative != narrative
            or existing.intent != intent
        ):
            raise RuntimeError(
                "EnvironmentExperienceProcessConfig.build payload mismatch "
                f"for existing bridge: environment_experience_process_config_id={process_bridge_id}"
            )
        return existing

    return EnvironmentExperienceProcessConfig(
        id=process_bridge_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key=normalized_key,
        title=title,
        description=description,
        position=position,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
