from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Node Ontology
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_config_environment_target import NodeConfigEnvironmentTarget
from aware_node_ontology.node.node_config_interface_target import NodeConfigInterfaceTarget
from aware_node_ontology.node.node_config_ontology_target import NodeConfigOntologyTarget
from aware_node_ontology.node.node_config_service_target import NodeConfigServiceTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_node_ontology.stable_ids import stable_node_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> NodeConfig:
    """
    Create the canonical Node-owned desired hosted-composition root.

    Contract:
    - Identity is keyed by semantic Node package/config `name`.
    - `NodeConfig` remains desired-state truth only; it does not point at live `NetworkNode`
      runtime state.
    - Hosted composition is attached through contained target objects keyed by stable semantic
      names rather than raw relationship-id primitives.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("NodeConfig.build requires non-empty name")
    normalized_description = (description or "").strip() or None

    config_id = stable_node_config_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    if session is not None:
        existing = session.imap_get(NodeConfig, config_id)
        if existing is not None:
            if existing.name != normalized_name:
                raise RuntimeError(
                    "NodeConfig.build name mismatch for existing config: "
                    f"node_config_id={config_id} "
                    f"existing={existing.name!r} provided={normalized_name!r}"
                )
            existing_description = (existing.description or "").strip() or None
            if existing_description != normalized_description:
                raise RuntimeError(
                    "NodeConfig.build description mismatch for existing config: "
                    f"node_config_id={config_id} "
                    f"existing={existing_description!r} provided={normalized_description!r}"
                )
            return existing

    return NodeConfig.model_construct(
        id=config_id,
        name=normalized_name,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build


async def attach_environment_target(node_config: NodeConfig, environment_handle: str) -> NodeConfigEnvironmentTarget:
    """
    Attach one canonical Environment target by stable environment handle.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Target identity is resolved from `environment_handle`.
    - Environment profile package mounts are installed separately by explicit
      Node environment profile declarations.
    """

    # --- AWARE: LOGIC START attach_environment_target
    if node_config.id is None:
        raise RuntimeError("NodeConfig.attach_environment_target requires NodeConfig.id")

    normalized_handle = (environment_handle or "").strip()
    if not normalized_handle:
        raise RuntimeError("NodeConfig.attach_environment_target requires non-empty environment_handle")

    for existing in node_config.environment_targets:
        if (existing.environment_handle or "").strip() == normalized_handle:
            return existing

    target = await NodeConfigEnvironmentTarget.build_via_node_config(
        node_config_id=node_config.id,
        environment_handle=normalized_handle,
    )
    node_config.environment_targets.append(target)
    return target
    # --- AWARE: LOGIC END attach_environment_target


async def attach_environment_profile_mount(
    node_config: NodeConfig,
    environment_handle: str,
    profile_key: str,
    package_name: str,
    mount_key: str,
    mode: str = "mounted",
    position: int | None = None,
) -> NodeConfigEnvironmentTarget:
    """
    Attach an Environment target and one explicit EnvironmentProfilePackage install mount.

    Contract:
    - Allows explicit EnvironmentProfilePackage install pointers in Node config.
    - Existing target is reused by `environment_handle`.
    - Mounts select OS profile install specs only; Experience lenses activate later.
    """

    # --- AWARE: LOGIC START attach_environment_profile_mount
    if node_config.id is None:
        raise RuntimeError("NodeConfig.attach_environment_profile_mount requires NodeConfig.id")

    normalized_handle = (environment_handle or "").strip()
    if not normalized_handle:
        raise RuntimeError("NodeConfig.attach_environment_profile_mount requires non-empty environment_handle")
    normalized_profile_key = (profile_key or "").strip()
    if not normalized_profile_key:
        raise RuntimeError("NodeConfig.attach_environment_profile_mount requires non-empty profile_key")
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("NodeConfig.attach_environment_profile_mount requires non-empty package_name")
    normalized_mount_key = (mount_key or "").strip()
    if not normalized_mount_key:
        raise RuntimeError("NodeConfig.attach_environment_profile_mount requires non-empty mount_key")
    normalized_mode = (mode or "mounted").strip() or "mounted"

    target = None
    for existing in node_config.environment_targets:
        if (existing.environment_handle or "").strip() == normalized_handle:
            target = existing
            break

    if target is None:
        target = await NodeConfigEnvironmentTarget.build_via_node_config(
            node_config_id=node_config.id,
            environment_handle=normalized_handle,
        )
        node_config.environment_targets.append(target)
    await target.add_profile_mount(
        profile_key=normalized_profile_key,
        package_name=normalized_package_name,
        mount_key=normalized_mount_key,
        mode=normalized_mode,
        position=position,
    )
    return target
    # --- AWARE: LOGIC END attach_environment_profile_mount


async def attach_service_config(node_config: NodeConfig, service_name: str) -> NodeConfigServiceTarget:
    """
    Attach one canonical `ServiceConfig` target by stable service name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Target identity is resolved from `service_name`.
    - Node keeps desired hosted composition local while Service keeps runtime semantics.
    """

    # --- AWARE: LOGIC START attach_service_config
    if node_config.id is None:
        raise RuntimeError("NodeConfig.attach_service_config requires NodeConfig.id")

    normalized_service_name = (service_name or "").strip()
    if not normalized_service_name:
        raise RuntimeError("NodeConfig.attach_service_config requires non-empty service_name")

    for existing in node_config.service_targets:
        if (existing.service_name or "").strip() == normalized_service_name:
            return existing

    created = await NodeConfigServiceTarget.build_via_node_config(
        node_config_id=node_config.id,
        service_name=normalized_service_name,
    )
    node_config.service_targets.append(created)
    return created
    # --- AWARE: LOGIC END attach_service_config


async def attach_ontology_package(node_config: NodeConfig, package_name: str) -> NodeConfigOntologyTarget:
    """
    Attach one canonical `OntologyPackage` target by stable package name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Target identity is resolved from `package_name`.
    - Node keeps desired hosted composition local while Ontology keeps
      semantic package/runtime meaning.
    """

    # --- AWARE: LOGIC START attach_ontology_package
    if node_config.id is None:
        raise RuntimeError("NodeConfig.attach_ontology_package requires NodeConfig.id")

    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("NodeConfig.attach_ontology_package requires non-empty package_name")

    for existing in node_config.ontology_targets:
        if (existing.package_name or "").strip() == normalized_package_name:
            return existing

    created = await NodeConfigOntologyTarget.build_via_node_config(
        node_config_id=node_config.id,
        package_name=normalized_package_name,
    )
    node_config.ontology_targets.append(created)
    return created
    # --- AWARE: LOGIC END attach_ontology_package


async def attach_interface_config(node_config: NodeConfig, interface_name: str) -> NodeConfigInterfaceTarget:
    """
    Attach one canonical `InterfaceConfig` target by stable interface name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Target identity is resolved from `interface_name`.
    - Node keeps desired hosted composition local while Interface keeps runtime semantics.
    """

    # --- AWARE: LOGIC START attach_interface_config
    if node_config.id is None:
        raise RuntimeError("NodeConfig.attach_interface_config requires NodeConfig.id")

    normalized_interface_name = (interface_name or "").strip()
    if not normalized_interface_name:
        raise RuntimeError("NodeConfig.attach_interface_config requires non-empty interface_name")

    for existing in node_config.interface_targets:
        if (existing.interface_name or "").strip() == normalized_interface_name:
            return existing

    created = await NodeConfigInterfaceTarget.build_via_node_config(
        node_config_id=node_config.id,
        interface_name=normalized_interface_name,
    )
    node_config.interface_targets.append(created)
    return created
    # --- AWARE: LOGIC END attach_interface_config
