from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Node Ontology
from aware_node_ontology.node.node_config_environment_profile_mount import NodeConfigEnvironmentProfileMount

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_node_ontology.stable_ids import (
    stable_node_config_environment_profile_mount_id,
)
from aware_environment_ontology.environment.environment_profile_package import (
    EnvironmentProfilePackage,
)
from aware_environment_ontology.stable_ids import stable_environment_profile_package_id

# --- AWARE: USER_IMPORTS END


async def build_via_node_config_environment_target(
    node_config_environment_target_id: UUID,
    profile_key: str,
    package_name: str,
    mount_key: str,
    mode: str = "mounted",
    position: int | None = None,
) -> NodeConfigEnvironmentProfileMount:
    """
    Create one Node-owned EnvironmentProfilePackage install mount.

    Contract:
    - Parent `NodeConfigEnvironmentTarget` scope is injected by propagation.
    - Identity is keyed by parent environment target plus `mount_key`.
    - `package_name` resolves the target EnvironmentProfilePackage portal.
    - `profile_key` selects the child EnvironmentProfileConfig key exported by that package.
    - The mount is an explicit Environment-owned OS profile install pointer.
    - Experience profiles are not represented here; they activate after Environment profile install.
    """

    # --- AWARE: LOGIC START build_via_node_config_environment_target
    normalized_profile_key = (profile_key or "").strip()
    if not normalized_profile_key:
        raise RuntimeError(
            "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
            "requires non-empty profile_key"
        )
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError(
            "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
            "requires non-empty package_name"
        )
    normalized_mount_key = (mount_key or "").strip()
    if not normalized_mount_key:
        raise RuntimeError(
            "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target " "requires non-empty mount_key"
        )
    normalized_mode = (mode or "mounted").strip() or "mounted"

    environment_profile_package_id = stable_environment_profile_package_id(
        name=normalized_package_name,
    )
    mount_id = stable_node_config_environment_profile_mount_id(
        node_config_environment_target_id=node_config_environment_target_id,
        mount_key=normalized_mount_key,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_environment_profile_package = (
        session.imap_get(EnvironmentProfilePackage, environment_profile_package_id) if session is not None else None
    )

    if session is not None:
        existing = session.imap_get(NodeConfigEnvironmentProfileMount, mount_id)
        if existing is not None:
            if existing.node_config_environment_target_id != node_config_environment_target_id:
                raise RuntimeError(
                    "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
                    "parent mismatch for existing mount: "
                    f"node_config_environment_profile_mount_id={mount_id}"
                )
            if (existing.package_name or "").strip() != normalized_package_name:
                raise RuntimeError(
                    "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
                    "package_name mismatch for existing mount: "
                    f"node_config_environment_profile_mount_id={mount_id}"
                )
            if (existing.profile_key or "").strip() != normalized_profile_key:
                raise RuntimeError(
                    "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
                    "profile_key mismatch for existing mount: "
                    f"node_config_environment_profile_mount_id={mount_id}"
                )
            if existing.environment_profile_package_id != environment_profile_package_id:
                raise RuntimeError(
                    "NodeConfigEnvironmentProfileMount.build_via_node_config_environment_target "
                    "environment_profile_package_id mismatch for existing mount: "
                    f"node_config_environment_profile_mount_id={mount_id}"
                )
            if existing.environment_profile_package is None and resolved_environment_profile_package is not None:
                existing.environment_profile_package = resolved_environment_profile_package
            return existing

    return NodeConfigEnvironmentProfileMount.model_construct(
        id=mount_id,
        node_config_environment_target_id=node_config_environment_target_id,
        environment_profile_package=resolved_environment_profile_package,
        environment_profile_package_id=environment_profile_package_id,
        package_name=normalized_package_name,
        profile_key=normalized_profile_key,
        mount_key=normalized_mount_key,
        mode=normalized_mode,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_node_config_environment_target
