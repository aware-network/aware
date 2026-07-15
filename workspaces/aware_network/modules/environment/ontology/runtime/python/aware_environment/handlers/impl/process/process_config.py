from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.process.process_config import ProcessConfig
from aware_environment_ontology.thread.thread_config import ThreadConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_process_config_id,
)

# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def create_thread_config(
    process_config: ProcessConfig,
    key: str,
    title: str | None = None,
    description: str | None = None,
    workspace_view_key: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
    state_prompt_template: str | None = None,
) -> ThreadConfig:
    """
    Create a ThreadConfig under this ProcessConfig.

    Contract:
    - Deterministic identity under this ProcessConfig using config-level keys.
    - Runtime Thread instances are created under Process.
    - Does not carry Experience program/action semantics.
    """

    # --- AWARE: LOGIC START create_thread_config
    if process_config.id is None:
        raise RuntimeError("ProcessConfig.create_thread_config requires ProcessConfig.id")

    created = await ThreadConfig.build_via_process_config(
        process_config_id=process_config.id,
        key=key,
        title=title,
        description=description,
        workspace_view_key=workspace_view_key,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
        state_prompt_template=state_prompt_template,
    )
    for existing in process_config.thread_configs:
        if existing.id == created.id:
            return existing
    process_config.thread_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_thread_config


async def update_picture(
    process_config: ProcessConfig,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the process config image.

    Contract:
    - Raw bytes are uploaded out-of-band via HTTP file operations.
    - Commits must reference commit-backed StorageBlob metadata only.
    - When setting a picture, image_sha/image_mime_type/image_size_bytes must be provided together.
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
        process_config.image_id = None
        process_config.image = None
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

    process_config.image = blob
    process_config.image_id = blob.id
    # --- AWARE: LOGIC END update_picture


async def build_via_environment_profile_config(
    environment_profile_config_id: UUID,
    type: str,
    key: str,
    title: str | None = None,
    description: str | None = None,
    shape: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ProcessConfig:
    """
    Construct a deterministic ProcessConfig under an EnvironmentProfileConfig.

    Contract:
    - Identity is profile-scoped configuration and does not derive from runtime Process.
    - Runtime Process instances are created under EnvironmentProfile.
    """

    # --- AWARE: LOGIC START build_via_environment_profile_config
    process_config_id = stable_process_config_id(
        environment_profile_config_id=environment_profile_config_id,
        key=key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(ProcessConfig, process_config_id)
    if existing is not None:
        if existing.environment_profile_config_id != environment_profile_config_id or existing.key != key:
            raise RuntimeError(
                "ProcessConfig.build_via_environment_profile_config mismatch "
                f"for existing process_config_id={process_config_id}"
            )
        return existing

    return ProcessConfig(
        id=process_config_id,
        environment_profile_config_id=environment_profile_config_id,
        type=type,
        key=key,
        title=title,
        description=description,
        shape=shape,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END build_via_environment_profile_config
