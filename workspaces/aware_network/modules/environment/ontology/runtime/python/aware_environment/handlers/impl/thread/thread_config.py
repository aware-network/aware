from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_config import ThreadConfig
from aware_environment_ontology.thread.thread_config_layout_config import ThreadConfigLayoutConfig
from aware_environment_ontology.thread.thread_config_object_projection_graph import ThreadConfigObjectProjectionGraph

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_thread_config_id,
)

# Storage Ontology
from aware_storage_ontology.blob.storage_blob import StorageBlob

# --- AWARE: USER_IMPORTS END


async def add_object_projection_graph(
    thread_config: ThreadConfig,
    object_projection_graph_id: UUID,
    view_key: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigObjectProjectionGraph:
    """
    Declare one projection graph this ThreadConfig can host.

    Contract:
    - Environment declares projection authority, not Experience ownership.
    - Experience may later bind actions/views over this hosted projection.
    """

    # --- AWARE: LOGIC START add_object_projection_graph
    if thread_config.id is None:
        raise RuntimeError("ThreadConfig.add_object_projection_graph requires ThreadConfig.id")

    created = await ThreadConfigObjectProjectionGraph.create_via_thread_config(
        thread_config_id=thread_config.id,
        object_projection_graph_id=object_projection_graph_id,
        view_key=view_key,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    for existing in thread_config.object_projection_graphs:
        if existing.id == created.id:
            return existing
    thread_config.object_projection_graphs.append(created)
    return created
    # --- AWARE: LOGIC END add_object_projection_graph


async def add_layout_config(
    thread_config: ThreadConfig,
    layout_config_id: UUID,
    key: str | None = None,
    position: int | None = None,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigLayoutConfig:
    """
    Create a deterministic ThreadConfigLayoutConfig association edge.

    Contract:
    - ThreadConfig declares which Attention LayoutConfig objects this thread offers.
    - Runtime Environment provisioning lowers this config edge into ThreadLayout.
    - Attention owns LayoutConfig/SectionConfig topology and focus state.
    """

    # --- AWARE: LOGIC START add_layout_config
    if thread_config.id is None:
        raise RuntimeError("ThreadConfig.add_layout_config requires ThreadConfig.id")

    created = await ThreadConfigLayoutConfig.create_via_thread_config(
        thread_config_id=thread_config.id,
        layout_config_id=layout_config_id,
        key=key,
        position=position,
        narrative=narrative,
        intent=intent,
    )
    for existing in thread_config.layout_configs:
        if existing.id == created.id:
            return existing
    thread_config.layout_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_layout_config


async def update_picture(
    thread_config: ThreadConfig,
    image_id: UUID | None = None,
    image_sha: str | None = None,
    image_mime_type: str | None = None,
    image_size_bytes: int | None = None,
) -> None:
    """
    Updates (or clears) the thread config image.

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
        thread_config.image_id = None
        thread_config.image = None
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

    thread_config.image = blob
    thread_config.image_id = blob.id
    # --- AWARE: LOGIC END update_picture


async def build_via_process_config(
    process_config_id: UUID,
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
    Construct a deterministic ThreadConfig under one ProcessConfig.

    Contract:
    - Identity is derived from ProcessConfig-scoped config keys.
    - Runtime Thread instances are created under Process.
    - Program/action semantics remain Experience-owned.
    """

    # --- AWARE: LOGIC START build_via_process_config
    thread_config_id = stable_thread_config_id(process_config_id=process_config_id, key=key)
    handler_session = current_handler_session()
    existing = handler_session.imap_get(ThreadConfig, thread_config_id)
    if existing is not None:
        if existing.process_config_id != process_config_id or existing.key != key:
            raise RuntimeError(
                "ThreadConfig.build_via_process_config mismatch " f"for existing thread_config_id={thread_config_id}"
            )
        return existing

    return ThreadConfig(
        id=thread_config_id,
        process_config_id=process_config_id,
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
    # --- AWARE: LOGIC END build_via_process_config
