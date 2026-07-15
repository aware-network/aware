from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# Node Ontology
from aware_node_ontology.node.node_config_service_code_package import NodeConfigServiceCodePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.runtime.handler_context import current_handler_session
from aware_node_ontology.stable_ids import stable_node_config_service_code_package_id
from aware_service_ontology.service.service_config_code_package_config import (
    ServiceConfigCodePackageConfig,
)

# --- AWARE: USER_IMPORTS END


async def build_via_node_config_service_target(
    node_config_service_target_id: UUID,
    slot_key: str,
    package_name: str,
    language: CodeLanguage = CodeLanguage.aware,
    service_config_code_package_config_id: UUID | None = None,
    code_package_id: UUID | None = None,
    description: str | None = None,
) -> NodeConfigServiceCodePackage:
    """
    Create one Node-owned service CodePackage activation.

    Contract:
    - Parent `NodeConfigServiceTarget` scope is injected by propagation.
    - Identity is keyed by `(node_config_service_target_id, slot_key, package_name, language)`.
    - This object is deployment intent. ServiceConfigCodePackageConfig remains capability
      truth; CodePackage remains concrete package truth.
    """

    # --- AWARE: LOGIC START build_via_node_config_service_target
    normalized_slot_key = (slot_key or "").strip().casefold()
    if not normalized_slot_key:
        raise RuntimeError(
            "NodeConfigServiceCodePackage.build_via_node_config_service_target requires non-empty slot_key"
        )
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError(
            "NodeConfigServiceCodePackage.build_via_node_config_service_target requires non-empty package_name"
        )
    language_value = getattr(language, "value", language)
    normalized_language = (str(language_value or "").strip().casefold()) or CodeLanguage.aware.value
    resolved_language = CodeLanguage(normalized_language)
    normalized_description = (description or "").strip() or None

    activation_id = stable_node_config_service_code_package_id(
        node_config_service_target_id=node_config_service_target_id,
        slot_key=normalized_slot_key,
        package_name=normalized_package_name,
        language=resolved_language.value,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    service_slot = (
        session.imap_get(
            ServiceConfigCodePackageConfig,
            service_config_code_package_config_id,
        )
        if session is not None and service_config_code_package_config_id is not None
        else None
    )
    code_package = (
        session.imap_get(CodePackage, code_package_id) if session is not None and code_package_id is not None else None
    )

    if session is not None:
        existing = session.imap_get(NodeConfigServiceCodePackage, activation_id)
        if existing is not None:
            if existing.node_config_service_target_id != node_config_service_target_id:
                raise RuntimeError(
                    "NodeConfigServiceCodePackage payload mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            if (existing.slot_key or "").strip().casefold() != normalized_slot_key:
                raise RuntimeError(
                    "NodeConfigServiceCodePackage slot mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            if (existing.package_name or "").strip() != normalized_package_name:
                raise RuntimeError(
                    "NodeConfigServiceCodePackage package mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            existing_language = getattr(existing.language, "value", existing.language)
            if (str(existing_language or "").strip().casefold()) != resolved_language.value:
                raise RuntimeError(
                    "NodeConfigServiceCodePackage language mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            if (
                existing.service_config_code_package_config_id is not None
                and service_config_code_package_config_id is not None
                and existing.service_config_code_package_config_id != service_config_code_package_config_id
            ):
                raise RuntimeError(
                    "NodeConfigServiceCodePackage service slot mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            if (
                existing.code_package_id is not None
                and code_package_id is not None
                and existing.code_package_id != code_package_id
            ):
                raise RuntimeError(
                    "NodeConfigServiceCodePackage CodePackage mismatch for existing activation: "
                    f"node_config_service_code_package_id={activation_id}"
                )
            if existing.service_config_code_package_config is None and service_slot is not None:
                existing.service_config_code_package_config = service_slot
            if existing.code_package is None and code_package is not None:
                existing.code_package = code_package
            if (
                existing.service_config_code_package_config_id is None
                and service_config_code_package_config_id is not None
            ):
                existing.service_config_code_package_config_id = service_config_code_package_config_id
            if existing.code_package_id is None and code_package_id is not None:
                existing.code_package_id = code_package_id
            existing.description = normalized_description
            return existing

    return NodeConfigServiceCodePackage.model_construct(
        id=activation_id,
        node_config_service_target_id=node_config_service_target_id,
        slot_key=normalized_slot_key,
        package_name=normalized_package_name,
        language=resolved_language,
        service_config_code_package_config_id=service_config_code_package_config_id,
        service_config_code_package_config=service_slot,
        code_package_id=code_package_id,
        code_package=code_package,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_node_config_service_target
