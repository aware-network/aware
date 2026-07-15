from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Node Ontology
from aware_node_ontology.node.node_config_environment_profile_mount import NodeConfigEnvironmentProfileMount
from aware_node_ontology.node.node_config_environment_target import NodeConfigEnvironmentTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_node_ontology.stable_ids import stable_node_config_environment_target_id
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.environment.environment_config import EnvironmentConfig
from aware_environment_ontology.stable_ids import stable_environment_config_id

# --- AWARE: USER_IMPORTS END


async def add_profile_mount(
    node_config_environment_target: NodeConfigEnvironmentTarget,
    profile_key: str,
    package_name: str,
    mount_key: str,
    mode: str = "mounted",
    position: int | None = None,
) -> NodeConfigEnvironmentProfileMount:
    """
    Attach one EnvironmentProfilePackage install mount under this Environment target.

    Contract:
    - Mounts select EnvironmentProfilePackage install specs, not Experience profiles.
    - `package_name/profile_key` remain stable authored refs; Node does not store
      raw package ids.
    - Experience lenses activate later through Experience/session rails after
      Environment has applied its OS profile.
    """

    # --- AWARE: LOGIC START add_profile_mount
    target_id = node_config_environment_target.id
    if target_id is None:
        raise RuntimeError("NodeConfigEnvironmentTarget.add_profile_mount requires NodeConfigEnvironmentTarget.id")

    normalized_profile_key = (profile_key or "").strip()
    if not normalized_profile_key:
        raise RuntimeError("NodeConfigEnvironmentTarget.add_profile_mount requires non-empty profile_key")
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("NodeConfigEnvironmentTarget.add_profile_mount requires non-empty package_name")
    normalized_mount_key = (mount_key or "").strip()
    if not normalized_mount_key:
        raise RuntimeError("NodeConfigEnvironmentTarget.add_profile_mount requires non-empty mount_key")
    normalized_mode = (mode or "mounted").strip() or "mounted"

    for existing in node_config_environment_target.profile_mounts:
        existing_mount_key = (existing.mount_key or "").strip()
        if existing_mount_key == normalized_mount_key:
            if (existing.package_name or "").strip() != normalized_package_name:
                raise RuntimeError(
                    "NodeConfigEnvironmentTarget.add_profile_mount package_name mismatch "
                    f"for mount_key={normalized_mount_key!r}"
                )
            if (existing.profile_key or "").strip() != normalized_profile_key:
                raise RuntimeError(
                    "NodeConfigEnvironmentTarget.add_profile_mount profile_key mismatch "
                    f"for mount_key={normalized_mount_key!r}"
                )
            return existing

    created = await NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target(
        node_config_environment_target_id=target_id,
        profile_key=normalized_profile_key,
        package_name=normalized_package_name,
        mount_key=normalized_mount_key,
        mode=normalized_mode,
        position=position,
    )
    node_config_environment_target.profile_mounts.append(created)
    return created
    # --- AWARE: LOGIC END add_profile_mount


async def build_via_node_config(node_config_id: UUID, environment_handle: str) -> NodeConfigEnvironmentTarget:
    """
    Create one Node-owned environment target by canonical environment selection.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Identity is keyed by `(node_config_id, environment_handle)`.
    - `environment_handle` resolves the target `EnvironmentConfig` portal.
    - Environment profile package mounts are explicit optional pointers.
    """

    # --- AWARE: LOGIC START build_via_node_config
    normalized_environment_handle = (environment_handle or "").strip()
    if not normalized_environment_handle:
        raise RuntimeError("NodeConfigEnvironmentTarget.build_via_node_config requires non-empty environment_handle")

    target_id = stable_environment_config_id(handle=normalized_environment_handle)
    association_id = stable_node_config_environment_target_id(
        node_config_id=node_config_id,
        environment_handle=normalized_environment_handle,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_environment_config = session.imap_get(EnvironmentConfig, target_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(NodeConfigEnvironmentTarget, association_id)
        if existing is not None:
            if existing.node_config_id != node_config_id:
                raise RuntimeError(
                    "NodeConfigEnvironmentTarget.build_via_node_config payload mismatch for existing target: "
                    f"node_config_environment_target_id={association_id}"
                )
            if existing.environment_config_id != target_id:
                raise RuntimeError(
                    "NodeConfigEnvironmentTarget.build_via_node_config "
                    "environment_config_id mismatch for existing target: "
                    f"node_config_environment_target_id={association_id}"
                )
            if (existing.environment_handle or "").strip() != normalized_environment_handle:
                raise RuntimeError(
                    "NodeConfigEnvironmentTarget.build_via_node_config "
                    "environment_handle mismatch for existing target: "
                    f"node_config_environment_target_id={association_id}"
                )
            if existing.environment_config is None and resolved_environment_config is not None:
                existing.environment_config = resolved_environment_config
            return existing

    created = NodeConfigEnvironmentTarget.model_construct(
        id=association_id,
        node_config_id=node_config_id,
        environment_config=resolved_environment_config,
        environment_config_id=target_id,
        environment_handle=normalized_environment_handle,
        profile_mounts=[],
    )
    return created
    # --- AWARE: LOGIC END build_via_node_config
