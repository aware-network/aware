from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread import Thread
from aware_environment_ontology.thread.thread_layout import ThreadLayout
from aware_environment_ontology.thread.thread_object_instance_graph_branch import ThreadObjectInstanceGraphBranch

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_thread_id,
)

# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def build_via_process(
    process_id: UUID,
    thread_config_id: UUID,
    key: str,
    title: str | None = None,
    description: str | None = None,
    is_main: bool = False,
) -> Thread:
    """
    Creates a new Thread in the current Environment.

    Notes:
    - Thread identity is derived deterministically from `key` (`stable_thread_id`).
    - This is an internal constructor used by Process.create_thread.
    - process_id must reference an existing Process in the OS lane.
    """

    # --- AWARE: LOGIC START build_via_process
    thread_id = stable_thread_id(
        process_id=process_id,
        thread_config_id=thread_config_id,
        key=key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(Thread, thread_id)
    if existing is not None:
        if (
            existing.thread_config_id != thread_config_id
            or existing.process_id != process_id
            or existing.key != key
        ):
            raise RuntimeError(
                "Thread.build_via_thread_config mismatch "
                f"for existing thread_id={thread_id}"
            )
        return existing

    thread = Thread(
        id=thread_id,
        thread_config_id=thread_config_id,
        process_id=process_id,
        key=key,
        title=title,
        description=description,
        is_main=is_main,
    )

    return thread
    # --- AWARE: LOGIC END build_via_process


async def attach_lane(
    thread: Thread,
    domain_branch_id: UUID,
    projection_hash: str,
    title: str | None = None,
    is_active: bool = True,
) -> ThreadObjectInstanceGraphBranch:
    """
    Attach an existing domain lane (branch_id, projection_hash) to this Thread.

    Canonical v0 intent:
    - Enables cross-environment reuse of global lanes (e.g. Identity) without copying commits.
    - OS lane commit only: does not create or mutate domain commits; commits are always SSOT.
    - Idempotent: safe to call multiple times for the same lane.
    """

    # --- AWARE: LOGIC START attach_lane
    if not projection_hash.strip():
        raise RuntimeError("Thread.attach_lane requires non-empty projection_hash")

    thread_id = thread.id
    if thread_id is None:
        raise RuntimeError("Thread.attach_lane requires Thread.id")

    created = await ThreadObjectInstanceGraphBranch.create_for_lane(
        thread_id=thread_id,
        domain_branch_id=domain_branch_id,
        projection_hash=projection_hash,
        title=title,
        is_active=is_active,
    )
    # Idempotent: only append if the association edge is not already present.
    for assoc in thread.thread_object_instance_graph_branches:
        if assoc.id == created.id:
            return assoc
    thread.thread_object_instance_graph_branches.append(created)
    return created
    # --- AWARE: LOGIC END attach_lane


async def add_layout(
    thread: Thread, layout_id: UUID, key: str | None = None
) -> ThreadLayout:
    """
    Register a Layout for this Thread via canonical ThreadLayout association.

    Contract:
    - Uses parent->child propagation (`construct thread_layouts.create(...)`) so child identity derives
    from `_via_thread_layouts` + `layout_id`.
    - Idempotent for repeated parent/layout pairs.
    """

    # --- AWARE: LOGIC START add_layout
    thread_id = thread.id
    if thread_id is None:
        raise RuntimeError("Thread.add_layout requires Thread.id")

    if not isinstance(layout_id, UUID):
        raise TypeError("Thread.add_layout requires layout_id (UUID)")

    normalized_key = (key or "").strip() or None

    for assoc in thread.thread_layouts:
        if assoc.layout_id == layout_id:
            return assoc

    created = await ThreadLayout.create_via_thread(
        thread_id=thread_id,
        layout_id=layout_id,
        key=normalized_key,
    )

    # Idempotent: only append if the association edge is not already present.
    for assoc in thread.thread_layouts:
        if assoc.id == created.id:
            return assoc
    thread.thread_layouts.append(created)
    return created
    # --- AWARE: LOGIC END add_layout


async def update_picture(
    thread: Thread,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the thread territory image override.

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
        thread.image_id = None
        thread.image = None
        return

    if not has_any_meta:
        raise ValueError(
            "image_sha, image_mime_type, and image_size_bytes are required when setting a picture"
        )
    if image_sha is None or image_mime_type is None or image_size_bytes is None:
        raise ValueError(
            "image_sha, image_mime_type, and image_size_bytes must be set together"
        )

    blob = await StorageBlob.create(
        sha=image_sha,
        mime_type=image_mime_type,
        size_bytes=image_size_bytes,
    )
    if image_id is not None and image_id != blob.id:
        raise ValueError(
            "image_id does not match StorageBlob.id derived from image_sha "
            f"(image_id={image_id} blob_id={blob.id})"
        )

    thread.image = blob
    thread.image_id = blob.id
    # --- AWARE: LOGIC END update_picture
