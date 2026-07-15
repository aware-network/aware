from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.process.process import Process
from aware_environment_ontology.thread.thread import Thread

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_process_id,
)

# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def create_thread(
    process: Process,
    thread_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    is_main: bool = False,
) -> Thread:
    """
    Instantiate one runtime Thread under this Process.

    Contract:
    - Process owns runtime Thread membership.
    - ThreadConfig remains a reusable config portal/key.
    - Runtime identity is `(process_id via path, thread_config_id, key)`.
    """

    # --- AWARE: LOGIC START create_thread
    if process.id is None:
        raise RuntimeError("Process.create_thread requires Process.id")

    created = await Thread.build_via_process(
        process_id=process.id,
        thread_config_id=thread_config_id,
        key=key,
        title=title,
        description=description,
        is_main=is_main,
    )
    for existing in process.threads:
        if existing.id == created.id:
            return existing
    process.threads.append(created)
    return created
    # --- AWARE: LOGIC END create_thread


async def update_picture(
    process: Process,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the process territory image override.

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

    # Clear picture.
    if image_id is None and not has_any_meta:
        process.image_id = None
        process.image = None
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

    process.image = blob
    process.image_id = blob.id
    # --- AWARE: LOGIC END update_picture


async def build_via_environment_profile(
    environment_profile_id: UUID, process_config_id: UUID, key: str, title: str, description: str | None = None
) -> Process:
    """
    Create a runtime Process under an EnvironmentProfile.

    Contract:
    - Parent EnvironmentProfile context is propagated by constructor lowering.
    - ProcessConfig is a reusable config portal/key.
    - Runtime identity is `(environment_profile_id via path, process_config_id, key)`.
    """

    # --- AWARE: LOGIC START build_via_environment_profile
    process_id = stable_process_id(
        environment_profile_id=environment_profile_id,
        process_config_id=process_config_id,
        key=key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(Process, process_id)
    if existing is not None:
        if (
            existing.environment_profile_id != environment_profile_id
            or existing.process_config_id != process_config_id
            or existing.key != key
        ):
            raise RuntimeError(
                "Process.build_via_environment_profile mismatch " f"for existing process_id={process_id}"
            )
        return existing

    return Process(
        id=process_id,
        environment_profile_id=environment_profile_id,
        process_config_id=process_config_id,
        key=key,
        title=title,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_environment_profile
