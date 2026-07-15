from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Node Ontology
from aware_node_ontology.node.node_config_service_code_package import NodeConfigServiceCodePackage
from aware_node_ontology.node.node_config_service_target import NodeConfigServiceTarget

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_node_ontology.stable_ids import stable_node_config_service_target_id
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.stable_ids import stable_service_config_id

# --- AWARE: USER_IMPORTS END


async def activate_code_package(
    node_config_service_target: NodeConfigServiceTarget,
    slot_key: str,
    package_name: str,
    language: CodeLanguage = CodeLanguage.aware,
    service_config_code_package_config_id: UUID | None = None,
    code_package_id: UUID | None = None,
    description: str | None = None,
) -> NodeConfigServiceCodePackage:
    """
    Activate one concrete CodePackage under this service target.

    Contract:
    - Parent `NodeConfigServiceTarget` scope is injected by propagation.
    - The activation is deployment intent only; the service declaration owns hostable slots.
    - Local-dev sources may name `slot_key` and `package_name` before WorkspaceRevision has
      resolved package refs. When available, materializers can attach the Service slot and
      CodePackage relationships.
    """

    # --- AWARE: LOGIC START activate_code_package
    if node_config_service_target.id is None:
        raise RuntimeError("NodeConfigServiceTarget.activate_code_package requires NodeConfigServiceTarget.id")
    normalized_slot_key = (slot_key or "").strip().casefold()
    if not normalized_slot_key:
        raise RuntimeError("NodeConfigServiceTarget.activate_code_package requires non-empty slot_key")
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("NodeConfigServiceTarget.activate_code_package requires non-empty package_name")
    language_value = getattr(language, "value", language)
    normalized_language = (str(language_value or "").strip().casefold()) or CodeLanguage.aware.value
    resolved_language = CodeLanguage(normalized_language)

    for existing in node_config_service_target.code_packages:
        existing_language = getattr(existing.language, "value", existing.language)
        if (
            (existing.slot_key or "").strip().casefold() == normalized_slot_key
            and (existing.package_name or "").strip() == normalized_package_name
            and (str(existing_language or "").strip().casefold()) == resolved_language.value
        ):
            return existing

    created = await NodeConfigServiceCodePackage.build_via_node_config_service_target(
        node_config_service_target_id=node_config_service_target.id,
        slot_key=normalized_slot_key,
        package_name=normalized_package_name,
        language=resolved_language,
        service_config_code_package_config_id=service_config_code_package_config_id,
        code_package_id=code_package_id,
        description=description,
    )
    node_config_service_target.code_packages.append(created)
    return created
    # --- AWARE: LOGIC END activate_code_package


async def build_via_node_config(node_config_id: UUID, service_name: str) -> NodeConfigServiceTarget:
    """
    Create one Node-owned service target by canonical service name.

    Contract:
    - Parent `NodeConfig` scope is injected by propagation.
    - Identity is keyed by `(node_config_id, service_name)`.
    - The target `ServiceConfig` portal is resolved from `service_name` without storing a raw
      relationship-id attribute as semantic source.
    """

    # --- AWARE: LOGIC START build_via_node_config
    normalized_service_name = (service_name or "").strip()
    if not normalized_service_name:
        raise RuntimeError("NodeConfigServiceTarget.build_via_node_config requires non-empty service_name")

    target_id = stable_service_config_id(name=normalized_service_name)
    association_id = stable_node_config_service_target_id(
        node_config_id=node_config_id,
        service_name=normalized_service_name,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_service_config = session.imap_get(ServiceConfig, target_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(NodeConfigServiceTarget, association_id)
        if existing is not None:
            if existing.node_config_id != node_config_id:
                raise RuntimeError(
                    "NodeConfigServiceTarget.build_via_node_config payload mismatch for existing target: "
                    f"node_config_service_target_id={association_id}"
                )
            if existing.service_config_id != target_id:
                raise RuntimeError(
                    "NodeConfigServiceTarget.build_via_node_config service_config_id mismatch for existing target: "
                    f"node_config_service_target_id={association_id}"
                )
            if (existing.service_name or "").strip() != normalized_service_name:
                raise RuntimeError(
                    "NodeConfigServiceTarget.build_via_node_config service_name mismatch for existing target: "
                    f"node_config_service_target_id={association_id}"
                )
            if existing.service_config is None and resolved_service_config is not None:
                existing.service_config = resolved_service_config
            return existing

    return NodeConfigServiceTarget.model_construct(
        id=association_id,
        node_config_id=node_config_id,
        service_config=resolved_service_config,
        service_config_id=target_id,
        service_name=normalized_service_name,
    )
    # --- AWARE: LOGIC END build_via_node_config
